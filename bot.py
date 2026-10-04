import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
import requests

# 1. Tiny HTTP server to satisfy Render's Web Service requirement
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Start the web server in a background thread
threading.Thread(target=run_web_server, daemon=True).start()

# 2. Discord Bot Logic
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}!")

@bot.command()
async def deposit(ctx, amount: float):
    payload = {"action": "deposit", "user": str(ctx.author.display_name), "amount": amount}
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 200:
        await ctx.send(f"💰 **${amount:.2f}** logged for {ctx.author.mention}!")

@bot.command()
async def balance(ctx):
    payload = {"action": "balance"}
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 200:
        data = res.json()
        msg = f"📊 **Concknbawe Savings Total: ${data['total']:.2f}**\n"
        for user, amt in data["users"].items():
            msg += f"• **{user}**: ${amt:.2f}\n"
        await ctx.send(msg)

bot.run(DISCORD_TOKEN)
