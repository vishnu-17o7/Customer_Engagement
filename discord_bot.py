#### filepath: /c:/Users/vishn/Desktop/Programs/Customer_Engagement/discord_bot.py
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import discord
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
from db_utils import store_discord_message
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Sentiment analysis and database storage enabled')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    analysis = analyze_text(message.content)
    
    if analysis["relevant"]:
        # Generate response
        rag_response = generate_rag_response(analysis["text"], message.content)

        # Get channel ID
        channel_id = message.channel.id

        # First, ensure the message is stored in the database regardless of Slack status
        try:
            # Store message in database with sentiment analysis
            store_result = store_discord_message(
                str(message.id),
                str(channel_id),
                message.content,
                analysis["category"],
                analysis["confidence"],
                rag_response
            )
            if store_result:
                print(f"✅ Successfully stored Discord message {message.id} in database")
            else:
                print(f"⚠️ Failed to store Discord message {message.id} in database")
        except Exception as db_err:
            print(f"⚠️ Error storing Discord message in database: {db_err}")

        # Then try to send to Slack for approval
        try:
            # Send the response for approval to Slack
            thread_ts = send_to_slack(analysis["text"], rag_response, "discord", message.id, channel_id)
            
            if thread_ts:
                print(f"✅ Successfully sent to Slack for approval: {message.id}")
            else:
                print(f"⚠️ Failed to send to Slack for approval: {message.id}")
        except Exception as slack_err:
            print(f"⚠️ Error sending to Slack: {slack_err}")

        # Notify user in Discord
        await message.channel.send(
            f"Response is awaiting approval. (Category: {analysis['category']} at {analysis['confidence']:.2f}%)"
        )

# Replace with your token or environment variable
bot.run(DISCORD_BOT_TOKEN)