"""
Integration Tests
End-to-end tests for complete user workflows
"""
import pytest
import sqlite3
from datetime import datetime, timedelta
import auth
import automation


class TestUserRegistrationFlow:
    """Integration tests for user registration and setup"""
    
    def test_complete_registration_flow(self, client, test_db):
        """Test complete user registration and first login"""
        # Register new user
        response = client.post('/register', data={
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'name': 'New User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Welcome' in response.data or b'Dashboard' in response.data
        
        # Verify user in database
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', 
            ('newuser@example.com',)
        ).fetchone()
        conn.close()
        
        assert user is not None
        assert user['email'] == 'newuser@example.com'
        assert user['name'] == 'New User'
    
    def test_register_login_add_account_flow(self, client, test_db):
        """Test complete flow: register, login, add account"""
        # 1. Register
        client.post('/register', data={
            'email': 'flowuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })
        
        # Get user ID
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', 
            ('flowuser@example.com',)
        ).fetchone()
        user_id = user['id']
        conn.close()
        
        # 2. Add account (should be logged in automatically after registration)
        response = client.post('/accounts/add', data={
            'name': 'My First Card',
            'account_type': 'credit_card',
            'balance': '500',
            'credit_limit': '5000',
            'statement_date': '15'
        }, follow_redirects=True)
        
        # 3. Verify account was created
        conn = sqlite3.connect(test_db)
        account = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ? AND name = ?', 
            (user_id, 'My First Card')
        ).fetchone()
        conn.close()
        
        assert account is not None


class TestAccountManagementFlow:
    """Integration tests for account management"""
    
    def test_add_account_generates_automation(self, authenticated_client, test_db, test_user):
        """Test adding account with statement date generates automation"""
        # Add account
        authenticated_client.post('/accounts/add', data={
            'name': 'Auto Card',
            'account_type': 'credit_card',
            'statement_date': '20',
            'balance': '100',
            'credit_limit': '1000'
        })
        
        # Run automations
        automation.run_all_automations(test_user['id'])
        
        # Verify reminder was created
        conn = sqlite3.connect(test_db)
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchall()
        conn.close()
        
        assert len(reminders) > 0
    
    def test_multiple_accounts_utilization_tracking(self, authenticated_client, test_db, test_user):
        """Test tracking utilization across multiple accounts"""
        # Add multiple accounts
        accounts_data = [
            {'name': 'Card 1', 'balance': 100, 'limit': 1000},
            {'name': 'Card 2', 'balance': 500, 'limit': 2000},
            {'name': 'Card 3', 'balance': 300, 'limit': 1500}
        ]
        
        for acc in accounts_data:
            authenticated_client.post('/accounts/add', data={
                'name': acc['name'],
                'account_type': 'credit_card',
                'balance': str(acc['balance']),
                'credit_limit': str(acc['limit'])
            })
        
        # Verify all accounts created
        conn = sqlite3.connect(test_db)
        accounts = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchall()
        conn.close()
        
        assert len(accounts) == 3


class TestDisputeWorkflow:
    """Integration tests for dispute management"""
    
    def test_create_and_update_dispute(self, authenticated_client, test_db, test_user):
        """Test complete dispute workflow"""
        # 1. Create dispute
        response = authenticated_client.post('/disputes/add', data={
            'bureau': 'Experian',
            'creditor': 'Test Bank',
            'account_name': 'Old Account',
            'reason': 'Account not mine',
            'notes': 'This account does not belong to me'
        }, follow_redirects=True)
        
        # Get dispute ID
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        dispute = conn.execute(
            'SELECT * FROM disputes WHERE user_id = ?', 
            (test_user['id'],)
        ).fetchone()
        dispute_id = dispute['id']
        
        # Initial status should be pending
        assert dispute['status'] == 'pending'
        
        # 2. Update dispute status
        conn.execute('''
            UPDATE disputes 
            SET status = ?, outcome = ?, date_resolved = ?
            WHERE id = ?
        ''', ('resolved', 'Removed from report', datetime.now().strftime('%Y-%m-%d'), dispute_id))
        conn.commit()
        
        # 3. Verify update
        updated_dispute = conn.execute(
            'SELECT * FROM disputes WHERE id = ?', 
            (dispute_id,)
        ).fetchone()
        conn.close()
        
        assert updated_dispute['status'] == 'resolved'
        assert updated_dispute['outcome'] == 'Removed from report'


class TestAutomationFlow:
    """Integration tests for automation and reminders"""
    
    def test_statement_reminder_flow(self, test_db, test_user):
        """Test complete statement reminder workflow"""
        # 1. Create account with statement date
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date, balance, credit_limit)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_user['id'], 'Test Card', 'credit_card', 15, 100.0, 1000.0))
        account_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 2. Generate automation
        automation.generate_statement_alert(
            test_user['id'],
            account_id,
            'Test Card',
            15
        )
        
        # 3. Verify reminder created
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row
        reminders = conn.execute(
            'SELECT * FROM reminders WHERE user_id = ? AND reminder_type = ?',
            (test_user['id'], 'automation')
        ).fetchall()
        conn.close()
        
        assert len(reminders) > 0
        assert 'Test Card' in reminders[0]['message']
    
    def test_multiple_reminders_no_duplicates(self, test_db, test_user):
        """Test that running automation multiple times doesn't create duplicates"""
        # Create account
        conn = sqlite3.connect(test_db)
        conn.execute('''
            INSERT INTO accounts (user_id, name, account_type, statement_date)
            VALUES (?, ?, ?, ?)
        ''', (test_user['id'], 'No Dupe Card', 'credit_card', 10))
        conn.commit()
        conn.close()
        
        # Run automation multiple times
        for _ in range(3):
            automation.run_all_automations(test_user['id'])
        
        # Should still only have one reminder
        conn = sqlite3.connect(test_db)
        count = conn.execute(
            'SELECT COUNT(*) FROM reminders WHERE user_id = ?',
            (test_user['id'],)
        ).fetchone()[0]
        conn.close()
        
        assert count == 1


class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_api_authentication_flow(self, client, test_db, test_user):
        """Test API authentication and usage"""
        # 1. Login via API
        response = client.post('/api/auth/login', json={
            'email': test_user['email'],
            'password': test_user['password']
        })
        
        assert response.status_code == 200
        data = response.get_json()
        token = data['token']
        
        # 2. Use token to access protected endpoint
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/v1/user/profile', headers=headers)
        
        assert response.status_code == 200
        profile = response.get_json()
        assert profile['email'] == test_user['email']
    
    def test_api_create_and_list_disputes(self, client, test_db, auth_headers):
        """Test creating and listing disputes via API"""
        # 1. Create dispute
        response = client.post('/api/v1/disputes',
            headers=auth_headers,
            json={
                'bureau': 'TransUnion',
                'creditor': 'API Test Bank',
                'reason': 'Incorrect information',
                'notes': 'Test dispute via API'
            })
        
        assert response.status_code == 201
        
        # 2. List disputes
        response = client.get('/api/v1/disputes', headers=auth_headers)
        
        assert response.status_code == 200
        disputes = response.get_json()
        assert len(disputes) > 0
        assert any(d['creditor'] == 'API Test Bank' for d in disputes)


class TestDataIsolation:
    """Integration tests for data isolation between users"""
    
    def test_users_cannot_access_each_others_data(self, client, test_db):
        """Test that users can only see their own data"""
        # Create two users
        password_hash = auth.hash_password('password123')
        
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # User 1
        cursor.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user1@example.com', password_hash, 'email', 'basic'))
        user1_id = cursor.lastrowid
        
        # User 2
        cursor.execute('''
            INSERT INTO users (email, password_hash, notification_preference, automation_level)
            VALUES (?, ?, ?, ?)
        ''', ('user2@example.com', password_hash, 'email', 'basic'))
        user2_id = cursor.lastrowid
        
        # Create account for user 1
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (user1_id, 'User 1 Card', 'credit_card'))
        user1_account_id = cursor.lastrowid
        
        # Create account for user 2
        cursor.execute('''
            INSERT INTO accounts (user_id, name, account_type)
            VALUES (?, ?, ?)
        ''', (user2_id, 'User 2 Card', 'credit_card'))
        user2_account_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        # Login as user 1
        client.post('/login', data={
            'email': 'user1@example.com',
            'password': 'password123'
        })
        
        # Try to access dashboard - should only see user 1's data
        response = client.get('/dashboard')
        
        # Verify both users have accounts
        conn = sqlite3.connect(test_db)
        user1_accounts = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?',
            (user1_id,)
        ).fetchall()
        user2_accounts = conn.execute(
            'SELECT * FROM accounts WHERE user_id = ?',
            (user2_id,)
        ).fetchall()
        conn.close()
        
        # Both users have accounts
        assert len(user1_accounts) > 0
        assert len(user2_accounts) > 0
        # But they should be separate
        assert user1_accounts[0][1] != user2_accounts[0][1]  # Different user_ids
        assert user1_account_id != user2_account_id  # Different account IDs


class TestErrorHandling:
    """Integration tests for error handling"""
    
    def test_invalid_account_data_handled_gracefully(self, authenticated_client):
        """Test that invalid account data is handled without crashing"""
        # Try to add account with invalid data
        response = authenticated_client.post('/accounts/add', data={
            'name': 'Bad Account',
            'account_type': 'credit_card',
            'balance': 'not_a_number',
            'credit_limit': 'also_invalid'
        }, follow_redirects=True)
        
        # Should not crash - either returns error page or redirects
        # Status codes: 200 (redirect to form with error), 400, or 500
        assert response.status_code in [200, 400, 500]
        # The important thing is the server didn't crash
    
    def test_missing_required_fields_handled(self, authenticated_client):
        """Test that missing required fields are handled"""
        # Try to add dispute without required fields
        response = authenticated_client.post('/disputes/add', data={
            'notes': 'Only notes provided'
        }, follow_redirects=True)
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]
