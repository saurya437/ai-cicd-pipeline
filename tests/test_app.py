import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

def test_home_endpoint():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200

def test_health_endpoint():
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'healthy'