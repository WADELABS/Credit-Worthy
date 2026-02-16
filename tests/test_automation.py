"""
Automation and Scheduling Logic Tests
Tests for automation rules, scheduling, cron-like behavior, and error handling
"""
import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import automation
import database


class TestAutomation:
    """Tests for automation calculation functions"""
    
    def test_calculate_next_date_future(self):
        """Test calculation for a day later in the current month"""
        today = datetime.now()
        # If today is the 15th, target the 20th
        target_day = (today.day % 28) + 1
        if target_day <= today.day:
             # Force it to be in the next month for this test case if the logic requires
             pass 
        
        # Test basic calculation
        next_date = automation.calculate_next_date(target_day)
        assert next_date.day == target_day
        assert next_date >= today

    def test_calculate_next_date_rollover(self):
        """Test calculation when the day has already passed in the current month"""
        today = datetime.now()
        if today.day > 1:
            past_day = today.day - 1
            next_date = automation.calculate_next_date(past_day)
            
            # Should be next month
            expected_month = (today.month % 12) + 1
            assert next_date.month == expected_month
            assert next_date.day == past_day

    def test_leap_year_edge_case(self):
        """Test handling of 31st on shorter months"""
        # February doesn't have 31 days
        next_date = automation.calculate_next_date(31)
        # Should return the last day of the current or next month
        assert next_date.day in [28, 29, 30, 31]
    
    def test_calculate_next_date_with_months_ahead(self):
        """Test calculating date multiple months ahead"""
        next_date = automation.calculate_next_date(15, months_ahead=3)
        today = datetime.now()
        
        # Should be at least 3 months from now
        assert next_date > today + relativedelta(months=2)
    
    def test_calculate_next_date_day_1(self):
        """Test calculating for first day of month"""
        next_date = automation.calculate_next_date(1)
        assert next_date.day == 1
    
    def test_calculate_next_date_day_31(self):
        """Test calculating for 31st of month"""
        next_date = automation.calculate_next_date(31)
        # Should be valid date
        assert next_date.day in [28, 29, 30, 31]


class TestStatementAlerts:
    """Tests for statement alert generation"""
    
    def test_generate_statement_alert_creates_reminder(self, test_db, test_user):
        """Test that statement alert creates a reminder"""
        automation.generate_statement_alert(
            test_user['id'], 
            1, 
            'Test Card', 
            15  # statement day
        )
        
        # Verify reminder was created
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchall()
        conn.close()
        
        assert len(reminders) == 1
        assert 'Test Card' in reminders[0]['message']
        assert reminders[0]['reminder_type'] == 'automation'
    
    def test_generate_statement_alert_no_duplicates(self, test_db, test_user):
        """Test that duplicate alerts are not created"""
        # Create first alert
        automation.generate_statement_alert(
            test_user['id'], 
            1, 
            'Test Card', 
            15
        )
        
        # Try to create same alert again
        automation.generate_statement_alert(
            test_user['id'], 
            1, 
            'Test Card', 
            15
        )
        
        # Should still only have one
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_generate_statement_alert_uses_lead_time(self, test_db, test_user):
        """Test that alert uses configured lead time"""
        statement_day = 15
        automation.generate_statement_alert(
            test_user['id'], 
            1, 
            'Test Card', 
            statement_day
        )
        
        # Get the reminder
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        reminder = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()
        conn.close()
        
        # Verify lead time is mentioned in message
        assert reminder is not None
        assert 'days' in reminder['message'].lower()


class TestAutomationExecution:
    """Tests for automation execution and rule processing"""
    
    def test_run_all_automations_creates_alerts(self, test_db, test_user):
        """Test running all automations for a user"""
        # Create an account with statement date
        conn = sqlite3.connect(test_db)
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'Test Card', 'credit_card', 15))
        conn.commit()
        conn.close()
        
        # Run automations
        automation.run_all_automations(test_user['id'])
        
        # Verify reminders were created
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count >= 1
    
    def test_run_all_automations_multiple_accounts(self, test_db, test_user):
        """Test automation runs for multiple accounts"""
        # Create multiple accounts
        conn = sqlite3.connect(test_db)
        for i in range(3):
            conn.execute('''
                INSERT INTO accounts (user_id, name, account_type, statement_date)
                VALUES (?, ?, ?, ?)
            ''', (test_user['id'], f'Card {i}', 'credit_card', 10 + i))
        conn.commit()
        conn.close()
        
        # Run automations
        automation.run_all_automations(test_user['id'])
        
        # Verify reminders for all accounts
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count >= 3
    
    def test_run_all_automations_skips_no_statement_date(self, test_db, test_user):
        """Test automation skips accounts without statement dates"""
        # Create account without statement date
        conn = sqlite3.connect(test_db)
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (test_user['id'], 'No Date Card', 'credit_card'))
        conn.commit()
        conn.close()
        
        # Run automations
        automation.run_all_automations(test_user['id'])
        
        # Should not create reminders
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count == 0


class TestAutomatedReminders:
    """Tests for automated reminder creation"""
    
    def test_create_automated_reminder_basic(self, test_db, test_user):
        """Test creating a basic automated reminder"""
        automation.create_automated_reminder(
            test_user['id'],
            'custom',
            'Test reminder message',
            days_before=5
        )
        
        # Verify reminder
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        reminder = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()
        conn.close()
        
        assert reminder is not None
        assert reminder['message'] == 'Test reminder message'
        assert reminder['reminder_type'] == 'custom'
    
    def test_create_automated_reminder_with_reference_date(self, test_db, test_user):
        """Test creating reminder with monthly recurring date"""
        automation.create_automated_reminder(
            test_user['id'],
            'monthly',
            'Monthly reminder',
            days_before=3,
            reference_date=15  # 15th of month
        )
        
        # Verify reminder was created
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count == 1
    
    def test_create_automated_reminder_handles_month_end(self, test_db, test_user):
        """Test reminder creation handles end of month correctly"""
        # Test with 31st (not all months have 31 days)
        automation.create_automated_reminder(
            test_user['id'],
            'monthly',
            'End of month reminder',
            days_before=0,
            reference_date=31
        )
        
        # Should not raise an exception
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count == 1


class TestAutomationConfiguration:
    """Tests for automation configuration loading"""
    
    def test_load_config_returns_defaults(self):
        """Test config loading returns default values"""
        config = automation.load_config()
        
        assert config is not None
        assert 'automation' in config
        assert 'utilization' in config['automation']
    
    def test_config_has_utilization_settings(self):
        """Test config includes utilization settings"""
        config = automation.load_config()
        
        util_config = config['automation']['utilization']
        assert 'target_maximum' in util_config
        assert 'warning_threshold' in util_config
        assert 'neutralization_lead_time_days' in util_config
    
    def test_config_utilization_values_are_numeric(self):
        """Test config values are proper types"""
        config = automation.load_config()
        
        util_config = config['automation']['utilization']
        assert isinstance(util_config['target_maximum'], (int, float))
        assert isinstance(util_config['warning_threshold'], (int, float))
        assert isinstance(util_config['neutralization_lead_time_days'], int)
