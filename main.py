# main.py — All-in-one Discord bot (prefix !, moderation, AI-like replies)
# Requirements: discord.py, flask
# Put your bot token into Replit Secrets as DISCORD_TOKEN
# Optional Secrets: MONTH_CHANNEL_ID, WELCOME_CHANNEL_ID, LOG_CHANNEL_ID, MONTHLY_TEXT

# -------- KEEP ALIVE SERVER (Replit) --------
from flask import Flask
from threading import Thread
import os
import json
import random
import asyncio
from datetime import datetime

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -------- DISCORD BOT SETUP --------
import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

PREFIX = "!"
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

CUSTOM_CMDS_FILE = "custom_cmds.json"
LOG_FILE = "bot.log"

# Create file if missing
if not os.path.exists(CUSTOM_CMDS_FILE):
    with open(CUSTOM_CMDS_FILE, "w") as f:
        json.dump({}, f)

def load_custom_cmds():
    with open(CUSTOM_CMDS_FILE, "r") as f:
        return json.load(f)

def save_custom_cmds(data):
    with open(CUSTOM_CMDS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Logging
async def write_log(bot, message):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts} UTC] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)

    log_channel_id = os.getenv("LOG_CHANNEL_ID")
    if log_channel_id and bot.is_ready():
        ch = bot.get_channel(int(log_channel_id))
        if ch:
            try:
                await ch.send(f"```\n{line}```")
            except:
                pass

# Monthly Message
MONTH_CHANNEL_ID = os.getenv("MONTH_CHANNEL_ID")
MONTHLY_TEXT = os.getenv("MONTHLY_TEXT", "This is your automatic monthly message!")

@tasks.loop(hours=720)
async def monthly_announce():
    if MONTH_CHANNEL_ID:
        try:
            ch = bot.get_channel(int(MONTH_CHANNEL_ID))
            if ch:
                await ch.send(MONTHLY_TEXT)
                await write_log(bot, f"Sent monthly message to {ch.id}")
        except Exception as e:
            await write_log(bot, f"Monthly announce error: {e}")

# ------------------ EVENTS ------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await write_log(bot, f"Bot started as {bot.user}")

    if not monthly_announce.is_running():
        monthly_announce.start()

@bot.event
async def on_member_join(member):
    welcome_channel = os.getenv("WELCOME_CHANNEL_ID")
    if welcome_channel:
        ch = bot.get_channel(int(welcome_channel))
        if ch:
            await ch.send(f"Welcome {member.mention}! 🎉")
            await write_log(bot, f"Welcomed {member} in {ch.id}")

# ------------- AI-LIKE SMALL TALK ------------
SMALL_TALK = {
    ("hi","hello","hey","hola"): [
        "Hey there! 👋",
        "Hello! How are you today?",
        "Hi! Need anything?"
    ],
    ("how are you","how r you","how ru"): [
        "I'm always great! Thanks for asking 😊",
        "Doing awesome! What about you?",
    ],
    ("bye","goodbye","see ya"): [
        "Bye! Come back soon 👋",
        "See you later!",
    ]
}

def ai_like_reply(text):
    t = text.lower()
    for keys, responses in SMALL_TALK.items():
        for k in keys:
            if k in t:
                return random.choice(responses)
    fallback = [
        "Interesting... tell me more.",
        "Haha nice!",
        "Need help? Type !help"
    ]
    if random.random() < 0.08:
        return random.choice(fallback)
    return None

# ------------------ COMMANDS ------------------

@bot.command(name="help")
async def help_cmd(ctx):
    help_text = (
        f"**Bot Commands (prefix: {PREFIX})**\n"
        "`!help` - show this message\n"
        "`!ping` - bot ping\n"
        "`!hello` - greet\n"
        "`!joke` `!fact` `!coinflip` `!roll` `!8ball` - fun commands\n"
        "`!serverinfo` `!userinfo` `!avatar` - info\n"
        "`!addcmd <name> <msg>` `!delcmd <name>` `!listcmds` - custom commands\n"
        "`!kick` `!ban` `!clear` `!slowmode` `!mute` `!unmute` - moderation"
    )
    await ctx.send(help_text)

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}! 👋")

@bot.command()
async def joke(ctx):
    jokes = [
        "Why don't skeletons fight each other? They don't have the guts!",
        "I'm reading a book about anti-gravity — it's impossible to put down!",
        "Why was the math book sad? Too many problems!"
    ]
    await ctx.send(random.choice(jokes))

@bot.command()
async def fact(ctx):
    facts = [
        "Honey never spoils.",
        "Octopuses have 3 hearts.",
        "Bananas are berries, strawberries aren't!"
    ]
    await ctx.send(random.choice(facts))

@bot.command()
async def coinflip(ctx):
    await ctx.send(random.choice(["Heads 👍", "Tails 👎"]))

@bot.command()
async def roll(ctx):
    await ctx.send(f"🎲 You rolled **{random.randint(1,6)}**")

@bot.command(name="8ball")
async def eightball(ctx, *, question=None):
    if not question:
        await ctx.send("Example: `!8ball Will I be rich?`")
        return
    responses = ["Yes", "No", "Maybe", "Absolutely!", "No chance!", "Ask again later."]
    await ctx.send(random.choice(responses))

@bot.command()
async def love(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("Usage: !love @user")
        return
    percent = random.randint(1,100)
    await ctx.send(f"❤️ Love between {ctx.author.mention} and {member.mention}: **{percent}%**")

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    await ctx.send(
        f"**Server:** {g.name}\n"
        f"**Members:** {g.member_count}\n"
        f"**Owner:** {g.owner}\n"
        f"**Created:** {g.created_at.strftime('%Y-%m-%d')}"
    )

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(
        f"**User:** {member}\n"
        f"**ID:** {member.id}\n"
        f"**Joined:** {member.joined_at.strftime('%Y-%m-%d')}\n"
        f"**Created:** {member.created_at.strftime('%Y-%m-%d')}"
    )

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.avatar.url)

# ---------------- CUSTOM COMMANDS ----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def addcmd(ctx, name: str, *, text: str):
    cmds = load_custom_cmds()
    cmds[name.lower()] = text
    save_custom_cmds(cmds)
    await ctx.send(f"Added custom command: `!{name}`")

@bot.command()
async def listcmds(ctx):
    cmds = load_custom_cmds()
    if not cmds:
        await ctx.send("No custom commands added.")
        return
    await ctx.send("Commands: " + ", ".join(f"`!{c}`" for c in cmds))

@bot.command()
@commands.has_permissions(administrator=True)
async def delcmd(ctx, name: str):
    cmds = load_custom_cmds()
    if name.lower() in cmds:
        del cmds[name.lower()]
        save_custom_cmds(cmds)
        await ctx.send(f"Deleted `!{name}`")
    else:
        await ctx.send("Command not found.")

# ---------------- MODERATION ----------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Usage: !kick @user")
    await member.kick()
    await ctx.send(f"Kicked {member}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Usage: !ban @user")
    await member.ban()
    await ctx.send(f"Banned {member}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Deleted {len(deleted)-1} messages.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slowmode set to {seconds} seconds.")

async def ensure_muted_role(guild):
    role = discord.utils.get(guild.roles, name="Muted")
    if role:
        return role
    role = await guild.create_role(name="Muted", permissions=discord.Permissions(send_messages=False))
    for ch in guild.channels:
        try:
            await ch.set_permissions(role, send_messages=False)
        except:
            pass
    return role

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Usage: !mute @user")
    role = await ensure_muted_role(ctx.guild)
    await member.add_roles(role)
    await ctx.send(f"Muted {member}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Usage: !unmute @user")
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Unmuted {member}")
    else:
        await ctx.send("That user is not muted.")

# ----------- CUSTOM COMMAND TRIGGER -----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # normal commands
    await bot.process_commands(message)

    # custom commands
    if message.content.startswith(PREFIX):
        cmd = message.content[len(PREFIX):].split()[0].lower()
        cmds = load_custom_cmds()
        if cmd in cmds:
            await message.channel.send(cmds[cmd])
            return

    # AI talk
    reply = ai_like_reply(message.content)
    if reply:
        await message.channel.send(reply)

# ----------- BOT STARTUP -----------
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN missing in Secrets.")
    else:
        bot.run(TOKEN)
