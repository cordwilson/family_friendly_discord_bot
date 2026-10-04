import os
import discord
from discord.ext import commands
import requests

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}! Concknbawe bot is online.")

@bot.command()
async def deposit(ctx, amount: float):
    """Logs a deposit: !deposit 25"""
    payload = {
        "action": "deposit",
        "user": str(ctx.author.display_name),
        "amount": amount
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            await ctx.send(f"💰 **${amount:.2f}** logged for {ctx.author.mention}!")
        else:
            await ctx.send("❌ Error: Could not log deposit to Google Sheets.")
    except Exception as e:
        await ctx.send(f"❌ Error communicating with backend: {e}")

@bot.command()
async def balance(ctx):
    """Displays overall total and user breakdown: !balance"""
    payload = {"action": "balance"}
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            data = response.json()
            total = data["total"]
            users = data["users"]
            
            msg = f"📊 **Concknbawe Savings Total: ${total:.2f}**\n"
            msg += "───────────────────────────\n"
            for user, amt in users.items():
                msg += f"• **{user}**: ${amt:.2f}\n"
                
            await ctx.send(msg)
        else:
            await ctx.send("❌ Error: Could not retrieve balance from Google Sheets.")
    except Exception as e:
        await ctx.send(f"❌ Error communicating with backend: {e}")

bot.run(DISCORD_TOKEN)