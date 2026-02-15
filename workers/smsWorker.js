// workers/smsWorker.js
const cron = require('node-cron');
const twilio = require('twilio');
const db = require('../server/src/models');

const client = twilio(
    process.env.TWILIO_ACCOUNT_SID,
    process.env.TWILIO_AUTH_TOKEN
);

// Run every day at 9am
cron.schedule('0 9 * * *', async () => {
    console.log('📱 Checking for daily reminders...');

    const today = new Date();
    const threeDaysFromNow = new Date(today);
    threeDaysFromNow.setDate(today.getDate() + 3);

    // Find users with statement dates in 3 days
    const accounts = await db.Account.find({
        statementDate: {
            $dayOfMonth: threeDaysFromNow.getDate()
        },
        notifications: { $in: ['sms'] }
    }).populate('userId');

    for (const account of accounts) {
        const user = account.userId;
        const message = `🔔 CredStack Alert: Your ${account.name} statement closes in 3 days. Current balance: $${account.balance}. Pay down to $${Math.floor(account.limit * 0.1)} to optimize credit utilization.`;

        try {
            await client.messages.create({
                body: message,
                to: user.phone,
                from: process.env.TWILIO_PHONE_NUMBER
            });
            console.log(`✓ Sent reminder to ${user.phone}`);
        } catch (error) {
            console.error(`✗ Failed to send to ${user.phone}:`, error);
        }
    }
});

console.log('📱 SMS worker started...');
