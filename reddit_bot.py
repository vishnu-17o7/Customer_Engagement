import praw
import os
from dotenv import load_dotenv
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
from db_utils import store_reddit_post
from slack_approval import pending_responses
import prawcore.exceptions

# Load environment variables
load_dotenv()

# Print environment variables for debugging (redacted for security)
reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_username = os.getenv("REDDIT_USERNAME")
reddit_password = os.getenv("REDDIT_PASSWORD")
reddit_user_agent = os.getenv("REDDIT_USER_AGENT") or os.getenv("USER_AGENT")

print(f"Reddit API credentials: Client ID: {reddit_client_id[:4]}*** Username: {reddit_username}")

# Reddit API setup with improved error handling
try:
    # Use same approach as redditPraw.py (no explicit authentication verification)
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        password=os.getenv("REDDIT_PASSWORD"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
        username=os.getenv("REDDIT_USERNAME"),
    )
    print("✅ Connected to Reddit API")
except prawcore.exceptions.ResponseException as auth_error:
    print(f"⚠️ Reddit API authentication error: {auth_error}")
    print("⚠️ Please check your Reddit API credentials in the .env file")
    reddit = None
except Exception as e:
    print(f"⚠️ Error initializing Reddit API client: {e}")
    reddit = None

# List of subreddits to monitor
subreddits = ["inearfidelity", "mechanicalkeyboards"]

def process_reddit_posts():
    """Process Reddit posts with error handling for API issues"""
    if reddit is None:
        print("❌ Reddit API client not initialized. Skipping Reddit post processing.")
        return
    
    print("🔍 Starting to process Reddit posts with sentiment analysis")
    
    for sub in subreddits:
        print(f"📊 Processing subreddit: r/{sub}")
        try:
            subreddit = reddit.subreddit(sub)
            
            # Test the subreddit access with a simple property
            display_name = subreddit.display_name
            print(f"✅ Successfully accessed subreddit: r/{display_name}")
            
            # Process posts with proper error handling
            try:
                # Use top() method instead of hot() (matches redditPraw.py)
                for post in subreddit.top(limit=10):  # Fetch top 10 posts
                    try:
                        analysis = analyze_text(post.title)
                        
                        if analysis["relevant"]:
                            print(f"✓ Relevant post found: {post.id} - {post.title}")
                            # Generate response
                            rag_response = generate_rag_response(analysis["text"], post.title)
                            
                            # First, ensure the post is stored in the database regardless of Slack status
                            try:
                                # Store post in database with sentiment analysis
                                store_result = store_reddit_post(
                                    post.id,
                                    post.title,
                                    analysis["category"],
                                    analysis["confidence"],
                                    rag_response,
                                    sub,
                                    post.score,
                                    post.url
                                )
                                
                                if store_result:
                                    print(f"✅ Stored post with sentiment analysis: {post.id}")
                                else:
                                    print(f"⚠️ Failed to store post: {post.id}")
                            except Exception as db_err:
                                print(f"⚠️ Error storing Reddit post in database: {db_err}")
                            
                            # Then try to send to Slack for approval
                            try:
                                # Send for Slack approval
                                thread_ts = send_to_slack(analysis["text"], rag_response, "reddit", post.id, None)
                                
                                if thread_ts:
                                    print(f"✅ Successfully sent to Slack for approval: {post.id}")
                                else:
                                    print(f"⚠️ Failed to send to Slack for approval: {post.id}")
                            except Exception as slack_err:
                                print(f"⚠️ Error sending to Slack: {slack_err}")
                    except Exception as post_err:
                        print(f"⚠️ Error processing post: {post_err}")
                        continue
            except prawcore.exceptions.ResponseException as api_err:
                print(f"⚠️ Reddit API error when fetching posts: {api_err}")
            except Exception as fetch_err:
                print(f"⚠️ Error fetching posts from subreddit r/{sub}: {fetch_err}")
        except prawcore.exceptions.ResponseException as sub_err:
            print(f"⚠️ Reddit API error accessing subreddit r/{sub}: {sub_err}")
        except Exception as e:
            print(f"⚠️ Error accessing subreddit r/{sub}: {e}")

if __name__ == "__main__":
    process_reddit_posts()
    print("✅ Process completed.")
