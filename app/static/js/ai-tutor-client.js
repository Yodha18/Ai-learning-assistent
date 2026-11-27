/**
 * AI Tutor WebSocket Chat Client
 * Handles real-time communication with the AI tutor
 */

class AITutorChatClient {
    constructor(config = {}) {
        this.config = {
            protocol: config.protocol || (window.location.protocol === 'https:' ? 'wss' : 'ws'),
            host: config.host || window.location.host,
            basePath: config.basePath || '/api/ai',
            reconnectAttempts: config.reconnectAttempts || 5,
            reconnectDelay: config.reconnectDelay || 3000,
            ...config
        };

        this.ws = null;
        this.conversationId = null;
        this.accessToken = null;
        this.isConnected = false;
        this.reconnectCount = 0;
        this.messageQueue = [];
        this.listeners = {
            open: [],
            close: [],
            message: [],
            error: [],
            typing: [],
            userOnline: [],
            userOffline: [],
            activeUsers: []
        };
    }

    /**
     * Connect to the WebSocket chat endpoint
     */
    connect(conversationId, accessToken) {
        this.conversationId = conversationId;
        this.accessToken = accessToken;

        const wsUrl = `${this.config.protocol}://${this.config.host}${this.config.basePath}/ws/chat/${conversationId}/${accessToken}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => this.handleOpen();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onerror = (event) => this.handleError(event);
            this.ws.onclose = () => this.handleClose();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.emit('error', { error: error.message });
        }
    }

    /**
     * Handle WebSocket open event
     */
    handleOpen() {
        this.isConnected = true;
        this.reconnectCount = 0;
        console.log(`✅ Connected to AI Tutor (Conversation ${this.conversationId})`);
        
        // Flush message queue
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.send(message);
        }

        this.emit('open', { conversationId: this.conversationId });
    }

    /**
     * Handle WebSocket message event
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'message':
                    this.emit('message', data);
                    break;
                case 'typing':
                    this.emit('typing', data);
                    break;
                case 'user_online':
                    this.emit('userOnline', data);
                    break;
                case 'user_offline':
                    this.emit('userOffline', data);
                    break;
                case 'active_users':
                    this.emit('activeUsers', data);
                    break;
                case 'error':
                    this.emit('error', data);
                    console.error('Server error:', data.message);
                    break;
                default:
                    console.warn('Unknown message type:', data.type);
            }
        } catch (error) {
            console.error('Message parsing error:', error);
        }
    }

    /**
     * Handle WebSocket error event
     */
    handleError(event) {
        console.error('❌ WebSocket error:', event);
        this.emit('error', { error: 'Connection error' });
    }

    /**
     * Handle WebSocket close event
     */
    handleClose() {
        this.isConnected = false;
        console.log('❌ WebSocket disconnected');
        this.emit('close', {});

        // Attempt to reconnect
        if (this.reconnectCount < this.config.reconnectAttempts) {
            this.reconnectCount++;
            console.log(`🔄 Reconnecting... (Attempt ${this.reconnectCount}/${this.config.reconnectAttempts})`);
            setTimeout(() => {
                this.connect(this.conversationId, this.accessToken);
            }, this.config.reconnectDelay * this.reconnectCount);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }

    /**
     * Send a message to the AI tutor
     */
    sendMessage(content) {
        const message = {
            type: 'message',
            content: content
        };
        this.send(message);
    }

    /**
     * Notify that user started typing
     */
    startTyping() {
        this.send({
            type: 'typing_start'
        });
    }

    /**
     * Notify that user stopped typing
     */
    stopTyping() {
        this.send({
            type: 'typing_stop'
        });
    }

    /**
     * Request list of active users
     */
    getActiveUsers() {
        this.send({
            type: 'get_users'
        });
    }

    /**
     * Send message through WebSocket
     */
    send(message) {
        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
            } catch (error) {
                console.error('Error sending message:', error);
            }
        } else {
            // Queue message if not connected
            this.messageQueue.push(message);
            console.warn('Message queued (not connected):', message);
        }
    }

    /**
     * Register event listener
     */
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`Unknown event: ${event}`);
        }
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Disconnect from WebSocket
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.isConnected = false;
        }
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            conversationId: this.conversationId,
            queuedMessages: this.messageQueue.length,
            reconnectAttempts: this.reconnectCount
        };
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AITutorChatClient;
}
