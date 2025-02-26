import os
from dotenv import load_dotenv
import praw
import mysql.connector

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
)

# MySQL Connection Setup
db = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST", "localhost"),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", "root"),
    database=os.getenv("MYSQL_DATABASE", "reddit_db")
)
cursor = db.cursor()

# Adjust table schema to match usage in reddit_bot.py:
cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        post_id VARCHAR(20) PRIMARY KEY,
        title TEXT,
        category TEXT,
        confidence FLOAT,
        response TEXT,
        subreddit TEXT,
        score INT,
        url TEXT
    )
""")

# Fetch top 10 posts from a subreddit
subreddit_name = "inearfidelity"  # Change this to your preferred subreddit
subreddit = reddit.subreddit(subreddit_name)

top_posts = []
for submission in subreddit.top(limit=10):
    top_posts.append((submission.id, submission.title, submission.score, submission.url))

# Insert data into MySQL
cursor.executemany("INSERT IGNORE INTO posts (post_id, title, score, url) VALUES (%s, %s, %s, %s)", top_posts)

# Commit and close
db.commit()
cursor.close()
db.close()

print("Top 10 posts stored successfully in MySQL.")
