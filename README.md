# Audio Equipment Recommendation System

This system provides audio equipment recommendations using Retrieval Augmented Generation (RAG) with the comprehensive audio equipment guide.

## Setup

1. Install the required packages:
   ```
   pip install langchain langchain_groq fastembed qdrant-client python-dotenv unstructured
   ```

2. Create a `.env` file with your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key
   ```

## How to Use

### Step 1: Create the Vector Database

Run the following script to create the vector database from the audio equipment guide:

```bash
python create_audio_vectordb.py
```

This only needs to be done once or whenever the audio equipment guide is updated.

### Step 2: Query for Recommendations

Run the query script to get recommendations:

```bash
python query_audio_guide.py
```

You can modify the example queries and user preferences in the script to get different recommendations.

## Customizing Queries

To customize recommendations in your code, import and use the function like this:

```python
from query_audio_guide import get_audio_recommendations, print_response

user_preferences = {
    "budget": "$300",
    "use_case": "studio monitoring",
    "preferred_type": "headphones",
    "sound_signature": "neutral"
}

response = get_audio_recommendations(
    "What are the best options for my use case?", 
    user_preferences
)
print_response(response)
```

## About the System

This system uses:
- LangChain for the RAG pipeline
- FastEmbed for embeddings
- Qdrant for vector storage
- Groq LLM (qwen-2.5-32b) for generating recommendations
