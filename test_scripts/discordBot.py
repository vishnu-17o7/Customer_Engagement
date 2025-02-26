import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import discord
import re
import spacy
from transformers import pipeline
import torch
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Check if GPU is available and set device accordingly
device = 0 if torch.cuda.is_available() else -1

# Load BERT-based intent classifier with GPU support if available
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)

# Define relevant keywords
company_keywords = ["YourCompanyName", "YourProduct", "YourService", "CompetitorName", "IndustryKeyword"]

# Define possible intents
intent_labels = ["question", "complaint", "feedback", "general discussion"]

# Function to check for keywords
def contains_keywords(text):
    return any(re.search(rf"\b{keyword}\b", text, re.IGNORECASE) for keyword in company_keywords)

# Function to detect intent using BERT
def detect_intent(text):
    result = classifier(text, intent_labels)
    return result["labels"][0]  # Get the most likely intent

# Discord Bot Setup
intents = discord.Intents.default()
intents.messages = True  # Enable message reading
intents.message_content = True 
intents.guilds = True
 # Required for reading messages

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author == bot.user:
        return

    text = message.content

    # Check if message is relevant
    if contains_keywords(text):
        intent = detect_intent(text)
        print(f"Relevant Message Found: \nUser: {message.author} \nMessage: {text} \nIntent: {intent} \n")

# Run the bot
bot.run(DISCORD_BOT_TOKEN)
