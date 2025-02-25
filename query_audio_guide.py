import os
import textwrap
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

def initialize_rag_system():
    """Initialize the RAG system with the audio equipment vector database."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    # Initialize dense embeddings
    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    
    # Create Qdrant client
    client = QdrantClient(path="./audio_db")
    
    # Define the collection name
    collection_name = "audio_equipment_embeddings"
    
    # Initialize Qdrant vector store
    qdrant = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
        vector_name="dense_vector"
    )
    
    print("Audio equipment vector database loaded successfully!")
    return qdrant

def get_audio_recommendations(query, user_preferences=None):
    """Get audio equipment recommendations based on user query and preferences."""
    # Initialize the RAG system
    qdrant = initialize_rag_system()
    if not qdrant:
        return "Failed to initialize RAG system"
    
    # Set default user preferences if none provided
    if user_preferences is None:
        user_preferences = {
            "budget": "$200",
            "use_case": "general listening",
            "preferred_type": "IEMs",
            "sound_signature": "balanced"
        }

    # Manually format the prompt before passing it to the model
    formatted_prompt = f"""
    Use the following information to provide audio equipment recommendations based on the user's query and preferences.

    Context: Audio equipment details and reviews.

    User Preferences:
      - Budget: {user_preferences['budget']}
      - Use Case: {user_preferences['use_case']}
      - Preferred Type: {user_preferences['preferred_type']}
      - Sound Signature Preference: {user_preferences['sound_signature']}
      - Query: {query}

    Provide detailed recommendations for audio equipment that match the user's preferences. 
    Include specific model recommendations, their key features, pros and cons, and price points.
    Format your response in a clear, structured way with sections and bullet points where appropriate.
    """

    # Initialize the LLM
    llm = ChatGroq(
        temperature=0.2,
        model_name="qwen-2.5-32b"
    )

    # Create the RetrievalQA chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=qdrant.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=False,
        chain_type_kwargs={"verbose": True},
    )

    # Execute the query by passing only the formatted prompt
    response = qa.invoke({
        "query": formatted_prompt,  # Now the entire formatted prompt is passed as the query
        "context": "Audio equipment details and reviews."
    })

    return response

def print_response(response):
    """Format and print the response nicely."""
    print("\n" + "=" * 80 + "\n")
    
    if isinstance(response, str):
        print(response)
        return
    
    response_txt = response.get("result", "")
    for chunk in response_txt.split("\n"):
        if not chunk:
            print()
            continue
        print("\n".join(textwrap.wrap(chunk, 100, break_long_words=False)))
    
    print("\n" + "=" * 80)
    print("\nSources:")
    for i, doc in enumerate(response.get("source_documents", [])):
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
    
    # Get recommendations and print the response
    print("Getting audio equipment recommendations...")
    response = get_audio_recommendations(example_queries[0], example_preferences)
    print_response(response)
