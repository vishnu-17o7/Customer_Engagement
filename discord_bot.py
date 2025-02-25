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
        
        # Send the response for approval to Slack.
        send_to_slack(analysis["text"], rag_response, "discord", message.id)
        
        # Store the pending response (using message.id as a key here for demonstration;
        # in a real implementation, you might use the Slack thread timestamp returned from the webhook).
        pending_responses[str(message.id)] = (message.id, "discord", rag_response)
        
        await message.channel.send(f"Response is awaiting approval. (Category: {analysis['category']} at {analysis['confidence']:.2f}%)")

bot.run("MTM0MzE3MDc4NjMxMTI3NDU4OA.GUBBir.yxwDhI2h2cQp5Lai_rAj8QBWP9tt7yk-1MFUu8")
