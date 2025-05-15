const { Telegraf } = require('telegraf');
require('dotenv').config();
const commands = require('./commands');
const registerRanking = require('./features/ranking');
const fs = require('fs');
const path = require('path');

// Initialize data storage
const DATA_DIR = path.join(__dirname, 'data');
const CHATS_FILE = path.join(DATA_DIR, 'chats.json');

// Create data directory if it doesn't exist
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR);
}

// Initialize chats data
let chatsData = { groups: [], users: [] };

// Load existing chats data
try {
    chatsData = JSON.parse(fs.readFileSync(CHATS_FILE, 'utf8'));
} catch (error) {
    fs.writeFileSync(CHATS_FILE, JSON.stringify(chatsData, null, 2));
}

// Helper function to save chats
function saveChats() {
    fs.writeFileSync(CHATS_FILE, JSON.stringify(chatsData, null, 2));
}

// Initialize bot
const bot = new Telegraf(process.env.BOT_TOKEN);

// Register commands
if (typeof commands === 'object') {
    Object.keys(commands).forEach(command => {
        if (typeof commands[command] === 'function') {
            bot.command(command, commands[command]);
        }
    });
} else {
    console.error('Commands module not properly exported');
}

// Debug middleware
bot.use(async (ctx, next) => {
    // Enhanced debug logging
    if (ctx.message?.text) {
        console.log(`Message received in ${ctx.chat.type} chat:`, {
            chatId: ctx.chat.id,
            from: ctx.from.username || ctx.from.id,
            text: ctx.message.text
        });
    }

    // Track chat if not already tracked
    const chatId = ctx.chat?.id;
    const chatType = ctx.chat?.type;
    
    if (chatId && chatType) {
        if (chatType === 'private' && !chatsData.users.includes(chatId)) {
            console.log(`📝 Tracking new private chat: ${chatId}`);
            chatsData.users.push(chatId);
            saveChats();
        } else if ((chatType === 'group' || chatType === 'supergroup') && !chatsData.groups.includes(chatId)) {
            console.log(`📝 Tracking new group chat: ${chatId}`);
            chatsData.groups.push(chatId);
            saveChats();
        }
    }

    await next();
});

// Track new chats and members
bot.on(['new_chat_members'], async (ctx) => {
    const chatId = ctx.chat.id;
    if (!chatsData.groups.includes(chatId)) {
        console.log(`➕ Adding new group from new_chat_members: ${chatId}`);
        chatsData.groups.push(chatId);
        saveChats();
    }
});

bot.on(['left_chat_member'], async (ctx) => {
    if (ctx.message.left_chat_member.id === ctx.botInfo.id) {
        const chatId = ctx.chat.id;
        console.log(`➖ Removing group: ${chatId}`);
        chatsData.groups = chatsData.groups.filter(id => id !== chatId);
        saveChats();
    }
});

// Enhanced startup function
async function startBot() {
    try {
        // Clear any existing webhooks
        await bot.telegram.deleteWebhook({ drop_pending_updates: true });
        
        // Launch bot with specific polling options
        await bot.launch({
            dropPendingUpdates: true,
            polling: {
                timeout: 30,
                limit: 100
            }
        });

        console.log('🤖 AegisIX is running...');
        console.log('Press Ctrl + C to stop');

    } catch (error) {
        if (error.message.includes('409: Conflict')) {
            console.error('❌ Another instance of the bot is already running!');
            console.error('Please stop other instances before starting a new one.');
            process.exit(1);
        }
        console.error('Startup error:', error);
        process.exit(1);
    }
}

// Enhanced shutdown handling
async function shutdown(signal) {
    console.log(`\n${signal} signal received. Shutting down gracefully...`);
    try {
        // Stop the bot
        await bot.stop(signal);
        console.log('Bot stopped successfully');
        
        // Save any pending data
        saveChats();
        console.log('Data saved successfully');
        
        process.exit(0);
    } catch (error) {
        console.error('Error during shutdown:', error);
        process.exit(1);
    }
}

// Register shutdown handlers
process.once('SIGINT', () => shutdown('SIGINT'));
process.once('SIGTERM', () => shutdown('SIGTERM'));

// Start the bot
startBot();
