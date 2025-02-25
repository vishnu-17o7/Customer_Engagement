import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Load environment variables
load_dotenv()

def create_audio_vectordb():
    print("Creating vector database from Audio Equipment Guide...")

    # Path to the audio equipment guide markdown file
    guide_path = Path("Resources/Audio_Equipment_Guide.md")

    # Check if the file exists
    if not guide_path.exists():
        raise FileNotFoundError(f"Audio equipment guide not found at {guide_path}")

    # Load the markdown document
    loader = UnstructuredMarkdownLoader(guide_path)
    loaded_documents = loader.load()

    print(f"Loaded document with {len(loaded_documents)} pages")

    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2048, chunk_overlap=200)
    docs = text_splitter.split_documents(loaded_documents)

    print(f"Split into {len(docs)} chunks")

    # Initialize dense embeddings using FastEmbedEmbeddings
    dense_embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")

    # Determine the dimension of the dense embeddings
    sample_embedding = dense_embeddings.embed_query("Sample text")
    dense_dimension = len(sample_embedding)

    # Create Qdrant client for local storage
    client = QdrantClient(path="./audio_db")

    # Define the collection name
    collection_name = "audio_equipment_embeddings"

    # Check if the collection exists and delete it if so (to recreate with correct config)
    collections = client.get_collections()
    if any(col.name == collection_name for col in collections.collections):
        client.delete_collection(collection_name=collection_name)
        print(f"Deleted existing collection: {collection_name}")

    # Create a new collection with a dense vector configuration using a named vector
    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense_vector": VectorParams(size=dense_dimension, distance=Distance.COSINE)
        }
    )
    print(f"Created new collection: {collection_name}")

    # Upsert documents with their dense embeddings ensuring valid UUIDs and named vector
    for doc in docs:
        embedding = dense_embeddings.embed_query(doc.page_content)
        
        # Use provided id if valid, otherwise generate a new one
        candidate_id = doc.metadata.get("id")
        try:
            if candidate_id:
                valid_uuid = uuid.UUID(str(candidate_id))
                final_id = str(valid_uuid)
            else:
                final_id = str(uuid.uuid4())
        except Exception:
            final_id = str(uuid.uuid4())
        
        point = PointStruct(
            id=final_id,
            # Provide the vector as a dictionary keyed by the vector name
            vector={"dense_vector": embedding},
            payload={"text": doc.page_content, "metadata": doc.metadata},
        )
        client.upsert(
            collection_name=collection_name,
            points=[point],
        )

    print("Vector database created successfully!")

if __name__ == "__main__":
    create_audio_vectordb()
