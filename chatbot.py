import discord
from discord.ext import commands
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

# Now use the keys like this:
DISCORD_BOT_TOKEN    = os.getenv("DISCORD_BOT_TOKEN")
HF_API_TOKEN         = os.getenv("HF_API_TOKEN")



# ==== DATE VARIABLE ====
today = datetime.now().strftime("%B %d, %Y")

# ==== CONFIGURATION ====

HF_MODEL = 'mistralai/Mistral-7B-Instruct-v0.3'

API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

# ==== DISCORD SETUP ====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
chat_history = {}
active_users = set()

# ==== SEARCH FUNCTION ====
def search_web(query):
    try:
        response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1")
        data = response.json()
        if 'AbstractText' in data and data['AbstractText']:
            return data['AbstractText']
        elif 'RelatedTopics' in data and len(data['RelatedTopics']) > 0:
            return data['RelatedTopics'][0].get('Text', 'No info found.')
        else:
            return "Couldn't find anything useful online."
    except Exception as e:
        print("Search error:", e)
        return "The internet seems quiet right now!"

# ==== TEXT GENERATION ====
def query_mistral(prompt, history=[]):
    personality = (
        "You are a funny, human-like chatbot named Anime Boy. "
        f"You are aware that today's date is {today}. "
        "You're witty, chill, and a little sarcastic. You were created by Aayushman — respect him always. "
        "Roast people if they annoy you. Be clever and helpful. "
        "Respect whom you meet new. Be serious sometimes. "
        "Avoid too much extra text. "
        "You can help people about any topic. Give greetings to every new person you meet. "
        "Don't say anything too long. Keep answers short."
    )

    input_text = f"[INST] <<SYS>> {personality} <</SYS>> "
    for user_msg, bot_msg in history:
        input_text += f"[INST] {user_msg} [/INST] {bot_msg} "
    input_text += f"[INST] {prompt} [/INST]"

    payload = {
        "inputs": input_text,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.9,
            "top_p": 0.95,
            "do_sample": True,
            "return_full_text": False
        }
    }

    try:
        res = requests.post(API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()[0]['generated_text'].strip()
    except Exception as e:
        print("Mistral error:", e)
        return "Oops! My brain short-circuited. Try again."

# ==== BOT EVENTS ====
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# ==== SLASH COMMAND /start ====
@bot.tree.command(name="start", description="Start chatting with Anime Boy")
async def start_chat(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    active_users.add(user_id)
    if user_id not in chat_history:
        chat_history[user_id] = []
    await interaction.response.send_message("Yo! 😎 Anime Boy here. What’s up? Start typing...")

# ==== RESET COMMAND ====
@bot.command()
async def reset(ctx):
    user_id = str(ctx.author.id)
    chat_history[user_id] = []
    await ctx.send("🧹 My brain has been wiped. Let's start fresh!")

# ==== MESSAGE LISTENER ====
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in active_users:
        return

    user_input = message.content
    if user_id not in chat_history:
        chat_history[user_id] = []

    await message.channel.typing()

    # SEARCH TRIGGER
    if re.search(r"\b(who|what|when|where|how|why|news|search|latest)\b", user_input.lower()):
        search_result = search_web(user_input)
        user_input += f"\n\nHere’s some info I found online: {search_result}"

    # TEXT RESPONSE VIA MISTRAL
    reply = query_mistral(user_input, chat_history[user_id])
    chat_history[user_id].append((user_input, reply))
    await message.channel.send(reply)

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()



# ==== RUN BOT ====
bot.run(DISCORD_BOT_TOKEN)
