import urllib.request
import json

data = json.dumps({
    'email': 'testuser@example.com',
    'password': 'TestPassword123'
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/auth/login',
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        print(f'Status: {response.status}')
        result = json.loads(response.read().decode())
        print(f'Login successful!')
        print(f'Access Token: {result.get("access_token")}')
        print(f'User ID: {result.get("user_id")}')
        
        # Save token to file for later use
        with open('access_token.txt', 'w') as f:
            f.write(result.get("access_token"))
            
except urllib.error.HTTPError as e:
    print(f'Status: {e.code}')
    body = e.read().decode()
    print(f'Response: {body}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
