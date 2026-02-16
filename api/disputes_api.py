"""
Disputes API Endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from datetime import datetime, timedelta
import auth
import database

disputes_ns = Namespace('disputes', description='Credit dispute tracking')

# Models
dispute_model = disputes_ns.model('Dispute', {
    'id': fields.Integer(readonly=True, description='Dispute ID'),
    'user_id': fields.Integer(readonly=True, description='User ID'),
    'bureau': fields.String(description='Credit bureau (Experian, Equifax, TransUnion)', example='Experian'),
    'account_name': fields.String(description='Account name', example='Chase Credit Card'),
    'creditor': fields.String(description='Creditor name', example='Chase Bank'),
    'reason': fields.String(description='Dispute reason', example='Incorrect balance'),
    'dispute_date': fields.String(description='Dispute date'),
    'date_filed': fields.String(description='Date filed'),
    'follow_up_date': fields.String(description='Follow-up date'),
    'date_resolved': fields.String(description='Date resolved'),
    'status': fields.String(description='Status (pending, in_progress, resolved, rejected)', example='pending'),
    'outcome': fields.String(description='Outcome description'),
    'notes': fields.String(description='Additional notes'),
    'created_at': fields.String(readonly=True, description='Created timestamp'),
})

dispute_create_model = disputes_ns.model('DisputeCreate', {
    'bureau': fields.String(required=True, description='Credit bureau', example='Experian'),
    'creditor': fields.String(required=True, description='Creditor name', example='Chase Bank'),
    'account_name': fields.String(description='Account name', example='Chase Credit Card'),
    'reason': fields.String(description='Dispute reason', example='Incorrect balance'),
    'notes': fields.String(description='Additional notes'),
})

dispute_update_model = disputes_ns.model('DisputeUpdate', {
    'status': fields.String(
        description='Dispute status',
        enum=['pending', 'in_progress', 'resolved', 'rejected'],
        example='in_progress'
    ),
    'outcome': fields.String(description='Outcome description', example='Removed from report'),
    'notes': fields.String(description='Additional notes'),
})

dispute_created_response = disputes_ns.model('DisputeCreated', {
    'id': fields.Integer(description='Dispute ID'),
    'message': fields.String(description='Success message'),
    'follow_up_date': fields.String(description='Recommended follow-up date'),
})

success_response = disputes_ns.model('Success', {
    'message': fields.String(description='Success message'),
})


@disputes_ns.route('')
class DisputeList(Resource):
    @disputes_ns.doc('list_disputes',
                     description='Get all disputes for current user',
                     security='Bearer',
                     params={
                         'status': 'Filter by status (pending, in_progress, resolved, rejected)',
                         'page': 'Page number (default: 1)',
                         'per_page': 'Items per page (default: 20, max: 100)',
                     },
                     responses={
                         200: ('Success', [dispute_model]),
                         401: 'Unauthorized',
                     })
    @disputes_ns.marshal_list_with(dispute_model)
    @auth.token_required
    def get(self):
        """List all disputes for current user"""
        user_id = request.user_id
        
        # Get query parameters
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        offset = (page - 1) * per_page
        
        # Build query
        query = 'SELECT * FROM disputes WHERE user_id = ?'
        params = [user_id]
        
        if status_filter:
            valid_statuses = ['pending', 'in_progress', 'resolved', 'rejected']
            if status_filter not in valid_statuses:
                disputes_ns.abort(400, f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
            query += ' AND status = ?'
            params.append(status_filter)
        
        query += ' ORDER BY dispute_date DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        conn = database.get_db()
        disputes = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(d) for d in disputes]
    
    @disputes_ns.doc('create_dispute',
                     description='Create a new dispute',
                     security='Bearer',
                     responses={
                         201: ('Dispute created', dispute_created_response),
                         400: 'Validation error',
                         401: 'Unauthorized',
                     })
    @disputes_ns.expect(dispute_create_model)
    @disputes_ns.marshal_with(dispute_created_response, code=201)
    @auth.token_required
    def post(self):
        """Create a new dispute"""
        user_id = request.user_id
        data = request.json
        
        bureau = data.get('bureau')
        creditor = data.get('creditor')
        account_name = data.get('account_name')
        reason = data.get('reason')
        notes = data.get('notes')
        
        if not bureau or not creditor:
            disputes_ns.abort(400, 'Bureau and creditor are required')
        
        # Validate bureau
        valid_bureaus = ['Experian', 'Equifax', 'TransUnion']
        if bureau not in valid_bureaus:
            disputes_ns.abort(400, f'Invalid bureau. Must be one of: {", ".join(valid_bureaus)}')
        
        dispute_date = datetime.now().strftime('%Y-%m-%d')
        follow_up_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disputes 
            (user_id, bureau, account_name, creditor, reason, dispute_date, date_filed, follow_up_date, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (user_id, bureau, account_name, creditor, reason, dispute_date, dispute_date, follow_up_date, notes))
        dispute_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': dispute_id,
            'message': 'Dispute created successfully',
            'follow_up_date': follow_up_date
        }, 201


@disputes_ns.route('/<int:dispute_id>')
@disputes_ns.param('dispute_id', 'Dispute ID')
class DisputeDetail(Resource):
    @disputes_ns.doc('get_dispute',
                     description='Get a specific dispute',
                     security='Bearer',
                     responses={
                         200: ('Success', dispute_model),
                         401: 'Unauthorized',
                         404: 'Dispute not found',
                     })
    @disputes_ns.marshal_with(dispute_model)
    @auth.token_required
    def get(self, dispute_id):
        """Get dispute by ID"""
        user_id = request.user_id
        
        conn = database.get_db()
        dispute = conn.execute('''
            SELECT * FROM disputes WHERE id = ? AND user_id = ?
        ''', (dispute_id, user_id)).fetchone()
        conn.close()
        
        if not dispute:
            disputes_ns.abort(404, 'Dispute not found')
        
        return dict(dispute)
    
    @disputes_ns.doc('update_dispute',
                     description='Update a dispute',
                     security='Bearer',
                     responses={
                         200: ('Dispute updated', success_response),
                         401: 'Unauthorized',
                         404: 'Dispute not found',
                     })
    @disputes_ns.expect(dispute_update_model)
    @disputes_ns.marshal_with(success_response)
    @auth.token_required
    def put(self, dispute_id):
        """Update dispute"""
        user_id = request.user_id
        data = request.json
        
        # Verify ownership
        conn = database.get_db()
        dispute = conn.execute('''
            SELECT * FROM disputes WHERE id = ? AND user_id = ?
        ''', (dispute_id, user_id)).fetchone()
        
        if not dispute:
            conn.close()
            disputes_ns.abort(404, 'Dispute not found')
        
        status = data.get('status')
        outcome = data.get('outcome')
        notes = data.get('notes')
        
        # Validate status if provided
        if status:
            valid_statuses = ['pending', 'in_progress', 'resolved', 'rejected']
            if status not in valid_statuses:
                conn.close()
                disputes_ns.abort(400, f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
        
        # Determine if we need to set date_resolved
        date_resolved = None
        if status in ['resolved', 'rejected']:
            date_resolved = datetime.now().strftime('%Y-%m-%d')
        
        # Use explicit UPDATE statements for security
        # Handle all combinations of fields
        if not (status or outcome or notes is not None):
            conn.close()
            return {'message': 'No updates provided'}
        
        # Build the appropriate query based on what fields are being updated
        if status and outcome and notes is not None and date_resolved:
            conn.execute('''
                UPDATE disputes SET status = ?, outcome = ?, notes = ?, date_resolved = ?
                WHERE id = ? AND user_id = ?
            ''', (status, outcome, notes, date_resolved, dispute_id, user_id))
        elif status and outcome and date_resolved:
            conn.execute('''
                UPDATE disputes SET status = ?, outcome = ?, date_resolved = ?
                WHERE id = ? AND user_id = ?
            ''', (status, outcome, date_resolved, dispute_id, user_id))
        elif status and notes is not None and date_resolved:
            conn.execute('''
                UPDATE disputes SET status = ?, notes = ?, date_resolved = ?
                WHERE id = ? AND user_id = ?
            ''', (status, notes, date_resolved, dispute_id, user_id))
        elif outcome and notes is not None:
            conn.execute('''
                UPDATE disputes SET outcome = ?, notes = ?
                WHERE id = ? AND user_id = ?
            ''', (outcome, notes, dispute_id, user_id))
        elif status and date_resolved:
            conn.execute('''
                UPDATE disputes SET status = ?, date_resolved = ?
                WHERE id = ? AND user_id = ?
            ''', (status, date_resolved, dispute_id, user_id))
        elif status and outcome:
            conn.execute('''
                UPDATE disputes SET status = ?, outcome = ?
                WHERE id = ? AND user_id = ?
            ''', (status, outcome, dispute_id, user_id))
        elif status and notes is not None:
            conn.execute('''
                UPDATE disputes SET status = ?, notes = ?
                WHERE id = ? AND user_id = ?
            ''', (status, notes, dispute_id, user_id))
        elif status:
            conn.execute('''
                UPDATE disputes SET status = ?
                WHERE id = ? AND user_id = ?
            ''', (status, dispute_id, user_id))
        elif outcome and notes is not None:
            conn.execute('''
                UPDATE disputes SET outcome = ?, notes = ?
                WHERE id = ? AND user_id = ?
            ''', (outcome, notes, dispute_id, user_id))
        elif outcome:
            conn.execute('''
                UPDATE disputes SET outcome = ?
                WHERE id = ? AND user_id = ?
            ''', (outcome, dispute_id, user_id))
        elif notes is not None:
            conn.execute('''
                UPDATE disputes SET notes = ?
                WHERE id = ? AND user_id = ?
            ''', (notes, dispute_id, user_id))
        
        conn.commit()
        conn.close()
        
        return {'message': 'Dispute updated successfully'}
    
    @disputes_ns.doc('delete_dispute',
                     description='Delete a dispute',
                     security='Bearer',
                     responses={
                         200: ('Dispute deleted', success_response),
                         401: 'Unauthorized',
                         404: 'Dispute not found',
                     })
    @disputes_ns.marshal_with(success_response)
    @auth.token_required
    def delete(self, dispute_id):
        """Delete dispute"""
        user_id = request.user_id
        
        conn = database.get_db()
        
        # Verify ownership
        dispute = conn.execute('''
            SELECT * FROM disputes WHERE id = ? AND user_id = ?
        ''', (dispute_id, user_id)).fetchone()
        
        if not dispute:
            conn.close()
            disputes_ns.abort(404, 'Dispute not found')
        
        conn.execute('DELETE FROM disputes WHERE id = ? AND user_id = ?', (dispute_id, user_id))
        conn.commit()
        conn.close()
        
        return {'message': 'Dispute deleted successfully'}
