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
    @users_ns.expect(user_update_model, validate=True)
    @users_ns.marshal_with(success_response)
    @auth.token_required
    def put(self):
        """Update user profile"""
        user_id = request.user_id
        data = request.json
        
        name = data.get('name')
        phone = data.get('phone')
        notification_preference = data.get('notification_preference')
        
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        
        if phone is not None:
            updates.append('phone = ?')
            params.append(phone)
        
        if notification_preference:
            valid_prefs = ['email', 'sms', 'both', 'calendar']
            if notification_preference not in valid_prefs:
                users_ns.abort(400, f'Invalid notification preference. Must be one of: {", ".join(valid_prefs)}')
            updates.append('notification_preference = ?')
            params.append(notification_preference)
        
        if not updates:
            return {'message': 'No updates provided'}
        
        params.append(user_id)
        conn = database.get_db()
        conn.execute(f'''
            UPDATE users SET {', '.join(updates)}
            WHERE id = ?
        ''', params)
        conn.commit()
        conn.close()
        
        return {'message': 'Profile updated successfully'}
