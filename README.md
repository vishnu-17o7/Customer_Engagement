# HeadphoneGeek Customer Engagement System

A comprehensive system for tracking, analyzing, and responding to customer queries across Discord and Reddit platforms.

## Features

- **Multi-Platform Integration**: Monitor and respond to queries from Discord and Reddit
- **Relevance Analysis**: Automatically detect relevant audio equipment queries
- **RAG-Powered Responses**: Generate accurate responses using a vector database of audio equipment knowledge
- **Sentiment Analysis**: Analyze customer sentiment in queries with VADER sentiment analysis
- **ADORE Score**: Track Audience Delight and Orientation Response Evaluation metrics
- **Streamlit Dashboard**: Visualize engagement metrics, sentiment trends, and platform analytics
- **Manual Approval Workflow**: Send responses to Slack for expert review before replying

## System Architecture

The system consists of the following components:

- **Discord Bot**: Monitors Discord channels for relevant queries
- **Reddit Bot**: Monitors subreddits for relevant audio equipment posts
- **RAG System**: Processes queries against an audio equipment knowledge base
- **MySQL Database**: Stores relevant queries with sentiment analysis
- **Database Utilities**: Centralizes database operations and sentiment analysis
- **Streamlit Dashboard**: Provides visualization of engagement metrics
- **Slack Approval**: Facilitates human review of AI-generated responses

## Setup Instructions

1. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Create or update a `.env` file with the following credentials:
   - Discord, Reddit, and Slack API credentials
   - Groq API key for LLM access
   - MySQL database credentials

3. **Initialize Database**:
   ```
   python db_utils.py
   ```

4. **Create Audio Equipment Vector Database** (if not already done):
   ```
   python create_audio_vectordb.py
   ```

## Running the System

### Discord Bot

```
python discord_bot.py
```

### Reddit Bot

```
python reddit_bot.py
```

### Streamlit Dashboard

```
streamlit run dashboard.py
```

## Database Schema

The system uses the following database tables:

1. **discord_messages**: Stores relevant Discord queries with sentiment analysis
2. **reddit_posts**: Stores relevant Reddit posts with sentiment analysis
3. **analytics**: Stores aggregated metrics for dashboard visualizations

## ADORE Score

The ADORE (Audience Delight and Orientation Response Evaluation) score is calculated as:

```
ADORE Score = ((positive - negative) / total) * 50 + 50
```

This creates a score from 0-100 where:
- 50 is neutral
- Above 50 indicates positive sentiment
- Below 50 indicates negative sentiment

## Maintenance

- Run Discord and Reddit bots regularly to collect new queries
- Monitor the Slack channel for pending approvals
- Check the dashboard for sentiment trends and customer engagement metrics
- Update the audio equipment vector database as new products and information become available