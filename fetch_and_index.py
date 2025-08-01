import os
import wikipediaapi
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient, models
from langchain_ollama import OllamaLLM
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid
import time
from SPARQLWrapper import SPARQLWrapper, JSON

# --- CONFIGURATION ---
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "unesco_world_heritage"
RECREATE_COLLECTION = True 
SITE_LIMIT = 50 # Set a limit for testing, or None to process all
WIKIDATA_USER_AGENT = "UNESCO-RAG-App/1.0 (iyenshiaut@gmail.com)"

# --- INITIALIZE CLIENTS ---
qdrant_client = QdrantClient(url=QDRANT_URL)
embedding_model = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-mpnet-base-v2")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
wiki_api = wikipediaapi.Wikipedia(language='en', user_agent=WIKIDATA_USER_AGENT)

def get_sites_from_wikidata():
    """
    Fetches the list of UNESCO World Heritage Sites directly from Wikidata
    using a SPARQL query. This is the most reliable method.
    """
    print("Querying Wikidata for the list of heritage sites...")
    endpoint_url = "https://query.wikidata.org/sparql"
    
    # This SPARQL query asks Wikidata for all items that are an "instance of"
    # a "UNESCO World Heritage site" and retrieves their name and country.
    query = """
    SELECT ?itemLabel ?countryLabel WHERE {
      ?item wdt:P31 wd:Q9259.
      ?item wdt:P17 ?country.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """
    
    sparql = SPARQLWrapper(endpoint_url, agent=WIKIDATA_USER_AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
    except Exception as e:
        print(f"ERROR: Failed to query Wikidata. {e}")
        return []

    sites = []
    for result in results["results"]["bindings"]:
        site_name = result.get("itemLabel", {}).get("value")
        country_name = result.get("countryLabel", {}).get("value")
        
        if site_name and country_name:
            # For stability, we will omit the category, which is harder to get reliably.
            sites.append({'name': site_name, 'country': country_name, 'category': 'Unknown'})
            
    print(f"Found {len(sites)} sites from Wikidata. Processing limit is {SITE_LIMIT or 'all'}.")
    return sites[:SITE_LIMIT] if SITE_LIMIT else sites

def process_and_index_sites(sites):
    """Fetches Wikipedia content for each site, chunks it, and indexes it in Qdrant."""
    if not sites:
        print("No sites to process. Exiting.")
        return

    print("\nProcessing and indexing sites...")
    
    # --- Corrected Data Preparation Logic ---
    # We will first collect all texts and their corresponding payloads.
    texts_to_embed = []
    payloads = []

    for i, site in enumerate(sites):
        try:
            print(f"[{i+1}/{len(sites)}] Processing: {site['name']}")
            page = wiki_api.page(site['name'])

            if page.exists():
                chunks = text_splitter.split_text(page.text)
                for chunk_text in chunks:
                    texts_to_embed.append(chunk_text)
                    payloads.append({
                        "site_name": site['name'],
                        "country": site['country'],
                        "category": site['category'],
                        "source": page.fullurl,
                        "text": chunk_text # Also store the original text in the payload
                    })
            else:
                print(f"  - Wikipedia page not found for '{site['name']}'. Skipping.")
        except Exception as e:
            print(f"  - Error processing {site['name']}: {e}")
        time.sleep(0.5)

    if texts_to_embed:
        print(f"\nCreating embeddings for {len(texts_to_embed)} chunks...")
        vectors = embedding_model.embed_documents(texts_to_embed)

        print(f"Assembling {len(vectors)} points for Qdrant...")
        # Now, create the PointStructs with the vectors included
        points_to_upsert = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            ) for vector, payload in zip(vectors, payloads)
        ]

        print(f"Upserting points to Qdrant...")
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points_to_upsert,
            wait=True
        )

def main():
    """Main function to set up DB and run the indexing pipeline."""
    collection_exists = qdrant_client.collection_exists(collection_name=COLLECTION_NAME)
    
    if RECREATE_COLLECTION and collection_exists:
        print(f"Recreating collection '{COLLECTION_NAME}'...")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        collection_exists = False

    if not collection_exists:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")

    sites_to_process = get_sites_from_wikidata()
    process_and_index_sites(sites_to_process)
    print("\n✅ Indexing complete!")

if __name__ == "__main__":
    main()