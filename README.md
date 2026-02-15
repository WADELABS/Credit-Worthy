# CredStack 🏦

**Stop guessing about your credit. Start automating it.**

CredStack is an open-source automation assistant that helps you maintain and improve your credit score through simple, scheduled reminders and smart notifications. It turns credit repair from an overwhelming mystery into a set of manageable weekly habits.

## 🚀 The Problem We Solve

> **"A friend called me, sounding completely defeated. Her credit score had just dropped 27 points, and she had no idea why. 'I paid everything on time,' she said. 'I don't understand how this works.'**
> 
> **I explained that it could be anything—reduction in account age, hard inquiries, or even just a high balance being reported at the wrong time. She sighed and said she wished there was a simpler way to keep up with it all.**
> 
> **That's when it clicked: credit repair isn't about magic; it's about consistency + catching problems early. And automation is perfect for that. So I decided to build her an assistant that does the 'keeping up' for her."**

## ✨ Core Automations

| Automation | What It Does | Why It Matters |
|------------|--------------|----------------|
| **Autopay Safety Net** | Sets min payment autopay on all accounts | Never miss a payment, ever |
| **Statement Date Alert** | Reminds you 3 days before statement closes | Keeps utilization low when reported |
| **Weekly Balance Scan** | Friday check-in on all card balances | Stops "silent" score drops |
| **Monthly Report Pull** | Rotates through 3 bureaus monthly | Catches errors/fraud immediately |
| **Dispute Tracker** | Follows up every 14 days | Keeps disputes from stalling |
| **One Thing Per Month** | Suggests a single improvement task | Repair without overwhelm |

## 🎯 The "80/20" Stack

Just want the basics that fix 80% of issues?

✅ **Autopay minimum** on everything  
✅ **Statement-close reminder** 3 days before  
✅ **Monthly credit report check**  

Set these 3 things and you're 90% protected.

## 🛠️ Quick Start (10 minutes)

### Prerequisites
- Node.js 18+
- A Google account (for calendar integration)
- (Optional) Plaid API key for automatic balance tracking

### Installation

```bash
# Clone the repo
git clone https://github.com/WADELABS/credstack.git
cd credstack

# Install dependencies
npm run install:all

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the setup wizard
npm run setup

# Start the app
npm run dev
```

## 🏗️ Project Structure

```
credstack/
├── client/          # React frontend
├── server/          # Node.js/Express backend
├── workers/         # Background job processors
├── docs/            # Documentation
└── infrastructure/  # Deployment configs
```

## 🔧 API Integrations

- **Plaid** - Connect bank/credit accounts for automatic balance tracking
- **Google Calendar API** - Create calendar events for reminders
- **Twilio** - Send SMS reminders
- **SendGrid/Resend** - Email notifications

---
*Developed by WADELABS. Precision Finance. Zero Guessing.*
