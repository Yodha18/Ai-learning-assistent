import urllib.request
import json

data = json.dumps({
    'full_name': 'Test User',
    'email': 'testuser@example.com',
    'password': 'TestPassword123',
    'course': 'CS',
    'semester': 1,
    'learning_goal': 'general',
    'daily_study_time': 120
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/register',
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print(f'Status: {response.status}')
        result = json.loads(response.read().decode())
        print(f'User created successfully!')
        print(f'User ID: {result.get("id")}')
        print(f'Email: {result.get("email")}')
except urllib.error.HTTPError as e:
    print(f'Status: {e.code}')
    body = e.read().decode()
    print(f'Response: {body}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
