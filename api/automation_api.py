"""
Automation Rules API Endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import auth
import database

automation_ns = Namespace('automation', description='Automation rules management')

# Models
automation_rule_model = automation_ns.model('AutomationRule', {
    'id': fields.Integer(readonly=True, description='Rule ID'),
    'user_id': fields.Integer(readonly=True, description='User ID'),
    'automation_type': fields.String(description='Type of automation', example='statement_alert'),
    'is_active': fields.Boolean(description='Whether rule is active', example=True),
    'configuration': fields.String(description='Rule configuration/description'),
    'created_at': fields.String(readonly=True, description='Created timestamp'),
    'last_run': fields.String(description='Last execution timestamp'),
})

automation_create_model = automation_ns.model('AutomationCreate', {
    'type': fields.String(required=True, description='Automation type', example='weekly_scan'),
    'configuration': fields.String(description='Configuration details', example='Scan every Friday at 9 AM'),
})

automation_update_model = automation_ns.model('AutomationUpdate', {
    'is_active': fields.Boolean(description='Enable or disable rule', example=True),
    'configuration': fields.String(description='Update configuration'),
})

automation_created_response = automation_ns.model('AutomationCreated', {
    'id': fields.Integer(description='Rule ID'),
    'message': fields.String(description='Success message'),
})

success_response = automation_ns.model('Success', {
    'message': fields.String(description='Success message'),
})


@automation_ns.route('/rules')
class AutomationRuleList(Resource):
    @automation_ns.doc('list_automation_rules',
                       description='Get all automation rules for current user',
                       security='Bearer',
                       params={
                           'active_only': 'Show only active rules (true/false)',
                           'page': 'Page number (default: 1)',
                           'per_page': 'Items per page (default: 20, max: 100)',
                       },
                       responses={
                           200: ('Success', [automation_rule_model]),
                           401: 'Unauthorized',
                       })
    @automation_ns.marshal_list_with(automation_rule_model)
    @auth.token_required
    def get(self):
        """List all automation rules for current user"""
        user_id = request.user_id
        
        # Get query parameters
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        offset = (page - 1) * per_page
        
        # Build query
        query = 'SELECT id, user_id, automation_type, is_active, configuration, created_at, last_run FROM automations WHERE user_id = ?'
        params = [user_id]
        
        if active_only:
            query += ' AND is_active = 1'
        
        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        conn = database.get_db()
        automations = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(a) for a in automations]
    
    @automation_ns.doc('create_automation_rule',
                       description='Create a new automation rule',
                       security='Bearer',
                       responses={
                           201: ('Rule created', automation_created_response),
                           400: 'Validation error',
                           401: 'Unauthorized',
                       })
    @automation_ns.expect(automation_create_model)
    @automation_ns.marshal_with(automation_created_response, code=201)
    @auth.token_required
    def post(self):
        """Create a new automation rule"""
        user_id = request.user_id
        data = request.json
        
        automation_type = data.get('type')
        configuration = data.get('configuration')
        
        if not automation_type:
            automation_ns.abort(400, 'Automation type is required')
        
        # Validate automation type
        valid_types = [
            'autopay_reminder',
            'statement_alert',
            'monthly_report',
            'weekly_scan',
            'dispute_tracker',
            'credit_builder',
            'inquiry_alert',
            'monthly_task'
        ]
        if automation_type not in valid_types:
            automation_ns.abort(400, f'Invalid automation type. Must be one of: {", ".join(valid_types)}')
        
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO automations (user_id, automation_type, configuration, is_active)
            VALUES (?, ?, ?, 1)
        ''', (user_id, automation_type, configuration))
        auto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': auto_id,
            'message': 'Automation rule created successfully'
        }, 201


@automation_ns.route('/rules/<int:rule_id>')
@automation_ns.param('rule_id', 'Automation rule ID')
class AutomationRuleDetail(Resource):
    @automation_ns.doc('get_automation_rule',
                       description='Get a specific automation rule',
                       security='Bearer',
                       responses={
                           200: ('Success', automation_rule_model),
                           401: 'Unauthorized',
                           404: 'Rule not found',
                       })
    @automation_ns.marshal_with(automation_rule_model)
    @auth.token_required
    def get(self, rule_id):
        """Get automation rule by ID"""
        user_id = request.user_id
        
        conn = database.get_db()
        rule = conn.execute('''
            SELECT * FROM automations WHERE id = ? AND user_id = ?
        ''', (rule_id, user_id)).fetchone()
        conn.close()
        
        if not rule:
            automation_ns.abort(404, 'Automation rule not found')
        
        return dict(rule)
    
    @automation_ns.doc('update_automation_rule',
                       description='Update an automation rule',
                       security='Bearer',
                       responses={
                           200: ('Rule updated', success_response),
                           401: 'Unauthorized',
                           404: 'Rule not found',
                       })
    @automation_ns.expect(automation_update_model)
    @automation_ns.marshal_with(success_response)
    @auth.token_required
    def put(self, rule_id):
        """Update automation rule"""
        user_id = request.user_id
        data = request.json
        
        # Verify ownership
        conn = database.get_db()
        rule = conn.execute('''
            SELECT * FROM automations WHERE id = ? AND user_id = ?
        ''', (rule_id, user_id)).fetchone()
        
        if not rule:
            conn.close()
            automation_ns.abort(404, 'Automation rule not found')
        
        is_active = data.get('is_active')
        configuration = data.get('configuration')
        
        # Use explicit UPDATE statements for security
        if is_active is not None and configuration is not None:
            conn.execute('''
                UPDATE automations SET is_active = ?, configuration = ?
                WHERE id = ? AND user_id = ?
            ''', (1 if is_active else 0, configuration, rule_id, user_id))
        elif is_active is not None:
            conn.execute('''
                UPDATE automations SET is_active = ?
                WHERE id = ? AND user_id = ?
            ''', (1 if is_active else 0, rule_id, user_id))
        elif configuration is not None:
            conn.execute('''
                UPDATE automations SET configuration = ?
                WHERE id = ? AND user_id = ?
            ''', (configuration, rule_id, user_id))
        else:
            conn.close()
            return {'message': 'No updates provided'}
        
        conn.commit()
        conn.close()
        
        return {'message': 'Automation rule updated successfully'}
    
    @automation_ns.doc('delete_automation_rule',
                       description='Delete an automation rule',
                       security='Bearer',
                       responses={
                           200: ('Rule deleted', success_response),
                           401: 'Unauthorized',
                           404: 'Rule not found',
                       })
    @automation_ns.marshal_with(success_response)
    @auth.token_required
    def delete(self, rule_id):
        """Delete automation rule"""
        user_id = request.user_id
        
        conn = database.get_db()
        
        # Verify ownership
        rule = conn.execute('''
            SELECT * FROM automations WHERE id = ? AND user_id = ?
        ''', (rule_id, user_id)).fetchone()
        
        if not rule:
            conn.close()
            automation_ns.abort(404, 'Automation rule not found')
        
        conn.execute('DELETE FROM automations WHERE id = ? AND user_id = ?', (rule_id, user_id))
        conn.commit()
        conn.close()
        
        return {'message': 'Automation rule deleted successfully'}
