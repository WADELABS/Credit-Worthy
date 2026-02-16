"""
Test configuration and fixtures for pytest
"""
import pytest
from app import app as flask_app, limiter


@pytest.fixture(scope='session', autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for all tests"""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def app():
    """Create application for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    yield flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
