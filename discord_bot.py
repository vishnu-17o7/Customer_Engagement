import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import discord
from relevance_checker import analyze_text
from rag_integration import generate_rag_response, send_to_slack
from slack_approval import pending_responses

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

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

        # Send the response for approval to Slack.
        send_to_slack(analysis["text"], rag_response, "discord", message.id, channel_id)
        
        # Store the pending response
        pending_responses[str(message.id)] = (message.id, channel_id, "discord", rag_response)
        
        await message.channel.send(
            f"Response is awaiting approval. (Category: {analysis['category']} at {analysis['confidence']:.2f}%)"
        )
        

bot.run("MTM0MzE3MDc4NjMxMTI3NDU4OA.GUBBir.yxwDhI2h2cQp5Lai_rAj8QBWP9tt7yk-1MFUu8")
