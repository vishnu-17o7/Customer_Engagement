import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import discord
import praw
from discord.ext import tasks
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

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

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

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

# Dictionary to track pending responses
# Key: Slack thread timestamp (or message ID)
# Value: tuple(message_id, channel_id, source, response_text)
pending_responses = {}

async def check_slack_approvals():
    """
    Fetch recent messages from Slack and check for approvals.
    """
    print("🔍 Checking Slack for approvals...")
    try:
        response = await asyncio.to_thread(slack_client.conversations_history, channel=SLACK_CHANNEL_ID, limit=10)
        
        if not response.get("ok"):
            print(f"⚠️ Slack API Error: {response['error']}")
            return

        print(f"📥 Retrieved {len(response['messages'])} messages from Slack.")

        for message in response["messages"]:
            thread_ts = message.get("ts")  # Main message timestamp
            print(f"🔄 Processing Slack message: {thread_ts}")

            if thread_ts in pending_responses and message.get("reply_count", 0) > 0:
                print(f"💬 Checking replies for message {thread_ts}...")

                replies = await asyncio.to_thread(slack_client.conversations_replies, channel=SLACK_CHANNEL_ID, ts=thread_ts)

                for reply in replies.get("messages", []):
                    text = reply.get("text", "").strip().lower()
                    print(f"💡 Found reply: {text}")

                    if text in ["yes", "y"]:
                        print(f"✅ Approval detected for {thread_ts}!")

                        message_id, channel_id, source, response_text = pending_responses.pop(thread_ts)
                        
                        if source == "discord":
                            print(f"🚀 Sending approved response to Discord (Channel: {channel_id}, Message: {message_id})...")
                            bot.loop.create_task(approve_discord_reply(channel_id, message_id, response_text))
                        elif source == "reddit":
                            print(f"🚀 Sending approved response to Reddit (Post: {message_id})...")
                            approve_reddit_reply(message_id, response_text)
                        break  # Stop checking after first approval
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

        print(f"📌 Found Discord channel: {channel.name}")

        message = await channel.fetch_message(int(message_id))
        print(f"📩 Found message: {message.content}")

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

        print(f"📌 Found Reddit post: {submission.title}")
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
