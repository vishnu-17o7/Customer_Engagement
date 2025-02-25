#### filepath: /c:/Users/vishn/Desktop/Programs/Customer_Engagement/discord_bot.py
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import discord
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
# We only rely on the shared pending_responses in slack_approval
# from slack_approval import pending_responses  
from dotenv import load_dotenv
import os
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    analysis = analyze_text(message.content)
    
    if analysis["relevant"]:
        rag_response = generate_rag_response(analysis["text"], message.content)

        # Get channel ID
        channel_id = message.channel.id

        # Send the response for approval to Slack (and store in shared pending_responses there)
        send_to_slack(analysis["text"], rag_response, "discord", message.id, channel_id)

        await message.channel.send(
            f"Response is awaiting approval. (Category: {analysis['category']} at {analysis['confidence']:.2f}%)"
        )

# Replace with your token or environment variable
bot.run(DISCORD_BOT_TOKEN)