import praw
import mysql.connector

reddit = praw.Reddit(
    client_id="kvBRHQxAcAoggL2pOYEI5w",
    client_secret="-9M0aBpNkFK88ih1RA9s9oigJve1oA",
    password="GVuK3H#YsHN6J:672882",
    user_agent="testscript",
    username="MonsterBottie007",
)

# MySQL Connection Setup
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="reddit_db"
)
cursor = db.cursor()

# Ensure table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id VARCHAR(20) PRIMARY KEY,
        title TEXT,
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
cursor.executemany("INSERT IGNORE INTO posts (id, title, score, url) VALUES (%s, %s, %s, %s)", top_posts)

# Commit and close
db.commit()
cursor.close()
db.close()

print("Top 10 posts stored successfully in MySQL.")
