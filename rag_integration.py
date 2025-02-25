#### filepath: /c:/Users/vishn/Desktop/Programs/Customer_Engagement/rag_integration.py
import os
import json
import time
import re
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pathlib import Path

# Import RAG system components
from langchain.prompts import PromptTemplate
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from transformers import pipeline

# Load environment variables
load_dotenv()

# Load Slack API credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Path for shared pending responses file
PENDING_RESPONSES_FILE = "pending_responses.json"

# Import for backward compatibility
from slack_approval import pending_responses

# Initialize intent classifier
try:
    intent_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    print(f"⚠️ Error initializing intent classifier: {e}")
    intent_classifier = None

# Function to load pending responses from file
def load_pending_responses():
    """Load pending responses from JSON file"""
    try:
        if os.path.exists(PENDING_RESPONSES_FILE):
            with open(PENDING_RESPONSES_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"⚠️ Error loading pending responses: {e}")
        return {}

# Function to save pending responses to file
def save_pending_responses(responses):
    """Save pending responses to JSON file"""
    try:
        # Convert tuple values to lists for JSON serialization
        serializable_responses = {}
        for key, value in responses.items():
            serializable_responses[key] = list(value)
            
        with open(PENDING_RESPONSES_FILE, 'w') as f:
            json.dump(serializable_responses, f)
    except Exception as e:
        print(f"⚠️ Error saving pending responses: {e}")

def initialize_rag_system():
    """Initialize the RAG system with the audio equipment vectordb"""
    print("\n🔍 DEBUG: Starting to initialize RAG system")
    try:
        # Check if audio_db directory exists
        db_path = Path("./audio_db")
        if not db_path.exists():
            print(f"❌ DEBUG: Vector database directory not found at {db_path.absolute()}")
            print("❓ DEBUG: Did you run create_audio_vectordb.py first?")
            return None

        # Initialize embeddings
        print("🔄 DEBUG: Initializing embeddings with BAAI/bge-base-en-v1.5")
        try:
            embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
            print("✅ DEBUG: Embeddings initialized successfully")
        except Exception as embed_err:
            print(f"❌ DEBUG: Failed to initialize embeddings: {embed_err}")
            return None
        
        # Create Qdrant client
        print("🔄 DEBUG: Creating Qdrant client")
        try:
            client = QdrantClient(path="./audio_db")
            print("✅ DEBUG: Qdrant client created successfully")
        except Exception as client_err:
            print(f"❌ DEBUG: Failed to create Qdrant client: {client_err}")
            return None
        
        # Load the existing vector database
        print("🔄 DEBUG: Attempting to load Qdrant vector database")
        try:
            collection_name = "audio_equipment_embeddings"
            qdrant = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
                vector_name="dense_vector"
            )
            print("✅ DEBUG: Audio equipment vector database loaded successfully!")
            return qdrant
        except Exception as qdrant_err:
            print(f"❌ DEBUG: Failed to load Qdrant database: {qdrant_err}")
            return None
    except Exception as e:
        print(f"⚠️ DEBUG: Unexpected error initializing RAG system: {e}")
        print("Make sure to run create_audio_vectordb.py first!")
        return None

def detect_query_intent(query):
    """Detect if query is asking for a recommendation or general information"""
    print(f"\n🔍 DEBUG: Detecting intent for query: '{query}'")
    if intent_classifier is None:
        print("ℹ️ DEBUG: Intent classifier not available, using regex fallback")
        # Fallback to regex-based detection
        recommendation_patterns = [
            r"recommend",
            r"suggest",
            r"what.*(good|best|top)",
            r"which.*(should|would|could)",
            r"looking for",
            r"buy",
            r"purchase",
            r"advice"
        ]
        
        for pattern in recommendation_patterns:
            if re.search(pattern, query.lower()):
                print(f"✅ DEBUG: Matched recommendation pattern: '{pattern}'")
                return "recommendation", 0.85
        
        print("ℹ️ DEBUG: No recommendation patterns matched, defaulting to information")
        return "information", 0.7
    
    # Use transformer-based classification
    print("🔄 DEBUG: Using transformer-based intent classification")
    try:
        intents = ["recommendation", "information", "comparison", "technical question"]
        result = intent_classifier(query, intents, multi_label=False)
        intent = result["labels"][0]
        confidence = result["scores"][0]
        print(f"✅ DEBUG: Classified intent as '{intent}' with confidence {confidence:.2f}")
        
        # Return top intent and confidence
        return intent, confidence
    except Exception as e:
        print(f"❌ DEBUG: Error during intent classification: {e}")
        print("ℹ️ DEBUG: Falling back to default information intent")
        return "information", 0.6

def extract_user_preferences(context, query):
    """Extract user preferences from context and query"""
    print(f"\n🔍 DEBUG: Extracting preferences from context and query")
    # Default preferences
    preferences = {
        "budget": "$200",
        "use_case": "general listening",
        "preferred_type": "IEMs",
        "sound_signature": "balanced"
    }
    print(f"ℹ️ DEBUG: Starting with default preferences: {preferences}")
    
    # Budget extraction
    budget_match = re.search(r"(\$\d+(?:\s*-\s*\$?\d+)?|\d+\s*dollars?|\d+\s*USD)", context + " " + query)
    if budget_match:
        budget = budget_match.group(1)
        preferences["budget"] = budget
        print(f"✅ DEBUG: Extracted budget: {budget}")
    
    # Use case extraction
    use_cases = ["gaming", "studio", "mixing", "travel", "commuting", "workout", "exercise", 
                "casual", "audiophile", "professional", "stage", "monitoring"]
    for use_case in use_cases:
        if use_case in (context + " " + query).lower():
            preferences["use_case"] = use_case
            print(f"✅ DEBUG: Extracted use case: {use_case}")
            break
    
    # Preferred type extraction
    if "headphone" in (context + " " + query).lower():
        preferences["preferred_type"] = "Headphones"
        print("✅ DEBUG: Extracted preferred type: Headphones")
    elif "iem" in (context + " " + query).lower() or "in-ear" in (context + " " + query).lower():
        preferences["preferred_type"] = "IEMs"
        print("✅ DEBUG: Extracted preferred type: IEMs")
    elif "earbud" in (context + " " + query).lower():
        preferences["preferred_type"] = "Earbuds"
        print("✅ DEBUG: Extracted preferred type: Earbuds")
    
    # Sound signature extraction
    signatures = ["bass", "treble", "bright", "warm", "neutral", "balanced", "v-shaped", "analytical"]
    for signature in signatures:
        if signature in (context + " " + query).lower():
            preferences["sound_signature"] = signature
            print(f"✅ DEBUG: Extracted sound signature: {signature}")
            break
    
    return preferences

# Removed template functions in favor of inline f-string formatting

def generate_direct_llm_response(context, user_input, intent="general"):
    """
    Generate a response directly from the LLM when vector database is not available
    """
    print("\n🚀 DEBUG: Generating direct LLM response (fallback mode)")
    print(f"📝 DEBUG: Intent for fallback: {intent}")
    
    # Check for GROQ API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ DEBUG: GROQ_API_KEY not found for fallback mode")
        return f"Thanks for your question about audio equipment. Our AI response system is currently being updated. A human specialist from headphoneGeek will review your question and provide expert assistance shortly!"
    
    try:
        # Initialize LLM
        print(f"🔄 DEBUG: Initializing ChatGroq LLM for fallback mode")
        llm = ChatGroq(
            temperature=0.4,
            model_name="qwen-2.5-32b",
            api_key=groq_api_key
        )
        print("✅ DEBUG: ChatGroq LLM initialized successfully for fallback mode")
        
        # Create appropriate prompt based on intent
        if intent == "recommendation":
            prompt_template = """
            You are a knowledgeable audio specialist at headphoneGeek, a premium audio equipment retailer specializing in high-quality headphones and IEMs.
            
            The user is asking for recommendations about audio equipment. Since our database is being updated, you'll need to provide general advice rather than specific model recommendations.
            
            User query: {question}
            
            Please provide a helpful response that:
            1. Acknowledges their specific request
            2. Offers general advice about the type of product they're interested in
            3. Explains what features to look for when making their decision
            4. Provides information about common price ranges
            
            Format your response in a clear, engaging way with a confident, expert tone.
            Always start with an enthusiastic greeting that includes the headphoneGeek brand name.
            Explain that while we're updating our product database, a specialist will follow up with specific model recommendations shortly.
            End with a friendly note thanking them for their patience.
            """
        else:
            prompt_template = """
            You are a knowledgeable audio specialist at headphoneGeek, a premium audio equipment retailer specializing in high-quality headphones and IEMs.
            
            The user is asking for information about audio equipment. Since our database is being updated, you'll need to provide general knowledge rather than detailed technical explanations.
            
            User query: {question}
            
            Please provide a helpful response that:
            1. Addresses their question directly and concisely
            2. Offers general educational information about the topic
            3. Is technically accurate but not overly complex
            
            Format your response in a clear, engaging way with a confident, expert tone.
            Always start with an enthusiastic greeting that includes the headphoneGeek brand name.
            Explain that while we're updating our knowledge base, a specialist will follow up with more detailed information shortly.
            End with a friendly note thanking them for their patience.
            """
        
        print("🔄 DEBUG: Creating PromptTemplate for fallback")
        prompt = PromptTemplate.from_template(prompt_template)
        
        print("🔄 DEBUG: Creating LLM chain for fallback")
        chain = prompt | llm
        
        print("🔄 DEBUG: Executing fallback LLM chain")
        response = chain.invoke({"question": user_input})
        print("✅ DEBUG: Fallback chain executed successfully")
        print(f"📝 DEBUG: Response type: {type(response)}")
        
        # Extract text from response based on response type
        if hasattr(response, 'content'):
            result = response.content
        elif isinstance(response, str):
            result = response
        else:
            print(f"⚠️ DEBUG: Unexpected response format: {type(response)}")
            result = str(response)
        
        print(f"📝 DEBUG: Fallback result snippet (first 100 chars): {result[:100]}...")
        return result
    
    except Exception as e:
        print(f"❌ DEBUG: Error in fallback response generation: {e}")
        import traceback
        print(f"📋 DEBUG: Fallback traceback:\n{traceback.format_exc()}")
        return f"Hello from headphoneGeek! Thank you for your question about audio equipment. Our product database is currently being updated. A human specialist will review your question and provide expert assistance shortly. We appreciate your patience!"

def generate_rag_response(context, user_input):
    """
    Generate a response using the RAG system based on query intent
    """
    print("\n🚀 DEBUG: Starting RAG response generation")
    print(f"📝 DEBUG: Input context: '{context}'")
    print(f"📝 DEBUG: User input: '{user_input}'")
    
    # Detect query intent first - we'll need this for both RAG and fallback
    intent, confidence = detect_query_intent(user_input)
    print(f"📊 DEBUG: Query intent determined: {intent} (confidence: {confidence:.2f})")
    
    # Initialize RAG system
    qdrant = initialize_rag_system()
    if not qdrant:
        print("❌ DEBUG: Failed to initialize RAG system, using direct LLM fallback")
        return generate_direct_llm_response(context, user_input, intent)
    
    print("🔄 DEBUG: Checking for GROQ API key")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ DEBUG: GROQ_API_KEY not found in environment variables")
        return f"Thanks for your question about audio equipment. Our AI response system is currently being updated. A human specialist from headphoneGeek will review your question and provide expert assistance shortly!"
    
    try:
        # Initialize LLM
        print(f"🔄 DEBUG: Initializing ChatGroq LLM with API key: {groq_api_key[:4]}...")
        llm = ChatGroq(
            temperature=0.3,
            model_name="qwen-2.5-32b",
            api_key=groq_api_key
        )
        print("✅ DEBUG: ChatGroq LLM initialized successfully")
    except Exception as e:
        print(f"❌ DEBUG: Error initializing LLM: {e}")
        return generate_direct_llm_response(context, user_input, intent)
    
    try:
        if intent == "recommendation":
            print("🔄 DEBUG: Processing as recommendation query")
            # Extract user preferences
            preferences = extract_user_preferences(context, user_input)
            print(f"👤 DEBUG: Extracted preferences: {preferences}")
            
            # Create recommendation prompt using f-string formatting
            print("🔄 DEBUG: Creating recommendation prompt with f-string")
            formatted_prompt = f"""
            You are a knowledgeable audio specialist at headphoneGeek, a premium audio equipment retailer specializing in high-quality headphones and IEMs.
            
            Use the following information to provide personalized audio equipment recommendations based on the user's query and preferences.
            
            Context: {context}
            
            User Preferences:
            - Budget: {preferences.get("budget")}
            - Use Case: {preferences.get("use_case")}
            - Preferred Type: {preferences.get("preferred_type")}
            - Sound Signature Preference: {preferences.get("sound_signature")}
            
            Query: {user_input}
            
            Provide detailed recommendations that match the user's preferences with a confident, expert tone. Focus on:
            1. Specific model recommendations that fit their requirements
            2. Key features and benefits of each recommended product
            3. Comparisons between options to help them make an informed decision
            4. Value proposition (what makes each option worth its price)
            
            Format your response in a clear, engaging way that showcases headphoneGeek's technical expertise and passion for quality audio.
            Always start with an enthusiastic greeting that includes the headphoneGeek brand name.
            End your response with a friendly offer to provide more specific recommendations if needed.
            """
            
            # Create RetrievalQA chain
            print("🔄 DEBUG: Creating RetrievalQA chain for recommendation")
            try:
                retriever = qdrant.as_retriever(search_kwargs={"k": 5})
                print("✅ DEBUG: Retriever created successfully")
            except Exception as retriever_err:
                print(f"❌ DEBUG: Error creating retriever: {retriever_err}")
                return generate_direct_llm_response(context, user_input, intent)
            
            try:
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=False,
                    chain_type_kwargs={"verbose": True},
                )
                print("✅ DEBUG: RetrievalQA chain created successfully")
            except Exception as chain_err:
                print(f"❌ DEBUG: Error creating QA chain: {chain_err}")
                return generate_direct_llm_response(context, user_input, intent)
            
            # Execute the query with formatted prompt
            print("🔄 DEBUG: Executing recommendation query with formatted prompt")
            try:
                response = qa.invoke({
                    "query": formatted_prompt,
                    "context": context
                })
                print("✅ DEBUG: Query executed successfully")
                print(f"📝 DEBUG: Response result type: {type(response)}")
                print(f"📝 DEBUG: Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
                
                if isinstance(response, dict) and "result" in response:
                    result = response["result"]
                    print(f"📝 DEBUG: Result snippet (first 100 chars): {result[:100]}...")
                    return result
                else:
                    print("❌ DEBUG: Response missing 'result' key or not a dict")
                    return generate_direct_llm_response(context, user_input, intent)
            except Exception as query_err:
                print(f"❌ DEBUG: Error executing recommendation query: {query_err}")
                return generate_direct_llm_response(context, user_input, intent)
        else:
            print("🔄 DEBUG: Processing as information query")
            # Create information prompt using f-string
            print("🔄 DEBUG: Creating information prompt with f-string")
            formatted_prompt = f"""
            You are a knowledgeable audio specialist at headphoneGeek, a premium audio equipment retailer specializing in high-quality headphones and IEMs.
            
            Use the following reference information to answer the user's question about audio equipment:
            
            Reference Information: {context}
            
            Query: {user_input}
            
            Provide a helpful, educational response that showcases headphoneGeek's technical expertise and passion for quality audio. Your response should:
            1. Be informative and technically accurate
            2. Explain concepts clearly without being condescending
            3. Include relevant facts and educational details
            4. Showcase the depth of knowledge that makes headphoneGeek a trusted authority
            
            Format your response in a clear, engaging way with a confident, expert tone.
            Always start with an enthusiastic greeting that includes the headphoneGeek brand name.
            End your response with a friendly offer to provide more information or recommendations if needed.
            """
            
            # Create RetrievalQA chain
            print("🔄 DEBUG: Creating RetrievalQA chain for information")
            try:
                retriever = qdrant.as_retriever(search_kwargs={"k": 3})
                print("✅ DEBUG: Retriever created successfully")
            except Exception as retriever_err:
                print(f"❌ DEBUG: Error creating retriever: {retriever_err}")
                return generate_direct_llm_response(context, user_input, intent)
            
            try:
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=False,
                    chain_type_kwargs={"verbose": True},
                )
                print("✅ DEBUG: RetrievalQA chain created successfully")
            except Exception as chain_err:
                print(f"❌ DEBUG: Error creating QA chain: {chain_err}")
                return generate_direct_llm_response(context, user_input, intent)
            
            # Execute the query with formatted prompt
            print("🔄 DEBUG: Executing information query with formatted prompt")
            try:
                response = qa.invoke({
                    "query": formatted_prompt,
                    "context": context
                })
                print("✅ DEBUG: Query executed successfully")
                print(f"📝 DEBUG: Response result type: {type(response)}")
                print(f"📝 DEBUG: Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
                
                if isinstance(response, dict) and "result" in response:
                    result = response["result"]
                    print(f"📝 DEBUG: Result snippet (first 100 chars): {result[:100]}...")
                    return result
                else:
                    print("❌ DEBUG: Response missing 'result' key or not a dict")
                    return generate_direct_llm_response(context, user_input, intent)
            except Exception as query_err:
                print(f"❌ DEBUG: Error executing information query: {query_err}")
                return generate_direct_llm_response(context, user_input, intent)
    except Exception as e:
        print(f"❌ DEBUG: Unexpected error generating RAG response: {e}")
        import traceback
        print(f"📋 DEBUG: Full traceback:\n{traceback.format_exc()}")
        return generate_direct_llm_response(context, user_input, intent)

def send_to_slack(context, generated_response, source, message_id, channel_id):
    """
    Send the generated response and context to Slack for manual approval.
    """
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text="🔍 *New AI Response Pending Approval* 🔍",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"📌 *Source:* {source}\n"
                            f"📜 *Context:* {context}\n"
                            f"💡 *Generated Response:* {generated_response}\n\n"
                            f"Reply with `yes` or `y` in this thread to approve."
                        ),
                    },
                }
            ],
        )

        if response["ok"]:
            thread_ts = response["ts"]
            print(f"✅ Sent approval request to Slack for {source} - {message_id}")
            
            # Load existing pending responses
            file_pending_responses = load_pending_responses()
            
            # Store the pending response for Slack approval (both in memory and file)
            pending_responses[thread_ts] = (message_id, channel_id, source, generated_response)
            file_pending_responses[thread_ts] = [message_id, channel_id, source, generated_response]
            
            # Save updated pending responses to file
            save_pending_responses(file_pending_responses)
            
            print(f"💾 Saved pending response to file for thread {thread_ts}")
        else:
            print(f"⚠️ Failed to send to Slack: {response['error']}")

    except SlackApiError as e:
        print(f"⚠️ Slack API Error: {e.response['error']}")

if __name__ == "__main__":
    # Example usage
    test_context = "Example context"
    test_message_id = 12345
    test_channel_id = 67890
    rag_response = generate_rag_response(test_context, "Can you recommend some good IEMs under $200 for commuting?")
    send_to_slack(test_context, rag_response, "testing", test_message_id, test_channel_id)