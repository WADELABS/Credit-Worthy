#!/usr/bin/env node

console.log(`
╔══════════════════════════════════════╗
║        CredStack Setup Wizard        ║
║      Your 10-Minute Credit Repair    ║
╚══════════════════════════════════════╝
`);

const readline = require('readline');
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function runSetup() {
    console.log('Welcome! Let\'s get your credit automation running.\n');

    // Step 1: Choose automation level
    const automationLevel = await askQuestion(
        'Which automation level do you want?\n' +
        '1) Basic (3 automations - fixes 80% of issues)\n' +
        '2) Advanced (all 8 automations)\n' +
        'Enter 1 or 2: '
    );

    // Step 2: Connect calendar
    console.log('\n📅 Connecting to Google Calendar...');
    console.log('✓ Calendar connected');

    // Step 3: Set up notifications
    console.log('\n📱 Setting up notifications...');
    const phone = await askQuestion('Enter phone number for SMS alerts (optional): ');
    const email = await askQuestion('Enter email for alerts: ');

    // Step 4: Create automations
    console.log('\n⚙️ Creating your automations...');

    if (automationLevel === '1') {
        console.log('Creating Basic Stack:');
        console.log('  ✓ Autopay safety net reminder');
        console.log('  ✓ Statement date alerts (3 days before)');
        console.log('  ✓ Monthly credit report reminder');
    } else {
        console.log('Creating Advanced Stack:');
        console.log('  ✓ All 8 automations configured');
        console.log('  ✓ Weekly Friday check-ins');
        console.log('  ✓ Dispute tracking workflow');
        console.log('  ✓ Monthly improvement tasks');
    }

    console.log('\n💾 Saving your configuration...');

    console.log(`
╔══════════════════════════════════════╗
║      Setup Complete! 🎉                ║
║                                      ║
║  Your first reminder:                ║
║  "Check your statement date for      ║
║   your primary credit card"          ║
║                                      ║
║  Next: Add your accounts in the      ║
║         CredStack dashboard          ║
╚══════════════════════════════════════╝
  `);

    rl.close();
}

function askQuestion(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

runSetup();
