/**
 * UI Controller for AI Tutor Real-time Chat
 * Handles the UI interactions with the WebSocket client
 */

class AITutorUI {
    constructor(config = {}) {
        this.config = config;
        this.client = new AITutorChatClient(config.chatConfig || {});
        this.typingTimeout = null;
        this.init();
    }

    init() {
        // Set up event listeners
        this.client.on('open', () => this.onConnectionOpen());
        this.client.on('close', () => this.onConnectionClose());
        this.client.on('message', (data) => this.onMessage(data));
        this.client.on('error', (data) => this.onError(data));
        this.client.on('typing', (data) => this.onTyping(data));
        this.client.on('userOnline', (data) => this.onUserOnline(data));
        this.client.on('userOffline', (data) => this.onUserOffline(data));
        this.client.on('activeUsers', (data) => this.onActiveUsers(data));
    }

    /**
     * Connect to chat
     */
    connect(conversationId, accessToken) {
        this.client.connect(conversationId, accessToken);
    }

    /**
     * Send a message
     */
    sendMessage(content) {
        if (!content.trim()) return;

        this.client.sendMessage(content);
        this.clearMessageInput();
    }

    /**
     * Handle message input (with typing indicator)
     */
    handleMessageInput() {
        this.client.startTyping();

        // Clear previous timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }

        // Stop typing after 1 second of inactivity
        this.typingTimeout = setTimeout(() => {
            this.client.stopTyping();
        }, 1000);
    }

    /**
     * Handle Enter key press
     */
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            const content = event.target.value.trim();
            if (content) {
                this.sendMessage(content);
            }
        }
    }

    // ==================== Event Handlers ====================

    onConnectionOpen() {
        console.log('✅ Chat connected');
        this.updateConnectionStatus('connected');
        this.showNotification('Connected to AI Tutor', 'success');
    }

    onConnectionClose() {
        console.log('❌ Chat disconnected');
        this.updateConnectionStatus('disconnected');
        this.showNotification('Disconnected from AI Tutor', 'warning');
    }

    onMessage(data) {
        console.log('📨 Received message:', data);
        this.addMessageToChat(data);
    }

    onError(data) {
        console.error('❌ Error:', data);
        this.showNotification(`Error: ${data.message || 'Unknown error'}`, 'error');
    }

    onTyping(data) {
        console.log('✏️ User typing:', data);
        if (data.is_typing) {
            this.showTypingIndicator(data.user_id);
        } else {
            this.hideTypingIndicator(data.user_id);
        }
    }

    onUserOnline(data) {
        console.log('👤 User online:', data);
        this.updateActiveUsers(data.active_users);
        this.showNotification(`${data.full_name} is now online`, 'info');
    }

    onUserOffline(data) {
        console.log('👤 User offline:', data);
        this.updateActiveUsers(data.active_users);
        this.showNotification(`${data.full_name} went offline`, 'info');
    }

    onActiveUsers(data) {
        console.log('👥 Active users:', data);
        this.updateActiveUsers(data.users);
    }

    // ==================== UI Methods ====================

    addMessageToChat(message) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.role}`;
        messageElement.id = `message-${message.message_id}`;
        messageElement.innerHTML = `
            <div class="message-header">
                <span class="role">${message.role === 'user' ? '👤 You' : '🤖 AI Tutor'}</span>
                <span class="time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            ${message.sources ? `<div class="message-sources">${this.formatSources(message.sources)}</div>` : ''}
        `;

        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    showTypingIndicator(userId) {
        const indicator = document.getElementById(`typing-${userId}`);
        if (indicator) {
            indicator.style.display = 'block';
        }
    }

    hideTypingIndicator(userId) {
        const indicator = document.getElementById(`typing-${userId}`);
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    updateActiveUsers(users) {
        const userList = document.getElementById('active-users');
        if (!userList) return;

        userList.innerHTML = users.map(userId => `
            <div class="user-badge">
                <span class="status-dot"></span>
                User #${userId}
            </div>
        `).join('');
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        statusElement.className = `status ${status}`;
        statusElement.textContent = status === 'connected' ? '● Online' : '● Offline';
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    clearMessageInput() {
        const input = document.getElementById('message-input');
        if (input) {
            input.value = '';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatSources(sources) {
        if (!Array.isArray(sources) || sources.length === 0) return '';

        return `
            <details class="sources">
                <summary>📚 Sources (${sources.length})</summary>
                <ul>
                    ${sources.map(source => `<li>${this.escapeHtml(source)}</li>`).join('')}
                </ul>
            </details>
        `;
    }

    /**
     * Get client status
     */
    getStatus() {
        return this.client.getStatus();
    }

    /**
     * Disconnect
     */
    disconnect() {
        this.client.disconnect();
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AITutorUI;
}
