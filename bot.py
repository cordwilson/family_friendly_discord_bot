import random
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands
import requests

SAVINGS_GOAL = 1000.0

JOKES = [
    "There no such thing a fully committed Jew. Most of them are only Jew-ish",
    "How heavy is a Jew? Chances are he Israelite",
    "A new PC was promised to Elijah 3000 years ago",
    "Where do pessimistic Jews go to worship? A cynicgogue",
    "Why are jews circumcised? Because its not kosher to mix cheese with meat",
    "The power of Epstein has compelled you!",
    "What is the opposite of a wandering Jew? A Roamin’ Catholic",
    "Why didn't the Jew pay for his coffee? Because Hebrew it himself",
    "How many Jews are at a Catholic school? Just one",
    "Why are circumsized penises so popular among Jewish girls? They love anything that's 15% off",
    "Why was the Jewish Jedi lonely? Because he had no Force Kin",
    "6 gonzillion and counting!",
    "I met a Jewish girl and she asked for my number. I told her we use names here"
]

GOAL_IDEAS = []

# 1. Background Health Check HTTP Server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# 2. Discord Bot Configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}!")

# Custom !help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="Jewbot Help Menu",
        description="Available commands:",
        color=discord.Color.gold()
    )
    embed.add_field(name="`!deposit <amount>`", value="Log a deposit into the group savings.", inline=False)
    embed.add_field(name="`!withdraw <amount>`", value="Log a withdrawal/adjustment from your total.", inline=False)
    embed.add_field(name="`!balance`", value="View individual balances and the total bank total.", inline=False)
    embed.add_field(name="`!leaderboard`", value="Show the top savers ranked by contribution.", inline=False)
    embed.add_field(name="`!goal`", value="Show progress toward current cash goal.", inline=False)
    embed.add_field(name="`!setgoal <amount>`", value="Set current cash goal.", inline=False)
    embed.add_field(name="`!ideas`", value="View wishlist items to spend savings on.", inline=False)
    embed.add_field(name="`!poll \"Topic\" \"Opt 1\" \"Opt 2\"`", value="Create a poll.", inline=False)
    embed.add_field(name="`!help`", value="Show this menu.", inline=False)
    embed.set_footer(text="CocknbaweTreasury")
    await ctx.send(embed=embed)

@bot.command()
async def deposit(ctx, amount: float):
    if amount <= 0:
        await ctx.send("❌ Deposit amount must be greater than $0.")
        return
    payload = {"action": "deposit", "user": str(ctx.author.display_name), "amount": amount}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if res.status_code == 200:
            await ctx.send(f"💰 **${amount:.2f}** logged for {ctx.author.mention}!")
        else:
            await ctx.send("⚠️ Received unexpected status from Google Sheets.")
    except requests.exceptions.Timeout:
        await ctx.send("⚠️ Google Sheets request timed out. Please try again.")
    except Exception as e:
        await ctx.send(f"❌ Error logging deposit: {e}")

@bot.command()
async def balance(ctx):
    payload = {"action": "balance"}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            msg = f"📊 **Concknbawe Savings Total: ${data.get('total', 0.0):.2f}**\n"
            for user, amt in data.get("users", {}).items():
                msg += f"• **{user}**: ${amt:.2f}\n"
            await ctx.send(msg)
        else:
            await ctx.send("⚠️ Unable to fetch balance from Google Sheets.")
    except requests.exceptions.Timeout:
        await ctx.send("⚠️ Google Sheets request timed out. Please try again.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching balance: {e}")

@bot.command()
async def leaderboard(ctx):
    payload = {"action": "balance"}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            sorted_users = sorted(data.get("users", {}).items(), key=lambda x: x[1], reverse=True)
            
            msg = "🏆 **Savings Leaderboard** 🏆\n"
            medals = ["🥇", "🥈", "🥉"]
            for idx, (user, amt) in enumerate(sorted_users):
                prefix = medals[idx] if idx < len(medals) else "•"
                msg += f"{prefix} **{user}**: ${amt:.2f}\n"
            await ctx.send(msg)
        else:
            await ctx.send("⚠️ Unable to fetch leaderboard from Google Sheets.")
    except requests.exceptions.Timeout:
        await ctx.send("⚠️ Google Sheets request timed out. Please try again.")
    except Exception as e:
        await ctx.send(f"❌ Error fetching leaderboard: {e}")

@bot.command()
async def joke(ctx):
    selected_joke = random.choice(JOKES)
    await ctx.send(f"{selected_joke}")

@bot.command()
async def goal(ctx):
    try:
        res = requests.post(WEBHOOK_URL, json={"action": "balance"}, timeout=5)
        if res.status_code == 200:
            total = res.json().get("total", 0.0)
            percent = min(100.0, (total / SAVINGS_GOAL) * 100)
            
            bar_length = 10
            filled = int(round(bar_length * total / float(SAVINGS_GOAL)))
            bar = "█" * filled + "░" * (bar_length - filled)
            
            await ctx.send(
                f"🎯 **Group Savings Goal:**\n"
                f"`[{bar}]` **{percent:.1f}%** (${total:.2f} /${SAVINGS_GOAL:.2f})"
            )
        else:
            await ctx.send("⚠️ Unable to fetch current total for goal calculation.")
    except requests.exceptions.Timeout:
        await ctx.send("⚠️ Google Sheets request timed out.")
    except Exception as e:
        await ctx.send(f"❌ Error checking goal: {e}")

@bot.command()
async def setgoal(ctx, new_goal: float):
    global SAVINGS_GOAL
    if new_goal <= 0:
        await ctx.send("❌ Goal amount must be greater than $0.")
        return
        
    SAVINGS_GOAL = new_goal
    await ctx.send(f"🎯 **New Savings Goal set to ${SAVINGS_GOAL:,.2f}**")

@bot.command()
async def ideas(ctx):
    if not GOAL_IDEAS:
        await ctx.send("💡 No goal ideas added yet.")
        return
    msg = "💡 **Concknbawe Savings Wishlist:**\n"
    for idx, idea in enumerate(GOAL_IDEAS, start=1):
        msg += f"{idx}. {idea}\n"
    await ctx.send(msg)
    
@bot.command()
async def poll(ctx, question: str, *options: str):
    if len(options) < 2:
        await ctx.send("❌ Please provide at least 2 options! Usage: `!poll \"Question\" \"Opt 1\" \"Opt 2\"`")
        return
    if len(options) > 10:
        await ctx.send("❌ Polls are limited to a maximum of 10 options.")
        return

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    description = [f"{emojis[idx]} {opt}" for idx, opt in enumerate(options)]
    
    embed = discord.Embed(
        title=f"📊 {question}",
        description="\n".join(description),
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Poll created by {ctx.author.display_name}")
    
    poll_msg = await ctx.send(embed=embed)
    for idx in range(len(options)):
        await poll_msg.add_reaction(emojis[idx])

bot.run(DISCORD_TOKEN)
