import os
import textwrap
from pathlib import Path
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

def initialize_rag_system():
    """Initialize the RAG system with the audio equipment vectordb"""
    # Load Groq API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    # Initialize embeddings
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    
    # Load the existing vector database
    try:
        qdrant = Qdrant(
            path="./audio_db",
            collection_name="audio_equipment_embeddings",
            embeddings=embeddings,
        )
        print("Audio equipment vector database loaded successfully!")
    except Exception as e:
        print(f"Error loading vector database: {e}")
        print("Make sure to run create_audio_vectordb.py first!")
        return None
    
    return qdrant

def get_audio_recommendations(query, user_preferences=None):
    """Get audio equipment recommendations based on user query and preferences"""
    # Initialize the RAG system
    qdrant = initialize_rag_system()
    if not qdrant:
        return "Failed to initialize RAG system"
    
    # Default user preferences if none provided
    if user_preferences is None:
        user_preferences = {
            "budget": "$200",
            "use_case": "general listening",
            "preferred_type": "IEMs",
            "sound_signature": "balanced"
        }
    
    # Create prompt template for audio recommendations
    recommendation_prompt = """
    Use the following information to provide audio equipment recommendations based on the user's query and preferences.
    
    Context: {context}
    
    User Preferences:
    - Budget: {budget}
    - Use Case: {use_case}
    - Preferred Type: {preferred_type}
    - Sound Signature Preference: {sound_signature}
    
    Query: {question}
    
    Provide detailed recommendations for audio equipment that match the user's preferences. 
    Include specific model recommendations, their key features, pros and cons, and price points.
    Format your response in a clear, structured way with sections and bullet points where appropriate.
    """
    
    prompt = PromptTemplate(
        template=recommendation_prompt,
        input_variables=["context", "question", "budget", "use_case", "preferred_type", "sound_signature"]
    )
    
    # Initialize LLM
    llm = ChatGroq(
        temperature=0.2,
        model_name="qwen-2.5-32b"
    )
    
    # Create RetrievalQA chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=qdrant.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt, "verbose": False},
    )
    
    # Execute the query
    response = qa.invoke({
        "question": query,
        "budget": user_preferences.get("budget"),
        "use_case": user_preferences.get("use_case"),
        "preferred_type": user_preferences.get("preferred_type"),
        "sound_signature": user_preferences.get("sound_signature"),
    })
    
    return response

def print_response(response):
    """Format and print the response nicely"""
    print("\n" + "="*80 + "\n")
    
    response_txt = response["result"]
    for chunk in response_txt.split("\n"):
        if not chunk:
            print()
            continue
        print("\n".join(textwrap.wrap(chunk, 100, break_long_words=False)))
    
    print("\n" + "="*80)
    print("\nSources:")
    for i, doc in enumerate(response["source_documents"]):
        print(f"Source {i+1}: {doc.metadata.get('source', 'Unknown')} (page {doc.metadata.get('page', 'unknown')})")

# Example usage
if __name__ == "__main__":
    # Example queries
    example_queries = [
        "What are the best IEMs under $100?",
        "Recommend some headphones for gaming",
        "What accessories should I get for my new IEMs?"
    ]
    
    # Example user preferences
    example_preferences = {
        "budget": "$150",
        "use_case": "commuting",
        "preferred_type": "IEMs",
        "sound_signature": "warm"
    }
    
    # Get recommendations
    print("Getting audio equipment recommendations...")
    response = get_audio_recommendations(example_queries[0], example_preferences)
    print_response(response)
