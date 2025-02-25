#### filepath: /c:/Users/vishn/Desktop/Programs/Customer_Engagement/slack_approval.py
import os
import sys
import asyncio
import discord
import praw
import json
from discord.ext import tasks
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Slack API credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Discord API credentials
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Reddit API credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
USER_AGENT = os.getenv("USER_AGENT")

# Path for shared pending responses file
PENDING_RESPONSES_FILE = "pending_responses.json"

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Function to load pending responses from file
def load_pending_responses():
    """Load pending responses from JSON file"""
    try:
        if os.path.exists(PENDING_RESPONSES_FILE):
            with open(PENDING_RESPONSES_FILE, 'r') as f:
                file_responses = json.load(f)
                
                # Convert list values back to tuples for compatibility
                converted_responses = {}
                for key, value in file_responses.items():
                    converted_responses[key] = tuple(value)
                
                print(f"📁 Loaded {len(converted_responses)} pending responses from file")
                return converted_responses
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
        print(f"💾 Saved {len(responses)} pending responses to file")
    except Exception as e:
        print(f"⚠️ Error saving pending responses: {e}")

# Initialize Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = discord.Client(intents=intents)

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent="testscript",
)

# Shared dictionary to track pending responses
# Key: Slack thread timestamp (main message ID)
# Value: tuple(message_id, channel_id, source, response_text)
pending_responses = {}

async def check_slack_approvals():
    """
    Fetch recent messages from Slack and check for approvals.
    """
    print("🔍 Checking Slack for approvals...")
    try:
        # First update the pending_responses from file
        file_responses = load_pending_responses()
        for key, value in file_responses.items():
            if key not in pending_responses:
                pending_responses[key] = value
        
        response = await asyncio.to_thread(slack_client.conversations_history, channel=SLACK_CHANNEL_ID, limit=10)
        
        if not response.get("ok"):
            print(f"⚠️ Slack API Error: {response['error']}")
            return

        print(f"📥 Retrieved {len(response.get('messages', []))} messages from Slack.")
        print(f"🔑 Current pending_responses keys (from memory): {list(pending_responses.keys())}")
        print(f"🔑 Current pending_responses keys (from file): {list(file_responses.keys())}")
        
        for message in response["messages"]:
            thread_ts = message.get("ts")
            print(f"🧵 Checking message with ts: {thread_ts}")
            
            if thread_ts in pending_responses:
                print(f"✅ Found match in pending_responses for ts: {thread_ts}")
                reply_count = message.get("reply_count", 0)
                print(f"💬 Reply count: {reply_count}")
                
                if reply_count > 0:
                    # Retrieve replies
                    replies = await asyncio.to_thread(slack_client.conversations_replies, channel=SLACK_CHANNEL_ID, ts=thread_ts)
                    print(f"📩 Retrieved {len(replies.get('messages', []))} replies for thread {thread_ts}")
                    
                    for reply in replies.get("messages", []):
                        text = reply.get("text", "").strip().lower()
                        print(f"📝 Checking reply text: '{text}'")
                        
                        if text in ["yes", "y"]:
                            print(f"✅ Approval found in reply: '{text}'")
                            # Get response info and remove from both memory and file
                            message_id, channel_id, source, response_text = pending_responses.pop(thread_ts)
                            
                            # Update the file to remove this entry
                            file_responses = load_pending_responses()
                            if thread_ts in file_responses:
                                file_responses.pop(thread_ts)
                                save_pending_responses(file_responses)
                                print(f"🗑️ Removed approved response from file for thread {thread_ts}")
                            print(f"📤 Processing approval for {source} message {message_id}")

                            if source == "discord":
                                await approve_discord_reply(channel_id, message_id, response_text)
                            elif source == "reddit":
                                approve_reddit_reply(message_id, response_text)

    except SlackApiError as e:
        print(f"⚠️ Slack API Error: {e.response['error']}")

async def approve_discord_reply(channel_id, message_id, response_text):
    """
    Approve and post the response to Discord.
    """
    print(f"🔄 Attempting to approve Discord reply: Channel {channel_id}, Message {message_id}")
    try:
        channel = await bot.fetch_channel(int(channel_id))
        if channel is None:
            print(f"⚠️ Channel {channel_id} not found in Discord.")
            return

        message = await channel.fetch_message(int(message_id))
        await message.reply(response_text)
        print(f"✅ Approved response posted to Discord: {response_text}")

    except discord.errors.NotFound:
        print(f"⚠️ Message {message_id} not found in Discord.")
    except discord.errors.Forbidden:
        print(f"⚠️ Bot does not have permission to reply in channel {channel_id}.")
    except Exception as e:
        print(f"⚠️ Unexpected error approving Discord reply: {e}")

def approve_reddit_reply(message_id, response_text):
    """
    Approve and post the response to Reddit.
    """
    print(f"🔄 Attempting to approve Reddit reply for post {message_id}...")
    try:
        submission = reddit.submission(id=message_id)
        if submission.locked:
            print(f"⚠️ Cannot reply to locked Reddit post {message_id}.")
            return
        submission.reply(response_text)
        print(f"✅ Approved response posted to Reddit: {response_text}")

    except praw.exceptions.APIException as e:
        print(f"⚠️ Reddit API error: {e}")
    except Exception as e:
        print(f"⚠️ Error posting to Reddit: {e}")

@tasks.loop(seconds=10)
async def slack_checker():
    await check_slack_approvals()

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    print("🔄 Starting Slack checker loop...")
    slack_checker.start()

if __name__ == "__main__":
    print("🚀 Starting bot...")
    bot.run(DISCORD_BOT_TOKEN)