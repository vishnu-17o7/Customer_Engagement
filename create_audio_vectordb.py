import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Qdrant
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
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2048,
        chunk_overlap=200
    )
    docs = text_splitter.split_documents(loaded_documents)
    
    print(f"Split into {len(docs)} chunks")
    
    # Create embeddings using FastEmbed
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    
    # Create Qdrant vector store
    qdrant = Qdrant.from_documents(
        docs,
        embeddings,
        path="./audio_db",
        collection_name="audio_equipment_embeddings",
    )
    
    print("Vector database created successfully!")
    return qdrant

if __name__ == "__main__":
    create_audio_vectordb()
