const fs = require('fs');
const path = require('path');

// Initialize ranking data storage
const RANKS_FILE = path.join(__dirname, '..', 'data', 'ranks.json');
let rankData = {};

// Aura ranks configuration
const AURA_RANKS = [
    { level: 0, name: '⚪ Dormant Aura', minMessages: 0 },
    { level: 1, name: '🔵 Ethereal Aura', minMessages: 100 },
    { level: 2, name: '🟣 Mystic Aura', minMessages: 500 },
    { level: 3, name: '🟡 Celestial Aura', minMessages: 1000 },
    { level: 4, name: '🔴 Phoenix Aura', minMessages: 2500 },
    { level: 5, name: '⚡ Thunder Aura', minMessages: 5000 },
    { level: 6, name: '🌟 Astral Aura', minMessages: 10000 },
    { level: 7, name: '👑 Divine Aura', minMessages: 25000 },
    { level: 8, name: '🌈 Legendary Aura', minMessages: 50000 },
    { level: 9, name: '✨ Immortal Aura', minMessages: 100000 }
];

// Load existing rank data
try {
    rankData = JSON.parse(fs.readFileSync(RANKS_FILE, 'utf8'));
} catch (error) {
    fs.writeFileSync(RANKS_FILE, JSON.stringify(rankData, null, 2));
}

// Helper function to save rank data
function saveRanks() {
    fs.writeFileSync(RANKS_FILE, JSON.stringify(rankData, null, 2));
}

// Get user's current rank
function getUserRank(messages) {
    return AURA_RANKS.reduce((prev, curr) => {
        return messages >= curr.minMessages ? curr : prev;
    });
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function registerRanking(bot) {
    // Track messages for ranking
    bot.on('message', async (ctx) => {
        const chatId = ctx.chat.id.toString();
        const userId = ctx.from.id.toString();
        
        if (!rankData[chatId]) {
            rankData[chatId] = {};
        }
        
        if (!rankData[chatId][userId]) {
            rankData[chatId][userId] = {
                messages: 0,
                username: ctx.from.username || ctx.from.first_name,
                lastMessageTime: 0,
                currentLevel: 0
            };
        }

        // Anti-spam: Only count messages if 3 seconds have passed
        const now = Date.now();
        if (now - rankData[chatId][userId].lastMessageTime >= 3000) {
            const oldRank = getUserRank(rankData[chatId][userId].messages);
            
            // Increment messages
            rankData[chatId][userId].messages++;
            rankData[chatId][userId].lastMessageTime = now;
            rankData[chatId][userId].username = ctx.from.username || ctx.from.first_name;
            
            // Check for level up
            const newRank = getUserRank(rankData[chatId][userId].messages);
            if (newRank.level > oldRank.level) {
                // Send level up notification
                const levelUpMsg = `
🌟 *Level Up!* 🌟
Congratulations ${ctx.from.username || ctx.from.first_name}!

You've reached: *${newRank.name}*
Total Messages: *${formatNumber(rankData[chatId][userId].messages)}*

Keep chatting to reach the next level!
${newRank.level < AURA_RANKS.length - 1 ? `\nNext Rank: ${AURA_RANKS[newRank.level + 1].name}` : ''}`;

                await ctx.replyWithMarkdown(levelUpMsg);
            }
            
            saveRanks();
        }
    });

    // Rank command
    bot.command('rank', async (ctx) => {
        const chatId = ctx.chat.id.toString();
        const userId = ctx.from.id.toString();

        if (!rankData[chatId]?.[userId]) {
            return ctx.reply('You haven\'t sent any messages yet!');
        }

        const userStats = rankData[chatId][userId];
        const currentRank = getUserRank(userStats.messages);
        const nextRank = AURA_RANKS[currentRank.level + 1];
        
        let progressBar = '';
        if (nextRank) {
            const progress = (userStats.messages - currentRank.minMessages) / 
                           (nextRank.minMessages - currentRank.minMessages);
            const filled = Math.floor(progress * 10);
            progressBar = '█'.repeat(filled) + '▒'.repeat(10 - filled);
        } else {
            progressBar = '█'.repeat(10);
        }

        const rankMessage = `
👤 *User:* ${userStats.username}
${currentRank.name}
📊 *Messages:* ${formatNumber(userStats.messages)}
📈 *Progress:*
${progressBar} ${nextRank ? `(${formatNumber(userStats.messages)}/${formatNumber(nextRank.minMessages)})` : '(MAX)'}
${nextRank ? `\n*Next Rank:* ${nextRank.name}` : ''}`;

        await ctx.replyWithMarkdown(rankMessage);
    });

    // Leaderboard command
    bot.command(['lb', 'leaderboard'], async (ctx) => {
        const chatId = ctx.chat.id.toString();
        
        if (!rankData[chatId]) {
            return ctx.reply('No rankings available for this chat!');
        }

        const rankings = Object.entries(rankData[chatId])
            .sort(([, a], [, b]) => b.messages - a.messages)
            .slice(0, 10);

        const leaderboard = rankings.map(([, user], index) => {
            const rank = getUserRank(user.messages);
            return `${['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'][index]} *${user.username}*\n${rank.name} | Messages: ${formatNumber(user.messages)}`;
        }).join('\n\n');

        await ctx.replyWithMarkdown(`*📊 Group Leaderboard*\n\n${leaderboard}`);
    });
}

module.exports = registerRanking;