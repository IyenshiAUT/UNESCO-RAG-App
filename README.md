# Unesco RAG App

Unesco RAG App is a web application that demonstrates Retrieval-Augmented Generation (RAG) techniques for UNESCO-related data. It allows users to fetch, index, and interactively query UNESCO datasets through a simple web interface. The app is built with Python and Flask, and is designed for educational and prototyping purposes.

## Features
- Fetches and preprocesses UNESCO data from external sources
- Indexes data for fast and relevant retrieval using RAG principles
- User-friendly web interface for querying and exploring indexed data
- Customizable UI with modular CSS and JavaScript
- Easily extensible for other datasets or advanced RAG workflows

## Project Structure
```
app.py                # Main Flask application
fetch_and_index.py    # Script to fetch and index UNESCO data
requirements.txt      # Python dependencies
static/
    css/style.css     # Custom styles
    js/script.js      # Custom JavaScript
templates/
    index.html        # Main HTML template
data/                 # (Optional) Directory for storing indexed data
```

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- (Optional) Git for cloning the repository

## Setup Instructions

### 1. Clone the repository
```powershell
git clone 
cd "Unesco RAG App"
```

### 2. Create and activate a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Fetch and index UNESCO data
```powershell
python fetch_and_index.py
```

### 5. Run the web application
```powershell
python app.py
```


The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Usage

1. Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000).
2. Enter your query in the search box and submit.
3. View the retrieved results and explore the UNESCO data interactively.

### Example Query
```
Show me World Heritage Sites in Italy
```
The app will return relevant UNESCO sites based on the indexed data.

## Customization
- Modify `static/css/style.css` for styles
- Modify `static/js/script.js` for client-side logic
- Update `templates/index.html` for the main page layout
- Extend `fetch_and_index.py` to fetch or preprocess additional datasets
- Enhance `app.py` to add new endpoints or improve retrieval logic

## Contributing
Contributions are welcome! To contribute:
- Fork the repository
- Create a new branch for your feature or bugfix
- Submit a pull request with a clear description of your changes

## License
This project is for educational and demonstration purposes. Add your license information here if needed.
