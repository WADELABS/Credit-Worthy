"""
API Module
Flask-RESTX API with Swagger documentation
"""

from flask import Blueprint
from flask_restx import Api

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Create API with documentation
api = Api(
    api_bp,
    version='1.0',
    title='CredStack API',
    description='Credit automation and dispute tracking API with multi-user support',
    doc='/docs',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Bearer token. Format: "Bearer {token}"'
        }
    },
    security='Bearer'
)

# Import namespaces
from api.auth_api import auth_ns
from api.users_api import users_ns
from api.disputes_api import disputes_ns
from api.automation_api import automation_ns
from api.credit_api import credit_ns

# Add namespaces
api.add_namespace(auth_ns, path='/v1/auth')
api.add_namespace(users_ns, path='/v1/users')
api.add_namespace(disputes_ns, path='/v1/disputes')
api.add_namespace(automation_ns, path='/v1/automation')
api.add_namespace(credit_ns, path='/v1/credit')
