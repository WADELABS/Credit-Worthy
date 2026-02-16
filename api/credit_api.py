"""
Credit API Endpoints
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from datetime import datetime
import auth
import database

credit_ns = Namespace('credit', description='Credit information and accounts')

# Models
credit_account_model = credit_ns.model('CreditAccount', {
    'id': fields.Integer(readonly=True, description='Account ID'),
    'name': fields.String(description='Account name', example='Chase Freedom'),
    'account_type': fields.String(description='Account type (credit_card, loan, mortgage)', example='credit_card'),
    'balance': fields.Float(description='Current balance', example=500.00),
    'credit_limit': fields.Float(description='Credit limit', example=5000.00),
    'statement_date': fields.Integer(description='Statement closing day (1-31)', example=15),
    'due_date': fields.Integer(description='Payment due day (1-31)', example=25),
    'last_updated': fields.String(readonly=True, description='Last update timestamp'),
})

credit_score_model = credit_ns.model('CreditScore', {
    'score': fields.Integer(description='Estimated credit score (simplified calculation)'),
    'utilization': fields.Float(description='Credit utilization percentage'),
    'date': fields.String(description='Calculation date'),
    'accounts_count': fields.Integer(description='Number of accounts'),
})


@credit_ns.route('/score')
class CreditScore(Resource):
    @credit_ns.doc('get_credit_score',
                   description='Get estimated credit score based on utilization',
                   security='Bearer',
                   responses={
                       200: ('Success', credit_score_model),
                       401: 'Unauthorized',
                   })
    @credit_ns.marshal_with(credit_score_model)
    @auth.token_required
    def get(self):
        """Get estimated credit score"""
        user_id = request.user_id
        
        conn = database.get_db()
        accounts = conn.execute('''
            SELECT balance, credit_limit FROM accounts 
            WHERE user_id = ? AND account_type = 'credit_card' AND credit_limit > 0
        ''', (user_id,)).fetchall()
        conn.close()
        
        # Calculate utilization and score (simplified)
        score = 0
        utilization = 0
        
        if accounts:
            total_balance = sum(float(a['balance'] or 0) for a in accounts)
            total_limit = sum(float(a['credit_limit'] or 0) for a in accounts)
            
            if total_limit > 0:
                utilization = (total_balance / total_limit) * 100
                
                # Simplified score calculation based on utilization
                if utilization < 10:
                    score = 780
                elif utilization < 30:
                    score = 720
                elif utilization < 50:
                    score = 680
                elif utilization < 70:
                    score = 650
                else:
                    score = 600
        
        return {
            'score': score,
            'utilization': round(utilization, 2),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'accounts_count': len(accounts)
        }


@credit_ns.route('/accounts')
class CreditAccountList(Resource):
    @credit_ns.doc('list_credit_accounts',
                   description='Get all credit accounts for current user',
                   security='Bearer',
                   params={
                       'account_type': 'Filter by account type (credit_card, loan, mortgage)',
                       'page': 'Page number (default: 1)',
                       'per_page': 'Items per page (default: 20, max: 100)',
                   },
                   responses={
                       200: ('Success', [credit_account_model]),
                       401: 'Unauthorized',
                   })
    @credit_ns.marshal_list_with(credit_account_model)
    @auth.token_required
    def get(self):
        """List all credit accounts"""
        user_id = request.user_id
        
        # Get query parameters
        account_type = request.args.get('account_type')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        offset = (page - 1) * per_page
        
        # Build query
        query = 'SELECT id, name, account_type, balance, credit_limit, statement_date, due_date, last_updated FROM accounts WHERE user_id = ?'
        params = [user_id]
        
        if account_type:
            valid_types = ['credit_card', 'loan', 'mortgage']
            if account_type not in valid_types:
                credit_ns.abort(400, f'Invalid account type. Must be one of: {", ".join(valid_types)}')
            query += ' AND account_type = ?'
            params.append(account_type)
        
        query += ' ORDER BY account_type, name LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        conn = database.get_db()
        accounts = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(a) for a in accounts]
