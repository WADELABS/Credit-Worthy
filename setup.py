#!/usr/bin/env python3
"""
CredStack Setup Wizard
Run this script to initialize your credit automation system.
"""

import os
import sys
import sqlite3
import getpass
from datetime import datetime
import questionary
from colorama import init, Fore, Style
import click

init(autoreset=True)

def print_banner():
    """Print the CredStack banner"""
    banner = f"""
{Fore.CYAN}{'='*60}
{Fore.YELLOW}   ______          _      ____  _             _    
{Fore.YELLOW}  / ____|   ___   | | __/ ___|| |_      __ _| | __
{Fore.YELLOW} | |       / _ \  | |/ /\___ \| __|    / _` | |/ /
{Fore.YELLOW} | |____  | (_) | |   <  ___) | |_    | (_| |   < 
{Fore.YELLOW}  \_____|  \___/  |_|\_\|____/ \__|    \__,_|_|\_\
{Fore.CYAN}                                                    
{Fore.GREEN}  Credit Repair Automation - Setup Wizard v1.0
{Fore.CYAN}{'='*60}
{Fore.RESET}
"""
    print(banner)

def check_python_version():
    """Verify Python version is compatible"""
    if sys.version_info < (3, 8):
        print(f"{Fore.RED}✗ Error: Python 3.8+ required")
        sys.exit(1)
    print(f"{Fore.GREEN}✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def create_database():
    """Initialize the SQLite database"""
    db_path = 'database/credstack.db'
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notification_preference TEXT DEFAULT 'email',
            automation_level TEXT DEFAULT 'basic'
        )
    ''')
    
    # Create accounts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance DECIMAL(10,2) DEFAULT 0,
            credit_limit DECIMAL(10,2),
            statement_date INTEGER,
            due_date INTEGER,
            min_payment DECIMAL(10,2),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create automations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS automations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            automation_type TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            configuration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_run TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create reminders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_type TEXT NOT NULL,
            reminder_date DATE NOT NULL,
            message TEXT,
            is_sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create disputes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disputes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bureau TEXT NOT NULL,
            account_name TEXT,
            dispute_date DATE NOT NULL,
            follow_up_date DATE,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"{Fore.GREEN}✓ Database initialized at {db_path}")

def setup_user():
    """Create user profile"""
    print(f"\n{Fore.CYAN}📝 Let's set up your profile")
    
    email = questionary.text("What's your email address?").ask()
    if not email:
        print(f"{Fore.RED}✗ Email is required")
        sys.exit(1)
    
    phone = questionary.text("What's your phone number? (optional, for SMS)").ask()
    
    name = questionary.text("What's your name?").ask()
    
    # Notification preference
    notification = questionary.select(
        "How would you like to receive reminders?",
        choices=[
            "Email only",
            "SMS only", 
            "Both email and SMS",
            "Calendar only"
        ]
    ).ask()
    
    notification_map = {
        "Email only": "email",
        "SMS only": "sms",
        "Both email and SMS": "both",
        "Calendar only": "calendar"
    }
    
    # Automation level
    print(f"\n{Fore.CYAN}⚙️ Choose your automation level:")
    print(f"  {Fore.YELLOW}1) Basic (3 automations - fixes 80% of issues)")
    print(f"     • Autopay safety net")
    print(f"     • Statement date alerts")
    print(f"     • Monthly credit report check")
    print(f"\n  {Fore.YELLOW}2) Advanced (all 8 automations)")
    print(f"     • Everything in Basic")
    print(f"     • Weekly balance scans")
    print(f"     • Dispute tracking")
    print(f"     • Credit builder routine")
    print(f"     • New inquiry alerts")
    print(f"     • Monthly improvement tasks")
    
    level = questionary.select(
        "Which level do you want?",
        choices=["Basic (recommended for beginners)", "Advanced"]
    ).ask()
    
    automation_level = "basic" if "Basic" in level else "advanced"
    
    # Save to database
    conn = sqlite3.connect('database/credstack.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, phone, name, notification_preference, automation_level)
        VALUES (?, ?, ?, ?, ?)
    ''', (email, phone or None, name, notification_map[notification], automation_level))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"{Fore.GREEN}✓ Profile created successfully!")
    return user_id

def setup_automations(user_id):
    """Set up initial automations based on user preference"""
    conn = sqlite3.connect('database/credstack.db')
    cursor = conn.cursor()
    
    # Get user's automation level
    cursor.execute('SELECT automation_level FROM users WHERE id = ?', (user_id,))
    level = cursor.fetchone()[0]
    
    automations = []
    
    # Core automations (always included)
    core_automations = [
        ('autopay_reminder', 'Reminder to set up autopay minimum'),
        ('statement_alert', 'Statement closing date alert'),
        ('monthly_report', 'Monthly credit report pull reminder')
    ]
    
    for auto_type, desc in core_automations:
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type, configuration)
            VALUES (?, ?, ?)
        ''', (user_id, auto_type, desc))
        automations.append(auto_type)
    
    # Advanced automations (if selected)
    if level == 'advanced':
        advanced_automations = [
            ('weekly_scan', 'Friday balance check'),
            ('dispute_tracker', '14-day dispute follow-up'),
            ('credit_builder', 'Payday payment reminder'),
            ('inquiry_alert', 'New inquiry monitor'),
            ('monthly_task', 'One improvement task per month')
        ]
        
        for auto_type, desc in advanced_automations:
            cursor.execute('''
                INSERT INTO automations (user_id, automation_type, configuration)
                VALUES (?, ?, ?)
            ''', (user_id, auto_type, desc))
            automations.append(auto_type)
    
    conn.commit()
    conn.close()
    
    print(f"{Fore.GREEN}✓ Created {len(automations)} automations")
    return automations

def setup_calendar():
    """Guide user through calendar setup"""
    print(f"\n{Fore.CYAN}📅 Calendar Integration")
    print("CredStack can add reminders directly to your Google Calendar.")
    
    setup_now = questionary.confirm("Would you like to set up Google Calendar integration now?").ask()
    
    if setup_now:
        print(f"\n{Fore.YELLOW}To set up Google Calendar:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable the Google Calendar API")
        print("4. Create credentials (OAuth 2.0 Client ID)")
        print("5. Add http://localhost:5000/auth/google/callback to authorized redirects")
        print("6. Copy your Client ID and Secret to the .env file")
        
        input(f"\n{Fore.CYAN}Press Enter once you've completed these steps...")
        
        print(f"{Fore.GREEN}✓ Calendar setup guide completed")
    else:
        print(f"{Fore.YELLOW}⏰ You can set up calendar integration later from the dashboard")

def setup_notifications():
    """Configure notification services"""
    print(f"\n{Fore.CYAN}📱 Notification Setup")
    
    # Check Twilio for SMS
    if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
        print(f"{Fore.GREEN}✓ Twilio configured for SMS")
    else:
        print(f"{Fore.YELLOW}⚠️  Twilio not configured - SMS reminders disabled")
        print("   Get credentials at: https://www.twilio.com/try-twilio")
    
    # Check SendGrid for email
    if os.getenv('SENDGRID_API_KEY'):
        print(f"{Fore.GREEN}✓ SendGrid configured for email")
    else:
        print(f"{Fore.YELLOW}⚠️  SendGrid not configured - using console email (dev only)")
        print("   Get credentials at: https://sendgrid.com/free/")
    
    return True

def create_welcome_reminders(user_id):
    """Create initial welcome reminders"""
    conn = sqlite3.connect('database/credstack.db')
    cursor = conn.cursor()
    
    # Get current date
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # Welcome reminder for tomorrow
    cursor.execute('''
        INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'welcome', (today + timedelta(days=1)).strftime('%Y-%m-%d'),
          'Welcome to CredStack! Today: Add your first credit card account.'))
    
    # Statement date reminder for 3 days from now
    cursor.execute('''
        INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'task', (today + timedelta(days=3)).strftime('%Y-%m-%d'),
          'Find your credit card statement closing dates and add them to CredStack.'))
    
    # Weekly check for Friday
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    
    cursor.execute('''
        INSERT INTO reminders (user_id, reminder_type, reminder_date, message)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'weekly', (today + timedelta(days=days_until_friday)).strftime('%Y-%m-%d'),
          'Weekly Credit Check: Log in to review your balances.'))
    
    conn.commit()
    conn.close()
    
    print(f"{Fore.GREEN}✓ Welcome reminders created")

def main():
    """Main setup function"""
    print_banner()
    
    print(f"{Fore.CYAN}🔍 Running pre-flight checks...")
    check_python_version()
    
    print(f"\n{Fore.CYAN}🗄️  Initializing database...")
    create_database()
    
    print(f"\n{Fore.CYAN}👤 Creating your profile...")
    user_id = setup_user()
    
    print(f"\n{Fore.CYAN}⚙️  Setting up automations...")
    automations = setup_automations(user_id)
    
    print(f"\n{Fore.CYAN}📅 Configuring calendar...")
    setup_calendar()
    
    print(f"\n{Fore.CYAN}📱 Setting up notifications...")
    setup_notifications()
    
    print(f"\n{Fore.CYAN}🎯 Creating your first reminders...")
    create_welcome_reminders(user_id)
    
    # Final success message
    print(f"""
{Fore.GREEN}{'='*60}
{Fore.YELLOW}🎉 Setup Complete! Your CredStack is now running.
{Fore.GREEN}{'='*60}

{Fore.CYAN}Next Steps:
{Fore.WHITE}1. Start the Flask app: {Fore.YELLOW}python app.py
{Fore.WHITE}2. Open your browser to: {Fore.YELLOW}http://localhost:5000
{Fore.WHITE}3. Log in with your email: {Fore.YELLOW}{automations[0] if automations else 'your-email@example.com'}
{Fore.WHITE}4. Add your credit card accounts in the dashboard
{Fore.WHITE}5. Your first reminder will arrive tomorrow!

{Fore.CYAN}Need help?
{Fore.WHITE}• Check the README.md file
{Fore.WHITE}• Run {Fore.YELLOW}python app.py --help{Fore.WHITE} for options
{Fore.WHITE}• Visit the dashboard for documentation

{Fore.GREEN}{'='*60}
{Fore.MAGENTA}Remember: Credit repair is a marathon, not a sprint.
You've just automated the hardest part - consistency!
{Fore.GREEN}{'='*60}{Fore.RESET}
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Setup cancelled. Run 'python setup.py' to start over.")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}✗ Setup failed: {e}")
        sys.exit(1)
