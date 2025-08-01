from flask import Flask, render_template, request, jsonify
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient, models

# --- CONFIGURATION ---
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "unesco_world_heritage"

# --- INITIALIZE CLIENTS ---
app = Flask(__name__)
qdrant_client = QdrantClient(url=QDRANT_URL)
llm = OllamaLLM(model="deepseek-r1:1.5b")
embedding_model = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-mpnet-base-v2")

# --- RAG PROMPT
# TEMPLATE ---
RAG_PROMPT_TEMPLATE = """
You are an expert assistant on UNESCO World Heritage Sites.
Use the following retrieved context to answer the user's question.
If you don't know the answer from the context, just say that you don't have enough information.
Your answer should be concise and directly based on the provided documents.

CONTEXT:
{context}

QUESTION:
{question}
"""
rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

def retrieve_context(query, filters):
    """Retrieves context from Qdrant based on query and filters."""
    query_vector = embedding_model.embed_query(query)
    
    filter_conditions = []
    if filters.get("country") and filters["country"] != "":
        filter_conditions.append(models.FieldCondition(key="country", match=models.MatchValue(value=filters["country"])))

    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=models.Filter(must=filter_conditions) if filter_conditions else None,
        limit=5 
    )
    
    context = "\n\n---\n\n".join([hit.payload["text"] for hit in search_result])
    return context

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("question")
    filters = data.get("filters", {})

    print(f"Received query: '{query}' with filters: {filters}") # Debug print

    if not query:
        return jsonify({"error": "No question provided"}), 400

    try:
        context = retrieve_context(query, filters)
        print(f"Retrieved context: {context[:200]}...") # Debug print
        
        rag_chain = rag_prompt | llm | StrOutputParser()
        response = rag_chain.invoke({"context": context, "question": query})
        
        print(f"LLM generated response: {response}") # Debug print
        return jsonify({"answer": response})
        
    except Exception as e:
        print(f"An error occurred in /ask route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get_filters", methods=["GET"])
def get_filters():
    try:
        all_points = qdrant_client.scroll(collection_name=COLLECTION_NAME, limit=10000, with_payload=True)[0]
        countries = sorted(list(set(p.payload['country'] for p in all_points if 'country' in p.payload)))
        return jsonify({"countries": countries})
    except Exception as e:
        print(f"An error occurred in /get_filters route: {e}")
        return jsonify({"countries": [], "categories": []})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)