

# 💼 Gen Z Workplace Coach - API Documentation

## 🎯 **Project Overview**

This is a **Flask REST API backend** for an AI-powered workplace coaching chatbot that helps Gen Z professionals navigate workplace challenges through:

* **Adaptive tone selection** (Professional/Casual)
* **Quick reply suggestions** for common workplace topics
* **Two-step conversation flow** (tone selection → topic selection)
* **STEP + 4Rs coaching frameworks** for adaptability and emotional intelligence
* **10-message free limit** with premium upgrade prompt
* **Session-based chat history** with Flask sessions
* **Safety boundaries** for harmful content and off-topic queries
* **OpenAI GPT-4o-mini** for intelligent, contextual responses
* **Qdrant vector database** for RAG (Retrieval-Augmented Generation)
* **HTML-formatted responses** with bold text and bullet points
* **Fast responses** (1-2 seconds) optimized for speed

---

## 🚀 **Base URL**

**Local Development:**
```
http://localhost:10000
```

**Production (Render):**
```
https://web-chatbot-xzep.onrender.com
```

---

## 🔌 **API Endpoints**

### 1️⃣ **`GET /`**
**Description:** Serves the main chat interface (HTML page)

**Response:** HTML page with embedded CSS and JavaScript

**Usage:**
```bash
curl http://localhost:10000/
```

---

### 2️⃣ **`POST /api/chat`**
**Description:** Main endpoint for sending user messages and receiving AI responses

#### ✅ Request:

**Headers:**
```json
{
  "Content-Type": "application/json",
  "Cookie": "session=<flask-session-cookie>"
}
```

**Body:**
```json
{
  "message": "I'm feeling stressed about my deadlines"
}
```

#### ✅ Response (Success):

```json
{
  "response": "That sounds really overwhelming. Here's how to tackle it using STEP:<br><br>• <b>Spot</b> - Which deadline is most urgent?<br>• <b>Think</b> - Can you break tasks into smaller chunks?<br>• <b>Engage</b> - Ask your manager to prioritize<br>• <b>Perform</b> - Track progress and adjust<br><br>Want help with any specific step?",
  "quick_replies": [],
  "success": true
}
```

**Response with Quick Replies (after first message):**
```json
{
  "response": "Hello! How can I support you today in navigating workplace challenges?",
  "quick_replies": ["Professional", "Casual"],
  "success": true
}
```

**Response with Topic Suggestions (after tone selection):**
```json
{
  "response": "Got it — I'll reply in a Casual tone. How can I help today?",
  "quick_replies": ["Work relationships", "Stress & deadlines", "Career growth", "Team conflicts"],
  "success": true
}
```

**Response when 10-message limit reached:**
```json
{
  "response": "You've reached the free message limit (10 messages). Upgrade to Premium for unlimited conversations! 🚀",
  "limit_reached": true,
  "quick_replies": [],
  "success": true
}
```

#### ❌ Error Responses:

**Empty message:**
```json
{
  "error": "Message cannot be empty"
}
```
*Status Code: 400*

**Service unavailable:**
```json
{
  "error": "Services unavailable. Please try again later.",
  "success": false
}
```
*Status Code: 503*

**Server error:**
```json
{
  "error": "An error occurred while processing your message.",
  "success": false
}
```
*Status Code: 500*

#### 🛡️ **Safety Responses:**

**Harmful content detected (violence, suicide, etc.):**
```json
{
  "response": "⚠️ I'm concerned about what you've shared. If you're in immediate danger or witnessing illegal activity, please contact:\n\n• Emergency Services: 911\n• National Suicide Prevention Lifeline: 988\n• Workplace Violence Hotline: 1-800-799-7233\n\nI'm designed to help with workplace communication challenges, not crisis or safety situations. Please reach out to professionals who can provide proper support.",
  "quick_replies": [],
  "success": true
}
```

**Personal health issues (headache, pain, etc.):**
```json
{
  "response": "I'm specifically designed for workplace communication challenges. For health concerns, please consult a medical professional. Can we focus on a work-related communication or teamwork challenge instead?",
  "quick_replies": [],
  "success": true
}
```

---

### 3️⃣ **`GET /api/history`**
**Description:** Retrieves the current session's chat history

#### ✅ Response:

```json
{
  "history": [
    {
      "user": "I'm stressed about my manager",
      "ai": "That sounds tough. What specifically is causing the stress?",
      "timestamp": "2025-11-11T10:30:45.123456"
    },
    {
      "user": "They micromanage everything",
      "ai": "Micromanagement can be frustrating. How does it impact your work?",
      "timestamp": "2025-11-11T10:31:12.789012"
    }
  ]
}
```

**Empty history:**
```json
{
  "history": []
}
```

---

### 4️⃣ **`POST /api/clear`**
**Description:** Clears the current session's chat history and resets conversation state

#### ✅ Response:

```json
{
  "success": true,
  "message": "Chat history cleared"
}
```

**Note:** This also resets the tone selection and message counter

---

### 5️⃣ **`GET /health`**
**Description:** Health check endpoint for monitoring service status

#### ✅ Response:

```json
{
  "status": "healthy",
  "openai_ready": true,
  "qdrant_ready": true,
  "timestamp": "2025-11-13T10:45:30.123456"
}
```

---

## ⚠️ **IMPORTANT: HTML Formatting in Responses**

### **What the API Returns**

All AI responses contain **HTML formatting** that must be rendered properly:

**Example API Response:**
```json
{
  "response": "Here's how to handle it using STEP:<br><br>• <b>Spot</b> - Identify the issue<br>• <b>Think</b> - Consider perspectives<br>• <b>Engage</b> - Take action<br>• <b>Perform</b> - Review outcomes",
  "success": true
}
```

### **HTML Tags Used**

| Tag | Purpose | Example |
|-----|---------|---------|
| `<b>` | **Bold text** | `<b>Spot</b>` → **Spot** |
| `<br>` | Line break | `text<br>text` → line break |
| `<br><br>` | Paragraph break | `intro<br><br>bullets` → double space |

### **Frontend Developer Requirements**

#### ✅ **Option 1: Use `innerHTML` (Recommended)**

```javascript
// ✅ CORRECT - Renders HTML tags
messageElement.innerHTML = data.response;
```

**Result:** Bold text and line breaks render properly

#### ❌ **Option 2: Use `textContent` (WRONG)**

```javascript
// ❌ WRONG - Shows raw HTML tags
messageElement.textContent = data.response;
```

**Result:** User sees `<b>Spot</b>` literally (bad UX!)

### **React/Vue Implementation**

**React:**
```jsx
<div 
  className="message-content" 
  dangerouslySetInnerHTML={{ __html: data.response }}
/>
```

**Vue:**
```vue
<div class="message-content" v-html="data.response"></div>
```

### **Security Note**

✅ **Safe to use `innerHTML`** because:
- All responses come from your own API (trusted source)
- No user-generated HTML is injected
- GPT-4o-mini only outputs `<b>` and `<br>` tags (no scripts, iframes, etc.)

### **Expected Visual Output**

**Raw API Response:**
```
"Here's how to handle it using STEP:<br><br>• <b>Spot</b> - Identify the issue<br>• <b>Think</b> - Consider perspectives"
```

**Rendered in Browser:**
```
Here's how to handle it using STEP:

• Spot - Identify the issue
• Think - Consider perspectives
```
(Note: "Spot" and "Think" will be bold)

---

## 🎨 **Conversation Flow**

### **Step 1: Initial Message**
User sends first message → Bot responds + shows tone selection buttons

**Request:**
```json
{
  "message": "hi"
}
```

**Response:**
```json
{
  "response": "Hello! How can I support you today in navigating workplace challenges?",
  "quick_replies": ["Professional", "Casual"],
  "success": true
}
```

---

### **Step 2: Tone Selection**
User clicks tone button → Bot confirms + shows topic buttons

**Request:**
```json
{
  "message": "Casual"
}
```

**Response:**
```json
{
  "response": "Got it — I'll reply in a Casual tone. How can I help today?",
  "quick_replies": ["Work relationships", "Stress & deadlines", "Career growth", "Team conflicts"],
  "success": true
}
```

---

### **Step 3: Topic Selection (Optional)**
User clicks topic button → Bot acknowledges and asks for details

**Request:**
```json
{
  "message": "Team conflicts"
}
```

**Response:**
```json
{
  "response": "Let's talk about team conflicts. What's going on?",
  "quick_replies": [],
  "success": true
}
```

---

### **Step 4+: Natural Conversation**
User describes their workplace challenge → Bot provides coaching using STEP or 4Rs framework

**Request:**
```json
{
  "message": "My coworker keeps taking credit for my ideas"
}
```

**Response (Casual tone):**
```json
{
  "response": "Ugh, that's super frustrating. Here's what you can do:<br><br>• <b>Recognize</b> - You're feeling undervalued (totally valid!)<br>• <b>Regulate</b> - Don't confront when angry<br>• <b>Respect</b> - Maybe they don't realize they're doing it?<br>• <b>Reflect</b> - Document your work for proof<br><br>Want to talk through how to bring this up?",
  "quick_replies": [],
  "success": true
}
```

**Response (Professional tone):**
```json
{
  "response": "That's a difficult situation. Here's a structured approach using the 4Rs:<br><br>• <b>Recognize</b> - Acknowledge your frustration<br>• <b>Regulate</b> - Choose the right time to address this<br>• <b>Respect</b> - Consider their perspective<br>• <b>Reflect</b> - What outcome do you want?<br><br>Would you like guidance on approaching this conversation?",
  "quick_replies": [],
  "success": true
}
```

---

## 🧠 **Coaching Frameworks**

### **STEP Framework** (Adaptability/Flexibility)
Used when user faces changes, new tasks, or flexibility challenges:

1. **Spot** → Identify the specific challenge
2. **Think** → Encourage perspective-shifting
3. **Engage** → Suggest small, doable action
4. **Perform** → Reflect on outcomes

### **4Rs Framework** (Emotional Intelligence)
Used when user faces emotions, relationships, or conflicts:

1. **Recognize** → Notice emotions (own and others')
2. **Regulate** → Manage emotional response
3. **Respect** → Acknowledge others' perspectives
4. **Reflect** → Draw takeaways for next time

---

## 🚨 **Safety Boundaries**

The chatbot **automatically detects and blocks**:

### **Harmful Content Triggers:**
- Violence keywords: `kill`, `murder`, `assault`, `weapon`, `gun`, `knife`, `blood`, `attack`, `stab`
- Crisis keywords: `suicide`, `abuse`, `threat`, `harass`

### **Off-Topic Triggers:**
- Health keywords: `headache`, `sick`, `pain`, `fever`, `medication`, `doctor`, `hospital`, `injury`, `hurt`

### **Scope Limitations:**
❌ **NOT designed for:**
- Personal health/medical advice
- Mental health crises
- Illegal activities
- Personal relationships (family, romantic)
- Financial, legal, or housing issues

✅ **Designed for:**
- Workplace communication challenges
- Team collaboration issues
- Career development conversations
- Professional relationship navigation

---

## 💰 **Message Limits**

- **Free tier:** 10 messages (5 exchanges)
- **Premium prompt:** Shown after 10th message
- **Counter resets:** When session is cleared or expires

---

## 🔧 **Technical Details**

### **Session Management**
- Uses **Flask server-side sessions** with secure cookies
- Session data includes:
  - `chat_history`: Array of message objects
  - `tone`: Selected tone (Professional/Casual)
  - Message counter for limit enforcement

### **Response Times**
- **Button clicks:** <100ms (instant, no AI call)
- **Safety blocks:** <100ms (keyword matching)
- **Regular messages:** 1-2 seconds (OpenAI API call)

### **AI Model**
- **Model:** GPT-4o-mini (latest OpenAI model for better reasoning)
- **Embeddings:** text-embedding-3-small (for Qdrant vector search)
- **Temperature:** 0.7 (balanced creativity and consistency)
- **Max tokens:** 200 (allows detailed framework explanations)
- **Context window:** Includes last 4 exchanges for better conversation memory

### **RAG Architecture**
- **Vector Database:** Qdrant Cloud
- **Collection:** bridgetext_scenarios
- **Top-K retrieval:** 3 most relevant context chunks
- **Embedding dimension:** 1536 (OpenAI text-embedding-3-small)

---

## 🧩 **Frontend Integration Examples**

### **JavaScript Fetch Example:**

```javascript
// Send message
async function sendMessage(message) {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include', // Important for session cookies
      body: JSON.stringify({ message })
    });

    const data = await response.json();

    if (data.success) {
      // Display AI response
      displayMessage(data.response, 'ai');

      // Show quick reply buttons if present
      if (data.quick_replies && data.quick_replies.length > 0) {
        displayQuickReplies(data.quick_replies);
      }

      // Handle premium limit
      if (data.limit_reached) {
        showPremiumPrompt();
      }
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
}

// Helper function to display message with HTML rendering
function displayMessage(text, role) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  // ✅ CRITICAL: Use innerHTML to render HTML tags (<b>, <br>)
  contentDiv.innerHTML = text;  // NOT textContent!
  
  messageDiv.appendChild(contentDiv);
  chatContainer.appendChild(messageDiv);
}

// Get chat history
async function loadHistory() {
  const response = await fetch('/api/history', {
    credentials: 'include'
  });
  const data = await response.json();
  
  data.history.forEach(msg => {
    displayMessage(msg.user, 'user');
    displayMessage(msg.ai, 'ai');
  });
}

// Clear chat
async function clearChat() {
  await fetch('/api/clear', {
    method: 'POST',
    credentials: 'include'
  });
  
  // Clear UI
  clearChatDisplay();
}
```

### **React Example:**

```jsx
import { useState, useEffect } from 'react';

function ChatBot() {
  const [messages, setMessages] = useState([]);
  const [quickReplies, setQuickReplies] = useState([]);
  const [limitReached, setLimitReached] = useState(false);

  const sendMessage = async (text) => {
    // Add user message
    setMessages(prev => [...prev, { text, role: 'user' }]);

    // Send to API
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();

    if (data.success) {
      // Add AI response (with HTML formatting intact)
      setMessages(prev => [...prev, { text: data.response, role: 'ai' }]);
      setQuickReplies(data.quick_replies || []);
      setLimitReached(data.limit_reached || false);
    }
  };

  return (
    <div className="chatbot">
      <MessageList messages={messages} />
      
      {quickReplies.length > 0 && (
        <QuickReplies 
          replies={quickReplies} 
          onSelect={sendMessage} 
        />
      )}
      
      {limitReached && <PremiumPrompt />}
      
      <ChatInput onSend={sendMessage} disabled={limitReached} />
    </div>
  );
}

// MessageList component should use dangerouslySetInnerHTML
function MessageList({ messages }) {
  return (
    <div className="messages">
      {messages.map((msg, idx) => (
        <div key={idx} className={`message ${msg.role}`}>
          {/* ✅ CRITICAL: Render HTML tags */}
          <div dangerouslySetInnerHTML={{ __html: msg.text }} />
        </div>
      ))}
    </div>
  );
}
```

### **Vue.js Example:**

```vue
<template>
  <div class="chat-container">
    <!-- ✅ CRITICAL: Use v-html to render HTML tags -->
    <div 
      v-for="msg in messages" 
      :key="msg.id" 
      :class="`message ${msg.role}`"
      v-html="msg.text"
    ></div>

    <div v-if="quickReplies.length" class="quick-replies">
      <button 
        v-for="reply in quickReplies" 
        :key="reply"
        @click="sendMessage(reply)"
      >
        {{ reply }}
      </button>
    </div>

    <div v-if="limitReached" class="premium-prompt">
      🚀 Upgrade to Premium for unlimited conversations!
    </div>

    <input 
      v-model="inputText" 
      @keyup.enter="sendMessage(inputText)"
      :disabled="limitReached"
    />
  </div>
</template>

<script>
export default {
  data() {
    return {
      messages: [],
      quickReplies: [],
      limitReached: false,
      inputText: ''
    };
  },
  methods: {
    async sendMessage(text) {
      this.messages.push({ text, role: 'user', id: Date.now() });

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: text })
      });

      const data = await res.json();

      if (data.success) {
        this.messages.push({ 
          text: data.response, 
          role: 'ai', 
          id: Date.now() + 1 
        });
        this.quickReplies = data.quick_replies || [];
        this.limitReached = data.limit_reached || false;
      }

      this.inputText = '';
    }
  }
};
</script>
```

---

## 🔒 **CORS Configuration**

The API has **CORS enabled** to allow cross-origin requests from frontend applications:

```python
CORS(app)  # Allows all origins by default
```

For production, configure specific origins:
```python
CORS(app, origins=["https://your-frontend-domain.com"])
```

---

## 📝 **Environment Variables Required**

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# Qdrant Vector Database
QDRANT_URL=https://your-qdrant-instance.cloud
QDRANT_API_KEY=your-qdrant-api-key

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
PORT=10000
FLASK_DEBUG=False
```

**Note:** All environment variables are required for full functionality.

---

## 🚦 **HTTP Status Codes**

| Code | Meaning               | When it occurs                    |
|------|-----------------------|-----------------------------------|
| 200  | Success               | Request processed successfully    |
| 400  | Bad Request           | Empty message sent                |
| 500  | Internal Server Error | Unexpected server error           |
| 503  | Service Unavailable   | OpenAI service not initialized    |

---

## 📊 **Rate Limiting**

- **Session-based:** 10 messages per session (free tier)
- **No API key required** for frontend
- **Session expires:** After browser close or timeout

---

## 🎯 **Best Practices for Frontend**

1. **Always include credentials:**
   ```javascript
   fetch('/api/chat', { credentials: 'include' })
   ```

2. **Handle quick replies dynamically:**
   - Show buttons only when `quick_replies` array has items
   - Remove buttons after user clicks one

3. **Show loading states:**
   - Display "thinking..." indicator while waiting for response
   - Use inline animation (not full-screen overlay)

4. **Handle errors gracefully:**
   - Show user-friendly error messages
   - Provide retry option for failed requests

5. **Respect the message limit:**
   - Disable input when `limit_reached: true`
   - Show prominent upgrade prompt

6. **Preserve session:**
   - Don't manually clear cookies
   - Use same domain for API and frontend

7. **Render HTML formatting:**
   - **MUST use `innerHTML` (JS) or `dangerouslySetInnerHTML` (React) or `v-html` (Vue)**
   - Do NOT use `textContent` or `{{ }}` - this breaks formatting
   - See "HTML Formatting in Responses" section above

---

## 🐛 **Common Issues & Solutions**

### **Issue: Session not persisting**
**Solution:** Ensure `credentials: 'include'` in fetch requests

### **Issue: CORS errors**
**Solution:** Backend has CORS enabled, check browser console for actual error

### **Issue: Slow responses**
**Solution:** Normal (1-2s for AI generation), show loading indicator

### **Issue: Quick replies not appearing**
**Solution:** Check if `data.quick_replies` exists and has length > 0

### **Issue: Messages not showing after 10**
**Solution:** Expected behavior, show premium prompt

### **Issue: Bold text not rendering / Seeing `<b>` tags**
**Solution:** Use `innerHTML` (JavaScript), `dangerouslySetInnerHTML` (React), or `v-html` (Vue). Do NOT use `textContent` or `{{ }}` interpolation.

### **Issue: No line breaks between bullet points**
**Solution:** Ensure HTML rendering is enabled. `<br>` tags need `innerHTML` to work.

---

## 📧 **Support**

For technical issues or questions, contact the backend team or refer to the main README.md file in the repository.

---

**Last Updated:** November 13, 2025  
**API Version:** 2.0  
**Backend Framework:** Flask 3.0.0  
**AI Model:** OpenAI GPT-4o-mini  
**Vector Database:** Qdrant Cloud