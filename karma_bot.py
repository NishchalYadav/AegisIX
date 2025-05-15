import os
import json
import asyncio  # Add this import
from datetime import datetime, timedelta
import random
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram import Update, ChatMember
from dotenv import load_dotenv
import re
from random import choice
import aiohttp
from urllib.parse import quote

# Load environment variables
load_dotenv()

# Initialize data storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
KARMA_FILE = os.path.join(DATA_DIR, 'karma.json')
COOLDOWN_FILE = os.path.join(DATA_DIR, 'cooldowns.json')
FILTERS_FILE = os.path.join(DATA_DIR, 'filters.json')
SHIPPING_FILE = os.path.join(DATA_DIR, 'shipping.json')

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Product/Status definitions
PRODUCTS = {
    "P001": {"name": "🌠 Supreme Overlord", "price": 50000, "rank": 20},
    "P002": {"name": "👑 Grand Emperor", "price": 45000, "rank": 19},
    "P003": {"name": "⚜️ Royal Sovereign", "price": 40000, "rank": 18},
    "P004": {"name": "🔱 Divine Master", "price": 35000, "rank": 17},
    "P005": {"name": "💫 Celestial Lord", "price": 30000, "rank": 16},
    "P006": {"name": "⚡ Thunder God", "price": 25000, "rank": 15},
    "P007": {"name": "🌟 Astral King", "price": 20000, "rank": 14},
    "P008": {"name": "🎯 Elite Champion", "price": 15000, "rank": 13},
    "P009": {"name": "🔮 Mystic Sage", "price": 12000, "rank": 12},
    "P010": {"name": "🌈 Rainbow Master", "price": 10000, "rank": 11},
    "P011": {"name": "⚔️ War Chief", "price": 8000, "rank": 10},
    "P012": {"name": "🛡️ Royal Guard", "price": 6000, "rank": 9},
    "P013": {"name": "⚡ Alpha Elite", "price": 5000, "rank": 8},
    "P014": {"name": "🌟 Sigma Prime", "price": 4000, "rank": 7},
    "P015": {"name": "💫 Beta Supreme", "price": 3000, "rank": 6},
    "P016": {"name": "✨ Omega Plus", "price": 2000, "rank": 5},
    "P017": {"name": "🌙 Nova Star", "price": 1500, "rank": 4},
    "P018": {"name": "💎 Crystal Knight", "price": 1000, "rank": 3},
    "P019": {"name": "🎭 Shadow Agent", "price": 500, "rank": 2},
    "P020": {"name": "🌱 Rising Star", "price": 250, "rank": 1}
}

WELCOME_MESSAGES = [
    "🎉 Holy moly! {user} just crash-landed into our group! Quick, hide the memes!",
    "👋 Whoosh! {user} just ninja'd their way in here! Everyone act natural!",
    "🌟 Alert! Alert! {user} has infiltrated our secret hideout!",
    "🎪 Ladies and gentlemen! Please welcome our newest clown, {user}!",
    "🚀 {user} has entered the chat! This is not a drill, I repeat, NOT A DRILL!",
    "💫 Look what the cat dragged in! It's {user}!",
    "🎭 Plot twist! {user} just joined our chaos party!",
    "🌈 *Poof* {user} appeared! Please don't be a bot... please don't be a bot...",
    "🎪 Breaking news: {user} has discovered our secret society!",
    "🎯 {user} has spawned in the chat! Quick, give them the initiation test!"
]

# Truth, Dare and NHIE data
TRUTH_QUESTIONS = [
    "What's the most embarrassing song on your playlist?",
    "What's the longest you've gone without showering?",
    "What's your biggest fear?",
    "What's your worst habit?",
    "What's the last lie you told?",
    "What's your biggest insecurity?",
    "What's the most childish thing you still do?",
    "What's your biggest regret?",
    "What's the worst thing you've ever done?",
    "What's your most controversial opinion?"
]

DARE_CHALLENGES = [
    "Send your last 5 photos from your gallery",
    "Send a voice message singing your favorite song",
    "Change your profile picture to a meme for 1 hour",
    "Text your crush 'I love pineapple on pizza'",
    "Send a selfie with a funny face",
    "Write a poem about the person above",
    "Tell a joke in a voice message",
    "Send your battery percentage",
    "Type like a robot for the next 10 minutes",
    "Share your most used emoji"
]

NHIE_QUESTIONS = [
    "Never have I ever sent a text to the wrong person",
    "Never have I ever pretended to be sick to skip work/school",
    "Never have I ever gone a whole day without using my phone",
    "Never have I ever stolen something",
    "Never have I ever lied about my age",
    "Never have I ever ghosted someone",
    "Never have I ever fallen asleep during a movie",
    "Never have I ever stalked an ex on social media",
    "Never have I ever forgotten someone's name while talking to them",
    "Never have I ever accidentally liked an old post while stalking"
]

# Owner check function
def is_owner(user_id: str) -> bool:
    owner_id = os.getenv('BOT_OWNER_ID')
    return str(user_id) == owner_id

# Data management functions
def load_data():
    try:
        with open(KARMA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": {}, "purchases": {}}
        save_data(data)
        return data

def save_data(data):
    with open(KARMA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_cooldowns():
    try:
        with open(COOLDOWN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_cooldowns(cooldowns):
    with open(COOLDOWN_FILE, 'w', encoding='utf-8') as f:
        json.dump(cooldowns, f, indent=2, ensure_ascii=False)

def load_filters():
    try:
        with open(FILTERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"groups": {}}

def save_filters(data):
    with open(FILTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_shipping():
    try:
        with open(SHIPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_ship": {}, "couples": {}}

def save_shipping(data):
    with open(SHIPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Command handlers
async def rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or str(user_id)
    
    data = load_data()
    cooldowns = load_cooldowns()
    
    # Owner gets unlimited karma
    if is_owner(user_id):
        if user_id not in data["users"]:
            data["users"][user_id] = {"karma": 0, "username": username}
        data["users"][user_id]["karma"] = 999999  # Set unlimited karma for owner
        save_data(data)
        await update.message.reply_text(
            "👑 *Owner Karma Refreshed*\n"
            "You now have unlimited karma points!", 
            parse_mode='Markdown'
        )
        return

    # Check cooldown
    if user_id in cooldowns:
        last_claim = datetime.fromisoformat(cooldowns[user_id])
        if datetime.now() < last_claim + timedelta(days=1):
            time_left = (last_claim + timedelta(days=1) - datetime.now())
            hours = int(time_left.total_seconds() / 3600)
            minutes = int((time_left.total_seconds() % 3600) / 60)
            await update.message.reply_text(
                f"⏳ You can claim rewards again in {hours}h {minutes}m"
            )
            return

    # Generate karma
    karma = random.randint(1, 300)
    
    # Update user data
    if user_id not in data["users"]:
        data["users"][user_id] = {"karma": 0, "username": username}
    
    data["users"][user_id]["karma"] += karma
    cooldowns[user_id] = datetime.now().isoformat()
    
    save_data(data)
    save_cooldowns(cooldowns)
    
    await update.message.reply_text(
        f"🎉 You received {karma} karma points!\n"
        f"Current balance: {data['users'][user_id]['karma']} points"
    )

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) != 2:
        await update.message.reply_text(
            "❌ Usage: /give @username amount"
        )
        return

    sender_id = str(update.effective_user.id)
    target_username = context.args[0].replace("@", "")
    
    try:
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Please specify a valid amount")
        return

    data = load_data()
    
    # Check if sender has enough karma
    if sender_id not in data["users"]:
        await update.message.reply_text("❌ You don't have any karma points")
        return
    
    if not is_owner(sender_id) and data["users"][sender_id]["karma"] < amount:
        await update.message.reply_text("❌ Insufficient karma points")
        return

    # Find target user by username
    target_id = None
    for uid, user_data in data["users"].items():
        if user_data.get("username") == target_username:
            target_id = uid
            break

    if not target_id:
        await update.message.reply_text("❌ User not found")
        return

    # Process transfer
    if not is_owner(sender_id):
        data["users"][sender_id]["karma"] -= amount
    data["users"][target_id]["karma"] = data["users"][target_id].get("karma", 0) + amount

    save_data(data)
    
    await update.message.reply_text(
        f"✅ Successfully sent {amount} karma to @{target_username}\n" +
        (f"Your new balance: {data['users'][sender_id]['karma']}" if not is_owner(sender_id) else "")
    )

async def store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_text = "*🏪 ═══ Karma Store ═══*\n\n"
    
    # Group products by tier
    tiers = {
        "🔥 *LEGENDARY TIER*": range(17, 21),
        "💫 *EPIC TIER*": range(13, 17),
        "✨ *RARE TIER*": range(9, 13),
        "🌟 *UNCOMMON TIER*": range(5, 9),
        "🌱 *STARTER TIER*": range(1, 5)
    }
    
    for tier_name, tier_range in tiers.items():
        store_text += f"\n{tier_name}\n"
        store_text += "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
        
        # Filter products for this tier
        tier_products = {k: v for k, v in PRODUCTS.items() 
                        if v["rank"] in tier_range}
        
        for pid, product in tier_products.items():
            store_text += f"• {product['name']}\n"
            store_text += f"  💰 Price: {product['price']:,} karma\n"
            store_text += f"  🔑 PID: `{pid}`\n\n"
    
    store_text += "\n*How to purchase:*\n"
    store_text += "Use command: `/buy PID`"
    
    await update.message.reply_text(store_text, parse_mode='Markdown')

# Update the buy function
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if not context.args:
        await update.message.reply_text("❌ Please specify a Product ID (PID)")
        return

    pid = context.args[0].upper()
    if pid not in PRODUCTS:
        await update.message.reply_text("❌ Invalid Product ID")
        return

    data = load_data()
    
    if user_id not in data["users"]:
        data["users"][user_id] = {"karma": 0, "username": update.effective_user.username or str(user_id)}
        save_data(data)

    product = PRODUCTS[pid]
    user_karma = data["users"][user_id]["karma"]

    # Skip karma check for owner
    if not is_owner(user_id) and user_karma < product["price"]:
        needed = product["price"] - user_karma
        await update.message.reply_text(
            f"❌ Insufficient karma points\n"
            f"You need {needed:,} more points"
        )
        return

    # Check for existing purchase
    if user_id in data["purchases"] and pid in data["purchases"][user_id]:
        await update.message.reply_text("❌ You already own this status")
        return

    # Process purchase (don't deduct karma for owner)
    if not is_owner(user_id):
        data["users"][user_id]["karma"] -= product["price"]
    
    if user_id not in data["purchases"]:
        data["purchases"][user_id] = {}
    data["purchases"][user_id][pid] = datetime.now().isoformat()
    
    save_data(data)
    
    await update.message.reply_text(
        f"✅ Successfully purchased {product['name']}\n" +
        (f"Remaining karma: {data['users'][user_id]['karma']:,}" if not is_owner(user_id) else "")
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    
    # Calculate user scores
    user_scores = []
    for user_id, purchases in data.get("purchases", {}).items():
        total_rank = sum(PRODUCTS[pid]["rank"] for pid in purchases)
        username = data["users"][user_id]["username"]
        statuses = [PRODUCTS[pid]["name"] for pid in purchases]
        user_scores.append((username, total_rank, statuses))

    # Sort by rank
    user_scores.sort(key=lambda x: x[1], reverse=True)
    
    if not user_scores:
        await update.message.reply_text("No purchases yet!")
        return

    # Format leaderboard
    lb_text = "*🏆 Status Leaderboard*\n\n"
    for i, (username, score, statuses) in enumerate(user_scores[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        lb_text += f"{medal} @{username}\n"
        lb_text += f"Statuses: {' '.join(statuses)}\n\n"

    await update.message.reply_text(lb_text, parse_mode='Markdown')

# Add after other command handlers
async def check_karma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    
    # Check if a username is provided
    if context.args:
        target_username = context.args[0].replace("@", "")
        # Find user by username
        target_id = None
        for uid, user_data in data["users"].items():
            if user_data.get("username") == target_username:
                target_id = uid
                break
        
        if not target_id:
            await update.message.reply_text("❌ User not found")
            return
            
        user_data = data["users"][target_id]
        karma = user_data["karma"]
        
        # Get user's statuses
        statuses = []
        if target_id in data.get("purchases", {}):
            statuses = [PRODUCTS[pid]["name"] for pid in data["purchases"][target_id]]
        
        # Format response
        response = (
            f"👤 *User:* @{target_username}\n"
            f"💰 *Karma Points:* {karma:,}\n"
        )
        
        if statuses:
            response += f"🏆 *Owned Statuses:*\n{' '.join(statuses)}"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    else:
        # Show karma for command user
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or str(user_id)
        
        if user_id not in data["users"]:
            data["users"][user_id] = {"karma": 0, "username": username}
            save_data(data)
        
        karma = data["users"][user_id]["karma"]
        
        # Get user's statuses
        statuses = []
        if user_id in data.get("purchases", {}):
            statuses = [PRODUCTS[pid]["name"] for pid in data["purchases"][user_id]]
        
        # Format response
        response = (
            f"👤 *Your Karma Stats*\n"
            f"💰 *Current Balance:* {karma:,} points\n"
        )
        
        if statuses:
            response += f"🏆 *Your Statuses:*\n{' '.join(statuses)}"
        else:
            response += "\n💫 *Tip:* Use `/store` to see available statuses!"
        
        await update.message.reply_text(response, parse_mode='Markdown')

# Add after the existing imports
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get target user (either replied to or command sender)
        if update.message.reply_to_message:
            user = update.message.reply_to_message.from_user
            member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        else:
            user = update.effective_user
            member = await context.bot.get_chat_member(update.effective_chat.id, user.id)

        # Get chat member status
        status_emoji = {
            'creator': '👑 Creator',
            'administrator': '⚜️ Admin',
            'member': '👤 Member',
            'restricted': '⚠️ Restricted',
            'left': '🚶 Left',
            'kicked': '🚫 Banned'
        }

        # Get karma data
        data = load_data()
        karma = data["users"].get(str(user.id), {}).get("karma", 0)
        
        # Get user's statuses
        statuses = []
        if str(user.id) in data.get("purchases", {}):
            statuses = [PRODUCTS[pid]["name"] for pid in data["purchases"][str(user.id)]]

        # Format join date
        joined_date = datetime.fromtimestamp(user.id >> 22).strftime('%B %d, %Y')
        
        # Create detailed info message
        info = [
            f"*👤 User Information*",
            f"┌ *Name:* {user.first_name}",
            f"├ *Username:* @{user.username}" if user.username else "├ *Username:* None",
            f"├ *User ID:* `{user.id}`",
            f"├ *Status:* {status_emoji.get(member.status, member.status)}",
            f"├ *Joined Telegram:* {joined_date}",
            f"└ *Language:* {user.language_code or 'Unknown'}"
        ]

        # Add name history if available
        if hasattr(user, 'first_name_history'):
            names = "\n".join(f"  • {name}" for name in user.first_name_history)
            info.append("\n*🔄 Name History:*\n" + names)

        # Add karma and status info
        info.extend([
            "\n*💰 Karma Information*",
            f"├ *Balance:* {karma:,} points",
            f"└ *Owned Statuses:* {len(statuses)}"
        ])

        if statuses:
            info.append("\n*🏆 Active Statuses:*")
            info.extend(f"  • {status}" for status in statuses)

        # Add profile flags
        flags = []
        if user.is_premium:
            flags.append("⭐ Telegram Premium")
        if user.is_bot:
            flags.append("🤖 Bot")
        if user.is_verified:
            flags.append("✅ Verified")
        if user.is_support:
            flags.append("💠 Telegram Support")
        
        if flags:
            info.append("\n*🚩 Account Flags:*")
            info.extend(f"  • {flag}" for flag in flags)

        # Send the formatted message
        await update.message.reply_text(
            "\n".join(info),
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching user info: {str(e)}")

async def manage_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can manage filters!")
        return

    chat_id = str(update.effective_chat.id)
    filters_data = load_filters()

    if chat_id not in filters_data["groups"]:
        filters_data["groups"][chat_id] = []

    if not context.args:
        # Show current filters
        if not filters_data["groups"][chat_id]:
            await update.message.reply_text("No filtered words set.\nUse: /filters add <word>")
            return
        
        filter_list = "\n".join(f"• {word}" for word in filters_data["groups"][chat_id])
        await update.message.reply_text(
            f"*Filtered Words:*\n{filter_list}\n\nCommands:\n"
            "/filters add <word>\n"
            "/filters remove <word>",
            parse_mode='Markdown'
        )
        return

    action = context.args[0].lower()
    if len(context.args) < 2:
        await update.message.reply_text("❌ Please specify a word!")
        return

    word = context.args[1].lower()

    if action == "add":
        if word in filters_data["groups"][chat_id]:
            await update.message.reply_text("This word is already filtered!")
            return
        filters_data["groups"][chat_id].append(word)
        save_filters(filters_data)
        await update.message.reply_text(f"✅ Added '{word}' to filtered words")

    elif action == "remove":
        if word not in filters_data["groups"][chat_id]:
            await update.message.reply_text("This word is not in the filter list!")
            return
        filters_data["groups"][chat_id].remove(word)
        save_filters(filters_data)
        await update.message.reply_text(f"✅ Removed '{word}' from filtered words")

async def ship_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    shipping_data = load_shipping()

    # Check cooldown
    if chat_id in shipping_data["last_ship"]:
        last_ship = datetime.fromisoformat(shipping_data["last_ship"][chat_id])
        if datetime.now() < last_ship + timedelta(days=1):
            time_left = (last_ship + timedelta(days=1) - datetime.now())
            hours = int(time_left.total_seconds() / 3600)
            minutes = int((time_left.total_seconds() % 3600) / 60)
            await update.message.reply_text(
                f"⏳ Next shipping in {hours}h {minutes}m"
            )
            return

    try:
        # Get chat members
        members = await context.bot.get_chat_administrators(update.effective_chat.id)
        member_list = []
        for member in members:
            if not member.user.is_bot:
                member_list.append(member.user)

        if len(member_list) < 2:
            await update.message.reply_text("Not enough members for shipping! 💔")
            return

        # Select random couple
        partner1, partner2 = random.sample(member_list, 2)
        
        # Calculate love percentage
        love_percent = random.randint(0, 100)
        
        # Get heart emoji based on percentage
        if love_percent >= 80: heart = "❤️"
        elif love_percent >= 60: heart = "💖"
        elif love_percent >= 40: heart = "💝"
        elif love_percent >= 20: heart = "💓"
        else: heart = "💔"

        # Save shipping data
        shipping_data["last_ship"][chat_id] = datetime.now().isoformat()
        if chat_id not in shipping_data["couples"]:
            shipping_data["couples"][chat_id] = []
        shipping_data["couples"][chat_id].append({
            "couple": [partner1.username or str(partner1.id), 
                      partner2.username or str(partner2.id)],
            "percentage": love_percent,
            "date": datetime.now().isoformat()
        })
        save_shipping(shipping_data)

        # Send shipping message
        await update.message.reply_text(
            f"🎯 *Today's Love Match* 🎯\n\n"
            f"@{partner1.username} + @{partner2.username} = {heart}\n\n"
            f"Love Percentage: {love_percent}%\n\n"
            f"{'Perfect Match! 🎉' if love_percent >= 80 else 'Interesting couple! 🤔'}",
            parse_mode='Markdown'
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error in shipping: {str(e)}")

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        if new_member.is_bot:
            continue

        welcome_msg = choice(WELCOME_MESSAGES).format(
            user=f"@{new_member.username}" if new_member.username else new_member.first_name
        )
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# Add message handler for filtered words
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    filters_data = load_filters()

    if chat_id in filters_data["groups"]:
        message_lower = update.message.text.lower()
        for word in filters_data["groups"][chat_id]:
            if word in message_lower:
                try:
                    await update.message.delete()
                    await update.message.reply_text(
                        f"⚠️ @{update.message.from_user.username} used a filtered word!"
                    )
                except Exception:
                    pass
                break

# Add these new command handlers
async def urban_dict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /urban <word>")
        return
    
    word = " ".join(context.args)
    url = f"https://api.urbandictionary.com/v0/define?term={quote(word)}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["list"]:
                        definition = data["list"][0]
                        message = (
                            f"📚 *{word}*\n\n"
                            f"*Definition:*\n{definition['definition'][:1000]}...\n\n"
                            f"*Example:*\n{definition['example'][:500]}...\n\n"
                            f"👍 {definition['thumbs_up']} | 👎 {definition['thumbs_down']}"
                        )
                        await update.message.reply_text(message, parse_mode='Markdown')
                    else:
                        await update.message.reply_text(f"No definition found for '{word}'")
        except Exception as e:
            await update.message.reply_text("Error accessing Urban Dictionary")

async def truth_or_dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /tod <truth/dare>\n"
            "Example: /tod truth"
        )
        return
    
    choice = context.args[0].lower()
    if choice == "truth":
        question = random.choice(TRUTH_QUESTIONS)
        await update.message.reply_text(
            f"🤔 *Truth Question:*\n\n{question}",
            parse_mode='Markdown'
        )
    elif choice == "dare":
        challenge = random.choice(DARE_CHALLENGES)
        await update.message.reply_text(
            f"😈 *Dare Challenge:*\n\n{challenge}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("Please choose either 'truth' or 'dare'")

async def never_have_i_ever(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = random.choice(NHIE_QUESTIONS)
    await update.message.reply_text(
        f"🎮 *Never Have I Ever...*\n\n{question}\n\n"
        "Reply with 🙋‍♂️ if you have\n"
        "Reply with 🙅‍♂️ if you haven't",
        parse_mode='Markdown'
    )

# Add this after bot initialization in main():
async def set_commands(app):
    commands = [
        # Karma Commands
        ("rewards", "Get daily karma points"),
        ("store", "View karma store"),
        ("buy", "Purchase status with PID"),
        ("give", "Give karma to another user"),
        ("karma", "Check karma points"),
        ("leaderboard", "View status leaderboard"),
        
        # Fun Commands
        ("urban", "Search Urban Dictionary"),
        ("tod", "Play Truth or Dare"),
        ("nhie", "Play Never Have I Ever"),
        
        # Moderation Commands
        ("warn", "Warn a user (Admin)"),
        ("warns", "Check user warnings"),
        ("mute", "Temporarily mute user (Admin)"),
        ("unmute", "Remove user's mute (Admin)"),
        ("ban", "Ban user from group (Admin)"),
        ("unban", "Remove user's ban (Admin)"),
        ("clean", "Delete recent messages (Admin)"),
        ("filters", "Manage word filters (Admin)"),
        
        # Utility Commands
        ("poll", "Create a poll"),
        ("pin", "Pin a message (Admin)"),
        ("unpin", "Unpin current message (Admin)"),
        ("tr", "Translate message")
    ]
    
    await app.bot.set_my_commands(commands)

# Update the help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *AegisIX Bot v2.2.0*

*Karma Commands:*
/rewards - Get daily karma points (1-300)
/karma - Check your karma balance
/give - Give karma to another user
/store - Browse the karma store
/buy - Purchase status with PID
/leaderboard - View status rankings

*Fun Commands:*
/shipping - Ship two random members
/info - View detailed user info
/urban <word> - Search Urban Dictionary
/tod <truth/dare> - Truth or Dare game
/nhie - Never Have I Ever game

*Admin Commands:*
/filters - Manage word filters
/warn - Warn a user
/mute - Temporarily mute user
/unmute - Remove user's mute
/ban - Ban user from group
/unban - Remove user's ban
/clean - Delete recent messages

*Utility Commands:*
/poll - Create a poll
/pin - Pin a message
/unpin - Unpin current message
/tr - Translate message

*Notes:*
• Karma rewards refresh daily
• Status purchases are permanent
• Shipping resets every 24h
• Some commands require admin rights

💡 Bot Version: 2.2.0
👨‍💻 Developer: @BeMyChase
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def dev_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dev_info = """
🛠 *Developer Information*
Developer: @BeMyChase
Version: 2.2.0
Framework: Telegraf.js
Language: Python 3.9+

*Recent Updates:*
• Added karma system with store
• Added shipping feature
• Added word filters
• Added detailed user info
• Enhanced welcome messages
• Improved error handling

*Stats:*
• 20+ Status ranks
• 10 Welcome messages
• 9+ Bot commands
"""
    await update.message.reply_text(dev_info, parse_mode='Markdown')

# Update the start_bot and main functions
async def start_bot(app):
    try:
        print("🤖 Starting AegisIX Bot v2.2.0...")
        
        # Set commands
        await set_commands(app)
        
        # Start bot
        await app.initialize()
        await app.start()
        print("✅ Bot is ready!")
        
        # Start polling in the background
        await app.updater.start_polling()
        
        # Keep the bot running until interrupted
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
    finally:
        await app.shutdown()

def main():
    try:
        # Create application instance
        app = Application.builder().token(os.getenv('BOT_TOKEN')).build()

        # Register commands
        app.add_handler(CommandHandler("start", help_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("dev", dev_command))
        app.add_handler(CommandHandler("rewards", rewards))
        app.add_handler(CommandHandler("store", store))
        app.add_handler(CommandHandler("buy", buy))
        app.add_handler(CommandHandler("give", give))
        app.add_handler(CommandHandler("karma", check_karma))
        app.add_handler(CommandHandler("leaderboard", leaderboard))
        app.add_handler(CommandHandler("info", user_info))
        app.add_handler(CommandHandler("filters", manage_filters))
        app.add_handler(CommandHandler("shipping", ship_members))
        
        # Add message handlers
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

        # Add new fun commands
        app.add_handler(CommandHandler("urban", urban_dict))
        app.add_handler(CommandHandler("tod", truth_or_dare))
        app.add_handler(CommandHandler("nhie", never_have_i_ever))
        
        # Run the bot with proper async handling
        asyncio.run(start_bot(app))
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        print("👋 Bot stopped")

if __name__ == '__main__':
    main()