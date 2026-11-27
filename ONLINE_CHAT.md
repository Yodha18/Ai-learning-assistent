# AI Tutor - Real-time Online Chat Documentation

## Overview

The AI Tutor now supports real-time online chat using WebSocket connections. This enables:

- **Real-time messaging** - Instant message delivery
- **Typing indicators** - See when others are typing
- **Online status** - Know who's currently online
- **Live updates** - No need to refresh to see new messages
- **Connection management** - Automatic reconnection on disconnection
- **Backward compatibility** - Existing REST API still works

## Architecture

### Components

1. **Backend (FastAPI + SQLAlchemy)**
   - WebSocket endpoint for real-time communication
   - Connection manager for handling multiple clients
   - Message broadcasting system
   - Automatic reconnection support

2. **Frontend (JavaScript)**
   - `AITutorChatClient` - WebSocket communication
   - `AITutorUI` - UI interaction controller
   - Event-driven architecture
   - Automatic message queuing

3. **Styles**
   - Modern chat UI with Material Design
   - Responsive for mobile and desktop
   - Smooth animations and transitions

## Installation

### Backend Setup

No additional packages needed! WebSocket support is built into FastAPI.

### Frontend Setup

Include the required JavaScript files in your HTML:

```html
<!-- WebSocket Chat Client -->
<script src="/static/js/ai-tutor-client.js"></script>

<!-- UI Controller -->
<script src="/static/js/ai-tutor-ui.js"></script>

<!-- Styles -->
<link rel="stylesheet" href="/static/css/ai-tutor-chat.css">
```

## Usage

### Basic Example

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
            <textarea 
                id="message-input" 
                placeholder="Ask me anything..."
                rows="1"
            ></textarea>
            <button id="send-button">Send</button>
        </div>
    </div>

    <script src="/static/js/ai-tutor-client.js"></script>
    <script src="/static/js/ai-tutor-ui.js"></script>
    
    <script>
        // Initialize UI
        const chat = new AITutorUI();
        
        // Connect to chat (get conversationId and token from your app)
        const conversationId = {{ conversation_id }};
        const accessToken = '{{ access_token }}';
        chat.connect(conversationId, accessToken);
        
        // Set up message sending
        const sendButton = document.getElementById('send-button');
        const messageInput = document.getElementById('message-input');
        
        sendButton.addEventListener('click', () => {
            const content = messageInput.value;
            if (content.trim()) {
                chat.sendMessage(content);
            }
        });
        
        messageInput.addEventListener('keypress', (e) => {
            chat.handleKeyPress(e);
        });
        
        messageInput.addEventListener('input', () => {
            chat.handleMessageInput();
        });
    </script>
</body>
</html>
```

### Advanced Configuration

```javascript
const chat = new AITutorUI({
    chatConfig: {
        protocol: 'wss',  // Use 'wss' for secure WebSocket
        host: 'example.com',
        basePath: '/api/ai',
        reconnectAttempts: 5,
        reconnectDelay: 3000
    }
});

// Connect
chat.connect(conversationId, accessToken);

// Listen to events
chat.client.on('open', () => console.log('Connected!'));
chat.client.on('message', (data) => console.log('Message:', data));
chat.client.on('error', (data) => console.log('Error:', data));

// Send messages
chat.sendMessage('Hello, AI!');

// Show typing status
chat.client.startTyping();
// ... user typing ...
chat.client.stopTyping();

// Get active users
chat.client.getActiveUsers();

// Check status
console.log(chat.getStatus());

// Disconnect
chat.disconnect();
```

## API Reference

### WebSocket Endpoint

```
ws://127.0.0.1:8000/api/ai/ws/chat/{conversation_id}/{access_token}
wss://example.com/api/ai/ws/chat/{conversation_id}/{access_token}
```

### Message Types

#### Client to Server

**Send Message**
```json
{
    "type": "message",
    "content": "Your message here"
}
```

**Typing Start**
```json
{
    "type": "typing_start"
}
```

**Typing Stop**
```json
{
    "type": "typing_stop"
}
```

**Get Active Users**
```json
{
    "type": "get_users"
}
```

#### Server to Client

**New Message**
```json
{
    "type": "message",
    "role": "user|assistant",
    "content": "Message text",
    "user_id": 123,
    "full_name": "John Doe",
    "message_id": 456,
    "sources": ["source1", "source2"],
    "timestamp": "2024-01-01T12:00:00"
}
```

**User Typing**
```json
{
    "type": "typing",
    "user_id": 123,
    "is_typing": true,
    "timestamp": "2024-01-01T12:00:00"
}
```

**User Online**
```json
{
    "type": "user_online",
    "user_id": 123,
    "full_name": "John Doe",
    "active_users": [123, 124],
    "timestamp": "2024-01-01T12:00:00"
}
```

**User Offline**
```json
{
    "type": "user_offline",
    "user_id": 123,
    "full_name": "John Doe",
    "active_users": [124],
    "timestamp": "2024-01-01T12:00:00"
}
```

**Active Users**
```json
{
    "type": "active_users",
    "users": [123, 124, 125],
    "count": 3
}
```

**Error**
```json
{
    "type": "error",
    "message": "Error description"
}
```

## REST API Endpoints (Backward Compatible)

All existing REST endpoints still work:

### Chat (HTTP POST)
```
POST /api/ai/chat
Content-Type: application/json

{
    "message": "Your question",
    "conversation_id": null,
    "subject_id": null,
    "topic_id": null,
    "document_id": null
}
```

### Get Conversations
```
GET /api/ai/conversations
```

### Get Specific Conversation
```
GET /api/ai/conversations/{conversation_id}
```

### Create Conversation
```
POST /api/ai/conversations
Content-Type: application/json

{
    "title": "Conversation Title",
    "subject_id": null,
    "topic_id": null,
    "document_id": null
}
```

### Delete Conversation
```
DELETE /api/ai/conversations/{conversation_id}
```

### Get Online Status
```
GET /api/ai/online-status/{user_id}
```

### Get Active Conversations
```
GET /api/ai/active-conversations
```

## Features

### 1. Real-time Messaging
- Messages appear instantly in all connected clients
- No polling or manual refresh needed
- Automatic message queuing when offline

### 2. Typing Indicators
- Shows when other users are typing
- Prevents duplicate typing notifications
- Auto-clears after inactivity

### 3. Online Status
- See which users are currently online
- Get notified when users connect/disconnect
- List of active users in each conversation

### 4. Connection Management
- Automatic reconnection on disconnect
- Configurable retry attempts and delays
- Graceful degradation if connection lost

### 5. AI Response Integration
- Seamless AI response streaming
- Source attribution
- Context-aware responses

### 6. Message History
- All messages saved to database
- Access conversation history
- Search and filter capabilities

## Security

### Authentication
- Token-based authentication (JWT)
- User isolation per conversation
- Automatic token validation

### Best Practices
```javascript
// Secure connection (use https in production)
const chat = new AITutorUI({
    chatConfig: {
        protocol: 'wss',  // Secure WebSocket
        host: 'api.example.com'
    }
});

// Never expose tokens in client code
const accessToken = document.querySelector('[data-token]').dataset.token;
chat.connect(conversationId, accessToken);
```

## Error Handling

### Connection Errors
```javascript
chat.client.on('error', (data) => {
    if (data.error) {
        console.error('Connection error:', data.error);
        // Handle error
    }
});
```

### Message Errors
```javascript
chat.client.on('error', (data) => {
    if (data.message) {
        console.error('Server error:', data.message);
        // Retry or inform user
    }
});
```

### Automatic Recovery
```javascript
// Reconnection is automatic
// Monitor status:
const status = chat.getStatus();
console.log(status.isConnected);
console.log(status.queuedMessages);
console.log(status.reconnectAttempts);
```

## Performance Tips

1. **Message Throttling**
   ```javascript
   let lastSend = Date.now();
   const THROTTLE_MS = 100;
   
   function sendMessageThrottled(content) {
       const now = Date.now();
       if (now - lastSend >= THROTTLE_MS) {
           chat.sendMessage(content);
           lastSend = now;
       }
   }
   ```

2. **Debounce Typing**
   ```javascript
   let typingTimeout;
   messageInput.addEventListener('input', () => {
       clearTimeout(typingTimeout);
       chat.client.startTyping();
       
       typingTimeout = setTimeout(() => {
           chat.client.stopTyping();
       }, 1000);
   });
   ```

3. **Message Limits**
   - Keep chat history bounded (e.g., last 50 messages)
   - Archive old conversations
   - Paginate message loading

## Troubleshooting

### Connection Won't Establish
```javascript
// Check browser console for errors
// Verify token is valid
// Check WebSocket endpoint URL
console.log(chat.client.getStatus());
```

### Messages Not Sending
```javascript
// Check if connected
if (!chat.client.isConnected) {
    console.log('Not connected, messages queued');
}

// Check message queue
console.log(chat.client.messageQueue);
```

### Reconnection Loop
```javascript
// Reduce reconnect attempts
const chat = new AITutorUI({
    chatConfig: {
        reconnectAttempts: 3,  // Lower value
        reconnectDelay: 5000   // Longer delay
    }
});
```

## Examples

### Multi-user Chat
```javascript
// Multiple users can be in same conversation
// See each other's messages in real-time
// Get notified of online status changes
```

### Private Tutoring Session
```javascript
// One-on-one chat with AI tutor
// Full message history
// Source attribution for learning
```

### Study Group Collaboration
```javascript
// Multiple students with AI tutor
// Shared conversation
// Real-time collaboration
```

## Browser Support

- Chrome/Edge 43+
- Firefox 45+
- Safari 10.1+
- Opera 30+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Limitations

- WebSocket connections limited by server capacity
- Message size limited to ~64KB per message
- Conversation history limited to database storage
- No file transfer (use document upload endpoint)

## Future Enhancements

- [ ] End-to-end message encryption
- [ ] Message reactions and threaded replies
- [ ] Rich text formatting
- [ ] Code snippet syntax highlighting
- [ ] Voice/video call integration
- [ ] Message search and filtering
- [ ] User presence indicators
- [ ] Message read receipts

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review browser console for errors
3. Check server logs for WebSocket errors
4. Refer to API documentation at `/docs`

---

**Happy chatting! 🚀**
