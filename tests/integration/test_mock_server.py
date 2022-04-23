import requests
import pytest


def test_mock_server_status():
    response = requests.put("http://mockserver:1080/mockserver/status")
    assert response.status_code == 200

def test_mock_request():
    response = requests.get("http://mockserver:1080/ping")
    assert response.status_code == 404
    result = requests.put("http://mockserver:1080/mockserver/expectation", json={
        'httpRequest': {
            'method': 'GET',
            'path': '/ping'
        },
        'httpResponse': {
            'statusCode': 200,
            'headers': [
                {
                    'name': 'Content-Type',
                    'values': ['application/json; charset=utf-8']
                }
            ],
            'body': 'pong'
        }
    })
    response = requests.get("http://mockserver:1080/ping")
    assert response.status_code == 200
    response = requests.put("http://mockserver:1080/mockserver/reset")
    assert response.status_code == 200
