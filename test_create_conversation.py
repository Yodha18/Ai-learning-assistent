import urllib.request
import json

# Read the access token
with open('access_token.txt', 'r') as f:
    token = f.read().strip()

# Create a new conversation
data = json.dumps({
    'subject_id': 1,  # Assuming subject exists
    'title': 'Test Chat'
}).encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/ai/conversations',
    data=data,
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
)

try:
    with urllib.request.urlopen(req) as response:
        print(f'Status: {response.status}')
        result = json.loads(response.read().decode())
        print(f'Conversation created successfully!')
        print(f'Conversation ID: {result.get("id")}')
        print(f'Title: {result.get("title")}')
        
        # Save conversation ID for WebSocket test
        with open('conversation_id.txt', 'w') as f:
            f.write(str(result.get("id")))
            
except urllib.error.HTTPError as e:
    print(f'Status: {e.code}')
    body = e.read().decode()
    print(f'Response: {body}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
