import praw
import mysql.connector
import os
from dotenv import load_dotenv
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
from slack_approval import pending_responses

# Load environment variables
load_dotenv()

# Reddit API setup
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    user_agent=os.getenv("REDDIT_USER_AGENT"),
    username=os.getenv("REDDIT_USERNAME"),
)

# MySQL Database connection
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "reddit_db")

try:
    db = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = db.cursor()
    print("✅ Connected to MySQL database")
except mysql.connector.Error as err:
    print(f"⚠️ MySQL connection error: {err}")
    exit()

# List of subreddits to monitor.
subreddits = ["inearfidelity", "mechanicalkeyboards"]

def process_reddit_posts():
    for sub in subreddits:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.hot(limit=10):  # Fetch top 10 posts
            analysis = analyze_text(post.title)

            if analysis["relevant"]:
                rag_response = generate_rag_response(analysis["text"], post.title)

                # Send for Slack approval & store Slack thread_ts
                thread_ts = send_to_slack(analysis["text"], rag_response, "reddit", post.id, None)

                # Store pending approval using Slack thread_ts
                if thread_ts:
                    print(f"📌 Pending approval for Reddit post {post.id}: {rag_response}")

                    # Insert details into MySQL database
                    try:
                        cursor.execute(
                            """
                            INSERT INTO posts (post_id, title, category, confidence, response, subreddit)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE response = VALUES(response);
                            """,
                            (post.id, post.title, analysis["category"], analysis["confidence"], rag_response, sub)
                        )
                        db.commit()
                    except mysql.connector.Error as err:
                        print(f"⚠️ MySQL insert error: {err}")

if __name__ == "__main__":
    process_reddit_posts()
    cursor.close()
    db.close()
    print("✅ Process completed, database connection closed.")
