const { Telegraf } = require('telegraf');
const fs = require('fs');
const path = require('path');
const os = require('os');
const jsonfile = require('jsonfile');
const { promisify } = require('util');
const setTimeoutPromise = promisify(setTimeout);

// Load environment variables
require('dotenv').config();

// Initialize warnings data
const WARNINGS_FILE = path.join(__dirname, 'warnings.json');
let warnings = {};

// Load existing warnings
try {
    warnings = JSON.parse(fs.readFileSync(WARNINGS_FILE, 'utf8'));
} catch (error) {
    fs.writeFileSync(WARNINGS_FILE, '{}');
}

// Helper function to save warnings
function saveWarnings() {
    fs.writeFileSync(WARNINGS_FILE, JSON.stringify(warnings, null, 2));
}

// Helper function to check admin status
async function isAdmin(ctx) {
    try {
        const member = await ctx.telegram.getChatMember(ctx.chat.id, ctx.from.id);
        return ['creator', 'administrator'].includes(member.status);
    } catch (error) {
        console.error('Admin check error:', error);
        return false;
    }
}

// Initialize data storage
const CHATS_FILE = path.join(__dirname, 'data', 'chats.json');
let chatsData = { groups: [], users: [] };

// Load existing chats data
try {
    chatsData = JSON.parse(fs.readFileSync(CHATS_FILE, 'utf8'));
} catch (error) {
    // Create data directory if it doesn't exist
    if (!fs.existsSync(path.join(__dirname, 'data'))) {
        fs.mkdirSync(path.join(__dirname, 'data'));
    }
    fs.writeFileSync(CHATS_FILE, JSON.stringify(chatsData, null, 2));
}

// Helper function to save chats
function saveChats() {
    fs.writeFileSync(CHATS_FILE, JSON.stringify(chatsData, null, 2));
}

// Karma system files
const KARMA_FILE = 'data/karma.json';
const COOLDOWN_FILE = 'data/cooldowns.json';

// Product/Status definitions
const PRODUCTS = {
    "P001": { "name": "⚡ Alpha Status", "price": 5000, "rank": 5 },
    "P002": { "name": "🌟 Sigma Status", "price": 3000, "rank": 4 },
    "P003": { "name": "💫 Beta Status", "price": 2000, "rank": 3 },
    "P004": { "name": "✨ Omega Status", "price": 1000, "rank": 2 },
    "P005": { "name": "🌙 Nova Status", "price": 500, "rank": 1 }
};

// Load or create karma data
function loadData() {
    try {
        return jsonfile.readFileSync(KARMA_FILE);
    } catch (error) {
        return { "users": {}, "purchases": {} };
    }
}

// Save karma data
function saveData(data) {
    jsonfile.writeFileSync(KARMA_FILE, data, { spaces: 2 });
}

// Command handlers
async function rewards(ctx) {
    const userId = ctx.from.id.toString();
    const username = ctx.from.username || userId;

    let data = loadData();
    let cooldowns = loadCooldownData();

    // Check cooldown
    if (userId in cooldowns) {
        const lastClaim = new Date(cooldowns[userId]);
        const now = new Date();
        const diff = now - lastClaim;

        // If less than 24 hours, show remaining time
        if (diff < 24 * 60 * 60 * 1000) {
            const hours = Math.floor((24 * 60 * 60 * 1000 - diff) / (60 * 60 * 1000));
            const minutes = Math.floor((24 * 60 * 60 * 1000 - diff) % (60 * 60 * 1000) / (60 * 1000));
            return ctx.reply(`⏳ You can claim rewards again in ${hours}h ${minutes}m`);
        }
    }

    // Generate random karma
    const karma = Math.floor(Math.random() * 300) + 1;

    // Update user data
    if (!(userId in data.users)) {
        data.users[userId] = { "karma": 0, "username": username };
    }

    data.users[userId].karma += karma;
    cooldowns[userId] = new Date().toISOString();

    saveData(data);
    saveCooldownData(cooldowns);

    ctx.reply(`🎉 You received ${karma} karma points!\nCurrent balance: ${data.users[userId].karma} points`);
}

async function store(ctx) {
    let storeText = "*🏪 Karma Store*\n\n";
    for (const [pid, product] of Object.entries(PRODUCTS)) {
        storeText += `*${product.name}*\n`;
        storeText += `Price: ${product.price} karma\n`;
        storeText += `PID: \`${pid}\`\n\n`;
    }

    storeText += "\nTo buy: `/buy PID`";
    await ctx.reply(storeText, { parse_mode: 'Markdown' });
}

async function buy(ctx) {
    if (!ctx.args.length) {
        return ctx.reply("❌ Please specify a Product ID (PID)");
    }

    const pid = ctx.args[0].toUpperCase();
    if (!(pid in PRODUCTS)) {
        return ctx.reply("❌ Invalid Product ID");
    }

    const userId = ctx.from.id.toString();
    let data = loadData();

    if (!(userId in data.users)) {
        return ctx.reply("❌ You don't have any karma points");
    }

    const product = PRODUCTS[pid];
    const userKarma = data.users[userId].karma;

    if (userKarma < product.price) {
        return ctx.reply(`❌ Insufficient karma points\nYou need ${product.price - userKarma} more points`);
    }

    // Check if user already owns this product
    if (userId in data.purchases && pid in data.purchases[userId]) {
        return ctx.reply("❌ You already own this status");
    }

    // Process purchase
    data.users[userId].karma -= product.price;
    if (!(userId in data.purchases)) {
        data.purchases[userId] = {};
    }
    data.purchases[userId][pid] = new Date().toISOString();

    saveData(data);

    ctx.reply(
        `✅ Successfully purchased ${product.name}\n` +
        `Remaining karma: ${data.users[userId].karma}`
    );
}

async function leaderboard(ctx) {
    let data = loadData();

    // Calculate user scores based on their purchases
    let userScores = [];
    for (const [userId, purchases] of Object.entries(data.purchases)) {
        const totalRank = Object.keys(purchases).reduce((sum, pid) => {
            return sum + PRODUCTS[pid].rank;
        }, 0);
        const username = data.users[userId].username;
        const statuses = Object.keys(purchases).map(pid => PRODUCTS[pid].name);
        userScores.push({ username, totalRank, statuses });
    }

    // Sort by total rank
    userScores.sort((a, b) => b.totalRank - a.totalRank);

    // Format leaderboard
    let lbText = "*🏆 Status Leaderboard*\n\n";
    for (let i = 0; i < Math.min(userScores.length, 10); i++) {
        const { username, totalRank, statuses } = userScores[i];
        const medal = i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}.`;
        lbText += `${medal} @${username}\n`;
        lbText += `Statuses: ${statuses.join(' ')}\n\n`;
    }

    await ctx.reply(lbText, { parse_mode: 'Markdown' });
}

function main() {
    const bot = new Telegraf(process.env.BOT_TOKEN);

    // Register commands
    bot.command('start', (ctx) => {
        ctx.replyWithMarkdown(`
👋 *Welcome to AegisIX Bot!*

I'm a group management bot with moderation and utility features.
Use /help to see available commands.

*Features:*
• Group Moderation
• Message Translation
• Polls Creation
• And more!
        `);
    });

    // Help command
    bot.command('help', (ctx) => {
        ctx.replyWithMarkdown(`
🤖 *AegisIX Bot v2.0.0*

*Basic Commands:*
/start - Start the bot
/help - Show this help menu
/dev - Developer information

*Moderation Commands:*
/warn - Warn a user (reply required)
/warns - Check user's warnings
/mute <minutes> - Temporarily mute user
/unmute - Remove user's mute
/ban - Ban user from group
/unban - Remove user's ban
/clean <number> - Delete recent messages

*Utility Commands:*
/poll - Create a poll (multi-line format)
/pin - Pin a message (reply required)
/unpin - Unpin current pinned message
/tr <lang> - Translate message to specified language

*Note:* 
• Moderation commands require admin privileges
• Use reply for user-targeted commands

For additional help, contact @BeMyChase
        `);
    });

    // Dev command
    bot.command('dev', (ctx) => {
        ctx.replyWithMarkdown(`
🛠 *Developer Information*
Developer: @BeMyChase
Version: 2.0.0
Framework: Telegraf.js
Language: Node.js

*Updates:*
• Improved moderation tools
• Enhanced performance
• Better error handling
        `);
    });

    // Warn command
    bot.command('warn', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to warn the user');

        const userId = ctx.message.reply_to_message.from.id;
        const username = ctx.message.reply_to_message.from.username || userId;

        warnings[userId] = (warnings[userId] || 0) + 1;
        saveWarnings();

        ctx.reply(`⚠️ @${username} has been warned.\nTotal warnings: ${warnings[userId]}`);
    });

    // Check warnings command
    bot.command('warns', async (ctx) => {
        const userId = ctx.message.reply_to_message?.from.id || ctx.from.id;
        const count = warnings[userId] || 0;
        ctx.reply(`Total warnings: ${count}`);
    });

    // Mute command
    bot.command('mute', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to mute the user');

        const minutes = parseInt(ctx.message.text.split(' ')[1]) || 60;
        const untilDate = Math.floor(Date.now() / 1000) + (minutes * 60);

        try {
            await ctx.restrictChatMember(ctx.message.reply_to_message.from.id, {
                until_date: untilDate,
                can_send_messages: false
            });
            ctx.reply(`🤐 User muted for ${minutes} minutes`);
        } catch (error) {
            ctx.reply('❌ Failed to mute user');
        }
    });

    // Unmute command
    bot.command('unmute', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to unmute the user');

        try {
            await ctx.restrictChatMember(ctx.message.reply_to_message.from.id, {
                can_send_messages: true,
                can_send_media_messages: true,
                can_send_other_messages: true,
                can_add_web_page_previews: true
            });
            ctx.reply('🔊 User unmuted');
        } catch (error) {
            ctx.reply('❌ Failed to unmute user');
        }
    });

    // Ban command
    bot.command('ban', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to ban the user');

        try {
            await ctx.banChatMember(ctx.message.reply_to_message.from.id);
            ctx.reply('🚫 User banned');
        } catch (error) {
            ctx.reply('❌ Failed to ban user');
        }
    });

    // Unban command
    bot.command('unban', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to unban the user');

        try {
            await ctx.unbanChatMember(ctx.message.reply_to_message.from.id);
            ctx.reply('✅ User unbanned');
        } catch (error) {
            ctx.reply('❌ Failed to unban user');
        }
    });

    // Clean messages command
    bot.command('clean', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        
        const amount = parseInt(ctx.message.text.split(' ')[1]) || 10;
        const max = Math.min(amount, 100);

        try {
            for (let i = 0; i < max; i++) {
                try {
                    await ctx.telegram.deleteMessage(ctx.chat.id, ctx.message.message_id - i);
                } catch (e) {
                    continue;
                }
            }
            const msg = await ctx.reply(`🧹 Cleaned ${max} messages`);
            setTimeout(() => ctx.telegram.deleteMessage(ctx.chat.id, msg.message_id), 3000);
        } catch (error) {
            ctx.reply('❌ Failed to clean messages');
        }
    });

    // Poll command
    bot.command('poll', (ctx) => {
        const args = ctx.message.text.split('\n');
        if (args.length < 3) {
            return ctx.reply(
                '❌ Please use this format:\n' +
                '/poll Question\nOption 1\nOption 2\n[Option 3...]'
            );
        }

        const question = args[0].replace('/poll ', '');
        const options = args.slice(1);

        ctx.replyWithPoll(question, options, { is_anonymous: true });
    });

    // Pin message command
    bot.command('pin', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        if (!ctx.message.reply_to_message) return ctx.reply('⚠️ Reply to a message to pin it');

        try {
            await ctx.pinChatMessage(ctx.message.reply_to_message.message_id);
            ctx.reply('📌 Message pinned');
        } catch (error) {
            ctx.reply('❌ Failed to pin message');
        }
    });

    // Unpin message command
    bot.command('unpin', async (ctx) => {
        if (!await isAdmin(ctx)) return ctx.reply('❌ Only admins can use this command');
        
        try {
            await ctx.unpinChatMessage();
            ctx.reply('📍 Message unpinned');
        } catch (error) {
            ctx.reply('❌ Failed to unpin message');
        }
    });

    // Hidden broadcast command (only accessible by bot owner)
    bot.command('broadcast', async (ctx) => {
        // Check if user is bot owner
        if (ctx.from.id.toString() !== process.env.BOT_OWNER_ID) {
            return ctx.reply('❌ Only the bot owner can use this command');
        }

        // Get the message content
        const messageToForward = ctx.message.reply_to_message || ctx.message;
        const broadcastText = ctx.message.text.split('/broadcast ')[1];

        // If no reply and no text after command, show error
        if (!messageToForward && !broadcastText) {
            return ctx.reply('❌ Please provide a message to broadcast or reply to a message');
        }

        try {
            let successCount = 0;
            let failCount = 0;

            // Send to all groups
            for (const groupId of chatsData.groups) {
                try {
                    if (messageToForward.photo) {
                        // Forward photo with caption
                        await ctx.telegram.sendPhoto(groupId, messageToForward.photo[0].file_id, {
                            caption: broadcastText || messageToForward.caption,
                            parse_mode: 'Markdown'
                        });
                    } else {
                        // Forward text message
                        await ctx.telegram.sendMessage(groupId, broadcastText || messageToForward.text, {
                            parse_mode: 'Markdown'
                        });
                    }
                    successCount++;
                    // Add delay between messages
                    await setTimeoutPromise(100);
                } catch (error) {
                    console.error(`Failed to send to group ${groupId}:`, error.message);
                    failCount++;
                }
            }

            // Send status to owner
            const status = `📣 *Broadcast Results*\n\n` +
                `✅ Successfully sent to: ${successCount} groups\n` +
                `❌ Failed: ${failCount} groups\n` +
                `📊 Total groups: ${chatsData.groups.length}`;

            await ctx.reply(status, { parse_mode: 'Markdown' });

        } catch (error) {
            console.error('Broadcast error:', error);
            await ctx.reply('❌ An error occurred during broadcast');
        }
    });

    // List chats command
    bot.command('listchats', async (ctx) => {
        // Check if user is bot owner
        if (ctx.from.id.toString() !== process.env.BOT_OWNER_ID) {
            return; // Silently ignore if not bot owner
        }

        try {
            const stats = {
                users: chatsData.users.length,
                groups: chatsData.groups.length
            };

            const message = `📊 *Stored Chats Statistics*\n` +
                `👤 Private Chats: ${stats.users}\n` +
                `👥 Groups: ${stats.groups}\n` +
                `📝 Total: ${stats.users + stats.groups}`;

            await ctx.reply(message, { parse_mode: 'Markdown' });
        } catch (error) {
            console.error('Error listing chats:', error);
        }
    });

    // Add a command to check stored chats
    bot.command('chats', async (ctx) => {
        if (ctx.from.id.toString() !== process.env.BOT_OWNER_ID) return;
        
        const stats = `📊 *Stored Chats*\n\n` +
            `Groups: ${chatsData.groups.length}\n` +
            `Users: ${chatsData.users.length}\n\n` +
            `Group IDs: \`${chatsData.groups.join(', ')}\`\n` +
            `User IDs: \`${chatsData.users.join(', ')}\``;
        
        await ctx.reply(stats, { parse_mode: 'Markdown' });
    });

    // Add karma command
    bot.command('rewards', rewards);

    // Store command
    bot.command('store', store);

    // Buy command
    bot.command('buy', buy);

    // Leaderboard command
    bot.command('leaderboard', leaderboard);

    // Launch the bot
    bot.launch();
}

main();

// Install required packages
// pip install python-telegram-bot python-dotenv

// Create data directory and files if they don't exist
if (!fs.existsSync('data')) {
    fs.mkdirSync('data');
}
if (!fs.existsSync(KARMA_FILE)) {
    fs.writeFileSync(KARMA_FILE, JSON.stringify({ users: {}, purchases: {} }, null, 2));
}
if (!fs.existsSync(COOLDOWN_FILE)) {
    fs.writeFileSync(COOLDOWN_FILE, JSON.stringify({}, null, 2));
}

module.exports = {
    start: startCommand,
    help: helpCommand,
    warn: warnCommand,
    // ...other commands
};