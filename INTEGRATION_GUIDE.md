# AI Tutor Online Chat - Quick Integration Guide

## For Developers

### Step 1: Backend Setup

No additional setup needed! The WebSocket endpoint is already integrated into `app/routers/ai_tutor.py`.

Just ensure your FastAPI app is running:

```bash
python run_dev.py
# or
python -m uvicorn app.main:app --reload
```

### Step 2: Add Chat to Your Page

```html
<!-- Add these to your HTML page -->

<!-- Include CSS -->
<link rel="stylesheet" href="/static/css/ai-tutor-chat.css">

<!-- Include JavaScript -->
<script src="/static/js/ai-tutor-client.js"></script>
<script src="/static/js/ai-tutor-ui.js"></script>

<!-- Add chat container -->
<div class="chat-container">
    <div class="chat-header">
        <h1>AI Tutor</h1>
        <div class="connection-status">
            <div id="connection-status">● Offline</div>
            <div id="active-users"></div>
        </div>
    </div>
    
    <div id="chat-messages"></div>
    
    <div class="chat-input-area">
        <textarea 
            id="message-input" 
            placeholder="Ask me anything..."
            rows="1"
        ></textarea>
        <button id="send-button">Send</button>
    </div>
</div>

<!-- Initialize chat -->
<script>
    const chat = new AITutorUI();
    chat.connect({{ conversation_id }}, '{{ access_token }}');
    
    document.getElementById('send-button').onclick = () => {
        const msg = document.getElementById('message-input').value;
        if (msg.trim()) chat.sendMessage(msg);
    };
    
    document.getElementById('message-input').onkeypress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const msg = e.target.value.trim();
            if (msg) chat.sendMessage(msg);
        }
    };
</script>
```

### Step 3: Get Access Token

Make sure users are authenticated and have access tokens:

```html
<!-- In your Jinja2 template -->
<div data-token="{{ access_token }}" style="display:none;"></div>

<!-- Or in your JavaScript -->
<script>
    const accessToken = localStorage.getItem('access_token');
    const conversationId = {{ conversation_id }};
</script>
```

### Step 4: Handle Events (Optional)

```javascript
const chat = new AITutorUI();

// Listen to connection events
chat.client.on('open', () => {
    console.log('Connected!');
    // Show success message
});

chat.client.on('close', () => {
    console.log('Disconnected!');
    // Show warning
});

chat.client.on('message', (data) => {
    console.log('New message:', data);
    // Custom handling
});

chat.client.on('error', (data) => {
    console.error('Error:', data);
    // Handle error
});

chat.client.on('userOnline', (data) => {
    console.log(data.full_name, 'is online');
});

chat.client.on('userOffline', (data) => {
    console.log(data.full_name, 'went offline');
});

// Connect
chat.connect(conversationId, accessToken);
```

## Common Tasks

### Send a Message
```javascript
chat.sendMessage('Hello, AI!');
```

### Show Typing Status
```javascript
// User started typing
chat.client.startTyping();

// User stopped typing
chat.client.stopTyping();
```

### Get Active Users
```javascript
chat.client.getActiveUsers();

chat.client.on('activeUsers', (data) => {
    console.log('Active users:', data.users);
});
```

### Check Connection Status
```javascript
const status = chat.getStatus();
console.log(status);
// {
//   isConnected: true,
//   conversationId: 1,
//   queuedMessages: 0,
//   reconnectAttempts: 0
// }
```

### Disconnect
```javascript
chat.disconnect();
```

## API Response Examples

### Message Response
```json
{
    "type": "message",
    "role": "assistant",
    "content": "The answer is...",
    "sources": ["document1.pdf", "chapter2"],
    "message_id": 123,
    "timestamp": "2024-01-01T12:00:00"
}
```

### Error Response
```json
{
    "type": "error",
    "message": "Failed to generate response"
}
```

### User Status Response
```json
{
    "type": "user_online",
    "user_id": 5,
    "full_name": "John Doe",
    "active_users": [5, 6, 7]
}
```

## Testing in Browser

```javascript
// Open browser console (F12)

// Create chat instance
const chat = new AITutorUI();

// Connect (replace with real token)
chat.connect(1, 'your_access_token_here');

// Check status
console.log(chat.getStatus());

// Send message
chat.sendMessage('Hello AI!');

// Listen to messages
chat.client.on('message', (msg) => console.log(msg));
```

## Troubleshooting

### WebSocket Connection Fails
```javascript
// Check if WebSocket is supported
console.log('WebSocket supported:', 'WebSocket' in window);

// Check network tab in browser DevTools
// Look for WebSocket upgrade request

// Verify token
console.log('Token valid:', token.length > 0);
```

### Messages Not Appearing
```javascript
// Check connection status
console.log(chat.client.isConnected);

// Check message queue
console.log(chat.client.messageQueue);

// Monitor network requests
// Look for WebSocket messages in browser DevTools
```

### Reconnection Loop
```javascript
// Check server logs for authentication errors
// Verify token is still valid
// Check server WebSocket endpoint availability

// Use different reconnection settings
const chat = new AITutorUI({
    chatConfig: {
        reconnectAttempts: 3,
        reconnectDelay: 5000
    }
});
```

## Advanced: Custom UI

```javascript
// Create your own UI with basic client
const client = new AITutorChatClient({
    protocol: 'wss',
    host: 'api.example.com'
});

client.on('message', (data) => {
    // Update your custom UI here
    if (data.role === 'user') {
        document.querySelector('#messages').innerHTML += 
            `<div class="user-msg">${data.content}</div>`;
    } else {
        document.querySelector('#messages').innerHTML += 
            `<div class="ai-msg">${data.content}</div>`;
    }
});

client.connect(conversationId, accessToken);

// Send message
document.querySelector('#send').onclick = () => {
    client.sendMessage(document.querySelector('#input').value);
};
```

## Production Deployment

### Security Checklist
- [ ] Use HTTPS/WSS in production
- [ ] Validate tokens server-side
- [ ] Implement rate limiting
- [ ] Add CORS headers
- [ ] Use environment variables for configuration
- [ ] Monitor WebSocket connections
- [ ] Log all errors
- [ ] Regular security updates

### Performance Checklist
- [ ] Enable WebSocket compression
- [ ] Implement message pagination
- [ ] Cache conversation metadata
- [ ] Monitor memory usage
- [ ] Set connection timeout
- [ ] Implement connection pooling
- [ ] Optimize database queries

### Configuration Example
```python
# app/config.py
class Settings(BaseSettings):
    # WebSocket
    WS_MAX_CONNECTIONS_PER_USER: int = 5
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Security
    WS_MAX_MESSAGE_SIZE: int = 65536
    WS_INACTIVITY_TIMEOUT: int = 3600
    
    # Performance
    WS_ENABLE_COMPRESSION: bool = True
```

## Example: Full Page Implementation

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI Tutor Chat</title>
    <link rel="stylesheet" href="/static/css/ai-tutor-chat.css">
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>AI Tutor</h1>
            <div class="connection-status">
                <div id="connection-status">● Offline</div>
                <div id="active-users"></div>
            </div>
        </div>
        <div id="chat-messages"></div>
        <div class="chat-input-area">
            <textarea id="message-input" placeholder="Ask me..."></textarea>
            <button id="send-button">Send</button>
        </div>
    </div>

    <script src="/static/js/ai-tutor-client.js"></script>
    <script src="/static/js/ai-tutor-ui.js"></script>
    <script>
        const chat = new AITutorUI();
        const token = document.querySelector('[data-token]')?.dataset.token || 
                     localStorage.getItem('access_token');
        
        if (token) {
            chat.connect(1, token);
            
            document.getElementById('send-button').onclick = () => {
                const text = document.getElementById('message-input').value;
                if (text.trim()) chat.sendMessage(text);
            };
        } else {
            alert('Please login first');
        }
    </script>
</body>
</html>
```

## Getting Help

1. **Documentation**: Read `ONLINE_CHAT.md` for comprehensive docs
2. **Examples**: Check `app/templates/ai_tutor_chat.html`
3. **API Docs**: Visit `/docs` endpoint while server is running
4. **Logs**: Check server console for errors
5. **Browser DevTools**: Use Network and Console tabs

## What's Next?

1. ✅ WebSocket real-time chat
2. ✅ Typing indicators
3. ✅ Online status
4. 🔜 Message search
5. 🔜 File sharing
6. 🔜 Voice/video
7. 🔜 Encryption

## Support

Questions or issues? 
- Check the documentation files
- Review the API reference
- Check browser DevTools for errors
- Review server logs

---

**Happy coding! 🚀**
