// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const charCount = document.getElementById('charCount');

// Auto-resize textarea
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    
    // Update character count
    const count = this.value.length;
    charCount.textContent = `${count}/1000`;
    
    if (count > 900) {
        charCount.style.color = '#ef4444';
    } else {
        charCount.style.color = 'var(--text-secondary)';
    }
});

// Send message on Enter (Shift+Enter for new line)
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Send example question
function sendExample(text) {
    userInput.value = text;
    sendMessage();
}

// Send message
async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Hide welcome message on first message
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.style.display = 'none';
    }
    
    // Disable input
    sendBtn.disabled = true;
    userInput.disabled = true;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    charCount.textContent = '0/1000';
    
    // Show loading
    loadingOverlay.style.display = 'flex';
    
    try {
        // Send to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        console.log('📦 Backend response:', data);
        console.log('🎯 Quick replies received:', data.quick_replies);
        
        if (data.success) {
            // Add AI response
            addMessage(data.response, 'ai', data.quick_replies);
        } else {
            addMessage('Sorry, something went wrong. Please try again.', 'ai');
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I couldn\'t connect to the server. Please try again.', 'ai');
    } finally {
        // Hide loading and re-enable input
        loadingOverlay.style.display = 'none';
        sendBtn.disabled = false;
        userInput.disabled = false;
        userInput.focus();
    }
}

// Add message to chat
function addMessage(text, type, quickReplies = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'user' ? '👤' : '🤖';
    
    const contentDiv = document.createElement('div');
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = text;  // Changed from textContent to innerHTML to support HTML formatting
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    contentDiv.appendChild(messageContent);
    contentDiv.appendChild(messageTime);
    
    // Add quick reply buttons if provided
    console.log('🔍 Checking quick replies:', quickReplies);
    if (quickReplies && quickReplies.length > 0) {
        console.log('✅ Creating buttons for:', quickReplies);
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'quick-replies';
        
        quickReplies.forEach(reply => {
            const button = document.createElement('button');
            button.className = 'quick-reply-btn';
            button.textContent = reply;
            button.onclick = () => {
                userInput.value = reply;
                sendMessage();
                // Remove buttons after click
                buttonsDiv.remove();
            };
            buttonsDiv.appendChild(button);
        });
        
        contentDiv.appendChild(buttonsDiv);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Clear chat
async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        await fetch('/api/clear', {
            method: 'POST'
        });
        
        // Clear messages
        messagesDiv.innerHTML = '';
        
        // Show welcome message again
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error clearing chat:', error);
        alert('Failed to clear chat. Please try again.');
    }
}

// Load chat history on page load
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.history && data.history.length > 0) {
            // Hide welcome message
            const welcomeMsg = document.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.style.display = 'none';
            }
            
            // Add messages from history
            data.history.forEach(msg => {
                addMessage(msg.user, 'user');
                addMessage(msg.ai, 'ai');
            });
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    userInput.focus();
});
