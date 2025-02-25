import praw
import mysql.connector
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
from slack_approval import pending_responses

# Reddit API setup - replace with your credentials.
reddit = praw.Reddit(
    client_id="kvBRHQxAcAoggL2pOYEI5w",
    client_secret="-9M0aBpNkFK88ih1RA9s9oigJve1oA",
    password="GVuK3H#YsHN6J:672882",
    user_agent="testscript",
    username="MonsterBottie007",
)

# MySQL connection setup (ensure your database and table are created)
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="reddit_db"
)
cursor = db.cursor()

# List of subreddits to monitor.
subreddits = ["inearfidelity", "mechanicalkeyboards"]

for sub in subreddits:
    subreddit = reddit.subreddit(sub)
    for post in subreddit.hot(limit=10):
        analysis = analyze_text(post.title)
        if analysis["relevant"]:
            rag_response = generate_rag_response(analysis["text"], post.title)
            
            # Send for Slack approval.
            send_to_slack(analysis["text"], rag_response, "reddit", post.id)
            
            # Store the pending response.
            pending_responses[post.id] = (post.id, "reddit", rag_response)
            
            print(f"Pending approval for Reddit post {post.id}: {rag_response}")
            
            # Optional: Save details to the database.
            cursor.execute(
                "INSERT INTO posts (post_id, title, category, confidence, response, subreddit) VALUES (%s, %s, %s, %s, %s, %s)",
                (post.id, post.title, analysis["category"], analysis["confidence"], rag_response, sub)
            )
            db.commit()

cursor.close()
db.close()
