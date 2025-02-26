import os
import mysql.connector
from dotenv import load_dotenv
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
from datetime import datetime

# Download NLTK resources for sentiment analysis
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

# Load environment variables
load_dotenv()

# MySQL connection parameters
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "customer_engagement_db")

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

def get_db_connection():
    """Create and return a MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        # Create database if it doesn't exist
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        cursor.execute(f"USE {MYSQL_DATABASE}")
        create_tables(connection)
        return connection
    except mysql.connector.Error as err:
        print(f"⚠️ Database connection error: {err}")
        return None

def create_tables(connection):
    """Create necessary tables if they don't exist"""
    cursor = connection.cursor()
    
    # Create table for Reddit posts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_posts (
            post_id VARCHAR(20) PRIMARY KEY,
            title TEXT,
            category VARCHAR(50),
            confidence FLOAT,
            response TEXT,
            subreddit VARCHAR(50),
            score INT,
            url TEXT,
            sentiment_score FLOAT,
            sentiment_label VARCHAR(20),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create table for Discord messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discord_messages (
            message_id VARCHAR(20) PRIMARY KEY,
            channel_id VARCHAR(20),
            content TEXT,
            category VARCHAR(50),
            confidence FLOAT,
            response TEXT,
            sentiment_score FLOAT,
            sentiment_label VARCHAR(20),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create table for aggregated analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            platform VARCHAR(20),
            date DATE,
            query_count INT,
            avg_sentiment FLOAT,
            adore_score FLOAT,
            positive_count INT,
            negative_count INT,
            neutral_count INT
        )
    """)
    
    connection.commit()

def analyze_sentiment(text):
    """Analyze sentiment of text using VADER"""
    sentiment = sia.polarity_scores(text)
    compound_score = sentiment['compound']
    
    # Determine sentiment label
    if compound_score >= 0.05:
        label = "positive"
    elif compound_score <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        "score": compound_score,
        "label": label,
        "detailed_scores": sentiment
    }

def store_reddit_post(post_id, title, category, confidence, response, subreddit, score=0, url=""):
    """Store a Reddit post with sentiment analysis"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Analyze sentiment
    sentiment = analyze_sentiment(title)
    
    try:
        cursor.execute("""
            INSERT INTO reddit_posts 
            (post_id, title, category, confidence, response, subreddit, score, url, sentiment_score, sentiment_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            title = VALUES(title),
            category = VALUES(category),
            confidence = VALUES(confidence),
            response = VALUES(response),
            subreddit = VALUES(subreddit),
            score = VALUES(score),
            url = VALUES(url),
            sentiment_score = VALUES(sentiment_score),
            sentiment_label = VALUES(sentiment_label)
        """, (
            post_id, title, category, confidence, response, subreddit, score, url, 
            sentiment["score"], sentiment["label"]
        ))
        connection.commit()
        update_analytics("reddit")
        return True
    except mysql.connector.Error as err:
        print(f"⚠️ Error storing Reddit post: {err}")
        return False
    finally:
        cursor.close()
        connection.close()

def store_discord_message(message_id, channel_id, content, category, confidence, response):
    """Store a Discord message with sentiment analysis"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    
    # Analyze sentiment
    sentiment = analyze_sentiment(content)
    
    try:
        cursor.execute("""
            INSERT INTO discord_messages 
            (message_id, channel_id, content, category, confidence, response, sentiment_score, sentiment_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            channel_id = VALUES(channel_id),
            content = VALUES(content),
            category = VALUES(category),
            confidence = VALUES(confidence),
            response = VALUES(response),
            sentiment_score = VALUES(sentiment_score),
            sentiment_label = VALUES(sentiment_label)
        """, (
            message_id, channel_id, content, category, confidence, response,
            sentiment["score"], sentiment["label"]
        ))
        connection.commit()
        update_analytics("discord")
        return True
    except mysql.connector.Error as err:
        print(f"⚠️ Error storing Discord message: {err}")
        return False
    finally:
        cursor.close()
        connection.close()

def update_analytics(platform):
    """Update analytics table with aggregated data"""
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = connection.cursor()
    today = datetime.now().date()
    
    try:
        # Get today's sentiment stats for the platform
        if platform == "reddit":
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(sentiment_score) as avg_sentiment,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM reddit_posts
                WHERE DATE(timestamp) = %s
            """, (today,))
        else:  # discord
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(sentiment_score) as avg_sentiment,
                    SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                FROM discord_messages
                WHERE DATE(timestamp) = %s
            """, (today,))
        
        result = cursor.fetchone()
        
        if result:
            query_count, avg_sentiment, positive_count, negative_count, neutral_count = result
            
            # Calculate ADORE score: (positive - negative) / total * 100 + 50
            # This creates a score from 0-100 where 50 is neutral
            total = positive_count + negative_count + neutral_count
            adore_score = 50  # Default neutral
            if total > 0:
                adore_score = ((positive_count - negative_count) / total) * 50 + 50
            
            # Check if entry exists for today
            cursor.execute("""
                SELECT id FROM analytics 
                WHERE platform = %s AND date = %s
            """, (platform, today))
            
            existing_id = cursor.fetchone()
            
            if existing_id:
                # Update existing record
                cursor.execute("""
                    UPDATE analytics
                    SET query_count = %s,
                        avg_sentiment = %s,
                        adore_score = %s,
                        positive_count = %s,
                        negative_count = %s,
                        neutral_count = %s
                    WHERE id = %s
                """, (
                    query_count, avg_sentiment, adore_score, 
                    positive_count, negative_count, neutral_count,
                    existing_id[0]
                ))
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO analytics
                    (platform, date, query_count, avg_sentiment, adore_score, positive_count, negative_count, neutral_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    platform, today, query_count, avg_sentiment, adore_score,
                    positive_count, negative_count, neutral_count
                ))
            
            connection.commit()
    except mysql.connector.Error as err:
        print(f"⚠️ Error updating analytics: {err}")
        return False
    finally:
        cursor.close()
        connection.close()
    
    return True

def get_analytics_data(days=30, platform=None):
    """Get analytics data for dashboard"""
    connection = get_db_connection()
    if not connection:
        print("❌ Database connection failed")
        return None
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Add more detailed logging
        print(f"🔍 Retrieving analytics data: days={days}, platform={platform}")
        
        # Modify query to ensure we always have data
        base_query = """
            SELECT 
                platform, 
                date, 
                COALESCE(query_count, 0) as query_count, 
                COALESCE(avg_sentiment, 0) as avg_sentiment, 
                COALESCE(adore_score, 50) as adore_score, 
                COALESCE(positive_count, 0) as positive_count, 
                COALESCE(negative_count, 0) as negative_count, 
                COALESCE(neutral_count, 0) as neutral_count
            FROM analytics
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        """
        
        if platform:
            query = base_query + " AND platform = %s ORDER BY date"
            params = (days, platform)
        else:
            query = base_query + " ORDER BY date, platform"
            params = (days,)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Log results for debugging
        print(f"📊 Retrieved {len(results)} analytics records")
        
        # If no results, generate sample data
        if not results:
            print("⚠️ No analytics data found. Generating sample data.")
            results = generate_sample_analytics_data(days, platform)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date')
        
        return df
    
    except mysql.connector.Error as err:
        print(f"❌ Error retrieving analytics data: {err}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def generate_sample_analytics_data(days, platform=None):
    """Generate sample analytics data when no real data exists"""
    import numpy as np
    
    # Create date range
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days)
    
    # Define platforms
    platforms = [platform] if platform else ['discord', 'reddit']
    
    # Generate sample data
    sample_data = []
    for plat in platforms:
        for date in dates:
            sample_data.append({
                'platform': plat,
                'date': date.date(),
                'query_count': np.random.randint(10, 100),
                'avg_sentiment': np.random.uniform(-1, 1),
                'adore_score': np.random.uniform(0, 100),
                'positive_count': np.random.randint(0, 50),
                'negative_count': np.random.randint(0, 50),
                'neutral_count': np.random.randint(0, 50)
            })
    
    return sample_data

def get_recent_queries(platform, limit=10):
    """Get recent queries for a specific platform"""
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = connection.cursor()
    
    try:
        if platform == "reddit":
            cursor.execute("""
                SELECT post_id, title, category, confidence, sentiment_score, sentiment_label, timestamp
                FROM reddit_posts
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
        else:  # discord
            cursor.execute("""
                SELECT message_id, content, category, confidence, sentiment_score, sentiment_label, timestamp
                FROM discord_messages
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
        
        columns = [col[0] for col in cursor.description]
        results = cursor.fetchall()
        
        # Convert to DataFrame
        df = pd.DataFrame(results, columns=columns)
        return df
    
    except mysql.connector.Error as err:
        print(f"⚠️ Error retrieving recent queries: {err}")
        return None
    finally:
        cursor.close()
        connection.close()

def initialize_db():
    """Initialize the database and create tables"""
    connection = get_db_connection()
    if connection:
        connection.close()
        print("✅ Database initialized successfully.")
    else:
        print("❌ Failed to initialize database.")

if __name__ == "__main__":
    initialize_db()