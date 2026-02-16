"""
Users API Endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import auth
import database

users_ns = Namespace('users', description='User profile management')

# Models
user_profile_model = users_ns.model('UserProfile', {
    'id': fields.Integer(readonly=True, description='User ID'),
    'email': fields.String(description='User email'),
    'name': fields.String(description='User full name'),
    'phone': fields.String(description='Phone number'),
    'notification_preference': fields.String(description='Notification preference (email, sms, both, calendar)'),
    'automation_level': fields.String(description='Automation level (basic, advanced)'),
    'created_at': fields.String(description='Account creation date'),
    'last_login': fields.String(description='Last login date'),
})

user_update_model = users_ns.model('UserUpdate', {
    'name': fields.String(description='User full name', example='John Doe'),
    'phone': fields.String(description='Phone number', example='+15551234567'),
    'notification_preference': fields.String(
        description='Notification preference',
        enum=['email', 'sms', 'both', 'calendar'],
        example='email'
    ),
})

success_response = users_ns.model('Success', {
    'message': fields.String(description='Success message'),
})


@users_ns.route('/profile')
class UserProfile(Resource):
    @users_ns.doc('get_user_profile',
                  description='Get current user profile information',
                  security='Bearer',
                  responses={
                      200: ('Success', user_profile_model),
                      401: 'Unauthorized',
                      404: 'User not found',
                  })
    @users_ns.marshal_with(user_profile_model)
    @auth.token_required
    def get(self):
        """Get user profile"""
        user_id = request.user_id
        conn = database.get_db()
        
        user = conn.execute('''
            SELECT id, email, name, phone, notification_preference, 
                   automation_level, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,)).fetchone()
        conn.close()
        
        if not user:
            users_ns.abort(404, 'User not found')
        
        return dict(user)
    
    @users_ns.doc('update_user_profile',
                  description='Update current user profile',
                  security='Bearer',
                  responses={
                      200: ('Profile updated', success_response),
                      401: 'Unauthorized',
                  })
    @users_ns.expect(user_update_model)
    @users_ns.marshal_with(success_response)
    @auth.token_required
    def put(self):
        """Update user profile"""
        user_id = request.user_id
        data = request.json
        
        name = data.get('name')
        phone = data.get('phone')
        notification_preference = data.get('notification_preference')
        
        # Validate notification preference if provided
        if notification_preference:
            valid_prefs = ['email', 'sms', 'both', 'calendar']
            if notification_preference not in valid_prefs:
                users_ns.abort(400, f'Invalid notification preference. Must be one of: {", ".join(valid_prefs)}')
        
        conn = database.get_db()
        
        # Use explicit UPDATE statements for security
        if name is not None and phone is not None and notification_preference:
            conn.execute('''
                UPDATE users SET name = ?, phone = ?, notification_preference = ?
                WHERE id = ?
            ''', (name, phone, notification_preference, user_id))
        elif name is not None and phone is not None:
            conn.execute('''
                UPDATE users SET name = ?, phone = ?
                WHERE id = ?
            ''', (name, phone, user_id))
        elif name is not None and notification_preference:
            conn.execute('''
                UPDATE users SET name = ?, notification_preference = ?
                WHERE id = ?
            ''', (name, notification_preference, user_id))
        elif phone is not None and notification_preference:
            conn.execute('''
                UPDATE users SET phone = ?, notification_preference = ?
                WHERE id = ?
            ''', (phone, notification_preference, user_id))
        elif name is not None:
            conn.execute('UPDATE users SET name = ? WHERE id = ?', (name, user_id))
        elif phone is not None:
            conn.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
        elif notification_preference:
            conn.execute('UPDATE users SET notification_preference = ? WHERE id = ?', (notification_preference, user_id))
        else:
            conn.close()
            return {'message': 'No updates provided'}
        
        conn.commit()
        conn.close()
        
        return {'message': 'Profile updated successfully'}
