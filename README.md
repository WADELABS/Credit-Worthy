# CredStack 🏦

**Stop guessing about your credit. Start automating it.**

CredStack is an open-source automation assistant that helps you maintain and improve your credit score through simple, scheduled reminders and smart notifications.

## 🚀 Quick Start

1. **Clone & Setup**
   ```bash
   git clone https://github.com/WADELABS/Credit-Worthy.git
   cd Credit-Worthy
   pip install -r requirements.txt
   ```

2. **Initialize Wizard**
   ```bash
   python setup.py
   ```
   Follow the prompts to create your profile and set your automation level (Basic or Advanced).

3. **Launch Dashboard**
   ```bash
   python app.py
   ```
   Open [http://localhost:5000](http://localhost:5000) to view your dashboard.

4. **Start Background Scheduler**
   ```bash
   python workers/scheduler.py
   ```

## 🧠 How It Works

CredStack focus on the 3 pillars of credit repair:
1. **Consistency**: Automated reminders for statement dates and payments.
2. **Utilization Management**: Alerts to pay down balances *before* statements close.
3. **Accuracy**: A built-in tracker for bureau disputes and follow-ups.

## 🛠️ Tech Stack
- **Backend**: Python / Flask
- **Database**: SQLite (Local & Fast)
- **Frontend**: Vanilla CSS (Glassmorphism UI)
- **Workers**: Multiprocess-ready background scripts

## ⚖️ License
MIT - Build it, break it, fix your credit.