document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const countryFilter = document.getElementById('country-filter');
    const categoryFilter = document.getElementById('category-filter');

    async function populateFilters() {
        try {
            const response = await fetch('/get_filters');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();

            if (data.countries) {
                data.countries.forEach(country => {
                    const option = new Option(country, country);
                    countryFilter.add(option);
                });
            }

            if (data.categories) {
                data.categories.forEach(category => {
                    const option = new Option(category, category);
                    categoryFilter.add(option);
                });
            }
        } catch (error) {
            console.error('Error fetching filters:', error);
            appendMessage('Could not load filters from the server.', 'assistant');
        }
    }
    
    populateFilters();

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = userInput.value.trim();
        if (userMessage === '') return;

        appendMessage(userMessage, 'user');
        userInput.value = '';

        // --- FIX #1: Pass class names as separate arguments ---
        const thinkingIndicator = appendMessage('...', 'assistant', 'thinking');

        const filters = {
            country: countryFilter.value,
            category: categoryFilter.value
        };

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMessage, filters: filters }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Server responded with status: ${response.status}`);
            }
            
            const data = await response.json();
            thinkingIndicator.classList.remove('thinking'); // This now correctly removes just the 'thinking' class
            thinkingIndicator.querySelector('p').textContent = data.answer;

        } catch (error) {
            console.error('Error during /ask fetch:', error);
            thinkingIndicator.classList.remove('thinking');
            thinkingIndicator.querySelector('p').textContent = `Sorry, an error occurred: ${error.message}`;
        }
    });

    // --- FIX #2: Update function to accept multiple class names ---
    function appendMessage(text, ...types) { // Use rest parameter to accept multiple arguments
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', ...types); // Use spread syntax to add all classes
        
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        
        messageDiv.appendChild(paragraph);
        chatBox.appendChild(messageDiv);
        
        chatBox.scrollTop = chatBox.scrollHeight;
        return messageDiv;
    }
});