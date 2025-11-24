# VoiceCoach Platform - Microservices Architecture

This repository contains two microservices that work together:

1. **VoiceCoach API** (FastAPI) - Voice-based workplace coaching with realistic manager personalities
2. **Web Chatbot** (Flask) - Text-based workplace communication coach with Qdrant vector search

Both services share authentication infrastructure and can be deployed separately or together.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Render Platform                           │
│                                                              │
│  ┌──────────────────────┐      ┌─────────────────────────┐ │
│  │  VoiceCoach API      │      │  Web Chatbot            │ │
│  │  (FastAPI + WebSocket)│◄────►│  (Flask + Qdrant)      │ │
│  │  Port: 8000          │      │  Port: 5001             │ │
│  └──────────────────────┘      └─────────────────────────┘ │
│           │                              │                  │
│           ▼                              ▼                  │
│  ┌──────────────────────┐      ┌─────────────────────────┐ │
│  │  PostgreSQL DB       │      │  PostgreSQL DB          │ │
│  │  (voicecoach-db)     │      │  (chatbot-db)           │ │
│  └──────────────────────┘      └─────────────────────────┘ │
│                                                              │
│  External Services:                                          │
│  • OpenAI API (GPT-4, Whisper, TTS)                         │
│  • ElevenLabs API (Voice synthesis)                         │
│  • Qdrant Cloud (Vector database)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start - Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL (optional - SQLite used by default locally)
- OpenAI API key
- ElevenLabs API key (optional)
- Qdrant Cloud credentials (for chatbot)

### 1. Clone and Setup

```cmd
cd c:\Users\suyas\Downloads\voiceCoach-master\voiceCoach-master
```

### 2. Install Dependencies

**VoiceCoach API:**
```cmd
pip install -r requirements.txt
```

**Web Chatbot:**
```cmd
pip install -r web_chatbot-main\requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in the root directory:

```env
# Shared Configuration
OPENAI_API_KEY=your_openai_key_here
ENVIRONMENT=development

# VoiceCoach API
SECRET_KEY=your_secret_key_for_jwt
ELEVENLABS_API_KEY=your_elevenlabs_key
DATABASE_URL=sqlite:///./voicecoach.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENABLE_RABBITMQ=false
ENABLE_VAD=true
ENABLE_AUGMENTATION=true

# Web Chatbot
FLASK_SECRET_KEY=your_flask_secret
JWT_SECRET_KEY=your_jwt_secret
FLASK_DEBUG=True
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
CORS_ORIGINS=http://localhost:3000,http://localhost:5001
AUTH_SERVICE_URL=http://localhost:8000
```

### 4. Run Services

**Terminal 1 - VoiceCoach API:**
```cmd
set PORT=8000
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Web Chatbot:**
```cmd
set PORT=5001
set FLASK_DEBUG=True
python web_chatbot-main\app.py
```

### 5. Access Services

- **VoiceCoach API:** http://localhost:8000
  - Health: http://localhost:8000/health
  - Docs: http://localhost:8000/docs
  
- **Web Chatbot:** http://localhost:5001
  - Health: http://localhost:5001/health
  - API: http://localhost:5001/api/chat

---

## 🌐 Render Deployment (Microservices)

### Option 1: Using render.yaml (Recommended)

1. **Connect Repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the `render.yaml` file

2. **Configure Environment Variables:**
   
   Render will prompt you to set these secrets:
   - `OPENAI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   
   Other variables are auto-generated or predefined in `render.yaml`.

3. **Deploy:**
   - Click "Apply"
   - Render will create:
     - 2 web services (voicecoach-api, voicecoach-chatbot)
     - 2 PostgreSQL databases
     - All networking and environment configs

### Option 2: Manual Service Creation

**Create VoiceCoach API Service:**
1. New Web Service
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
4. Root Directory: `voiceCoach-master`
5. Add environment variables from `.env.example`

**Create Web Chatbot Service:**
1. New Web Service
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app`
4. Root Directory: `voiceCoach-master/web_chatbot-main`
5. Add environment variables
6. Set `AUTH_SERVICE_URL` to VoiceCoach API URL

**Create Databases:**
1. New PostgreSQL database for each service
2. Copy connection strings to respective `DATABASE_URL` env vars

### Important Render Configuration Notes

⚠️ **Common Render Issues & Solutions:**

1. **Database Connection String:**
   - Render PostgreSQL URLs start with `postgres://`
   - Both services automatically convert to `postgresql://` for SQLAlchemy
   
2. **CORS Configuration:**
   - Update `ALLOWED_ORIGINS` and `CORS_ORIGINS` with actual Render URLs
   - Format: `https://service-name.onrender.com`

3. **Health Check Paths:**
   - VoiceCoach: `/health`
   - Chatbot: `/health`
   - Ensure these return 200 OK

4. **Timeouts:**
   - Chatbot uses 120s timeout for Gunicorn
   - Increase if OpenAI/Qdrant calls are slow

5. **Cold Starts:**
   - Free tier services sleep after 15 minutes
   - First request may take 30-60 seconds
   - Use Starter plan for always-on services

---

## 🔧 API Endpoints

### VoiceCoach API (FastAPI)

**Authentication:**
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/status` - Check auth status
- `GET /auth/me` - Get user profile

**Business Accounts:**
- `POST /auth/business-signup` - Create business account
- `GET /auth/business-dashboard` - Get company dashboard
- `POST /auth/add-business-user` - Add team member
- `DELETE /auth/delete-business-user/{id}` - Remove team member

**Voice Coaching:**
- `WS /ws/{client_id}` - WebSocket for voice conversations
  - Query params: `token`, `personality`, `scenario`
- `POST /feedback_summary` - Get conversation analysis

**Configuration:**
- `GET /config` - Get personalities and scenarios
- `GET /health` - Health check

### Web Chatbot (Flask)

**Authentication:**
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `POST /auth/logout` - Logout
- `GET /auth/status` - Check auth status

**Chat:**
- `POST /api/chat` - Send message (with JWT token)
- `GET /api/history` - Get chat history
- `POST /api/clear` - Clear history

**System:**
- `GET /health` - Health check
- `GET /api/session-check` - Debug session info

---

## 🧪 Testing

### Test Authentication (Chatbot)

```bash
# Signup
curl -X POST http://localhost:5001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"StrongP@ss123!","name":"Test User"}'

# Login
curl -X POST http://localhost:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"StrongP@ss123!"}'

# Check Status (use token from login response)
curl -X GET http://localhost:5001/auth/status \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Test Chat (Chatbot)

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"message":"My manager gave me harsh feedback and I feel upset"}'
```

### Test VoiceCoach WebSocket

Use the web interface at `http://localhost:8000/` or test with WebSocket client:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/test-client?token=YOUR_TOKEN&personality=entj_commander&scenario=role_shift');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};

// Send audio
ws.send(JSON.stringify({
  type: 'audio_data',
  audio: 'base64_encoded_audio_here'
}));
```

---

## 🔐 Security Features

Both services implement:
- ✅ Strong password validation (8+ chars, upper, lower, number, special)
- ✅ Email validation with disposable domain blocking
- ✅ Input sanitization (XSS, SQL injection prevention)
- ✅ JWT token authentication with expiration
- ✅ Token revocation on logout
- ✅ Rate limiting (VoiceCoach)
- ✅ CORS configuration
- ✅ Bcrypt password hashing
- ✅ Database connection pooling
- ✅ Environment-based configuration

---

## 📊 Database Schema

### Shared Tables (Both Services)

**users**
- `user_id` (PK)
- `email` (unique)
- `password_hash`
- `name`
- `user_type` (free, b2b_admin, b2b_employee)
- `trial_status` (active, expired, cancelled)
- `company_id` (FK, nullable)
- `created_at`

**companies**
- `company_id` (PK)
- `name` (unique)
- `contact_email`
- `created_at`

**revoked_tokens**
- `id` (PK)
- `jti` (unique token identifier)
- `revoked_at`

### Chatbot-Specific Tables

**chat_sessions**
- `session_id` (PK)
- `user_id` (FK)
- `session_token`
- `tone` (Professional, Casual)
- `message_count`
- `created_at`, `updated_at`

**chat_messages**
- `message_id` (PK)
- `session_id` (FK)
- `role` (user, assistant)
- `content`
- `timestamp`

---

## 🛠️ Troubleshooting

### Database Connection Issues

**Error:** `could not connect to server`
```bash
# Check DATABASE_URL format
# Correct: postgresql://user:pass@host/db
# Incorrect: postgres://user:pass@host/db (will auto-fix)
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'models'`
```bash
# Ensure you're in correct directory
cd web_chatbot-main
python app.py
```

### CORS Errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`
```bash
# Update ALLOWED_ORIGINS / CORS_ORIGINS with actual frontend URLs
# Include http://localhost:3000 for local development
```

### WebSocket Connection Failed

**Error:** `WebSocket connection to 'ws://...' failed`
```bash
# Check token is valid: GET /auth/status
# Verify personality and scenario exist: GET /config
# Ensure no firewall blocking WebSocket connections
```

### Render 502 Bad Gateway

- Check service logs in Render dashboard
- Verify health check endpoint returns 200
- Increase timeout if needed
- Check DATABASE_URL is set correctly

---

## 📦 Project Structure

```
voiceCoach-master/
├── server.py                    # VoiceCoach FastAPI app
├── requirements.txt             # VoiceCoach dependencies
├── render.yaml                  # Render microservices config
├── README.md                    # This file
├── .env.example                 # Environment template
│
├── core/                        # VoiceCoach core modules
│   ├── models.py                # Database models
│   ├── database.py              # Database config
│   └── schemas.py               # Pydantic schemas
│
├── routes/                      # VoiceCoach routes
│   └── auth_routes.py           # Auth endpoints
│
├── services/                    # VoiceCoach services
│   ├── feedback_analysis.py    # AI feedback generation
│   └── advanced_analysis_async.py
│
├── utils/                       # VoiceCoach utilities
│   ├── auth_utils.py            # JWT helpers
│   ├── auth_validators.py      # Input validation
│   ├── security_utils.py       # Password hashing
│   └── rate_limiter.py          # Rate limiting
│
├── static/                      # VoiceCoach frontend
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   └── js/
│
└── web_chatbot-main/            # Chatbot microservice
    ├── app.py                   # Flask app
    ├── requirements.txt         # Chatbot dependencies
    ├── models.py                # Database models
    ├── database.py              # Database config
    │
    ├── utils/                   # Chatbot utilities
    │   ├── auth_validators.py   # Input validation
    │   └── security_utils.py    # Password hashing
    │
    ├── templates/               # Chatbot frontend
    │   └── index.html
    │
    └── static/
        ├── css/
        └── js/
```

---

## 🤝 Integration Guide

### Using Shared Authentication

The chatbot can authenticate users via the VoiceCoach API:

1. **Set AUTH_SERVICE_URL** in chatbot environment:
   ```env
   AUTH_SERVICE_URL=https://voicecoach-api.onrender.com
   ```

2. **Or use independent auth:**
   - Leave `AUTH_SERVICE_URL` empty
   - Chatbot will use its own database

3. **Shared token format:**
   Both services use JWT with same structure:
   ```json
   {
     "user_id": 123,
     "email": "user@example.com",
     "exp": 1234567890
   }
   ```

### Cross-Service Communication

Services communicate via:
- **HTTP REST** for auth forwarding
- **Shared PostgreSQL** (optional)
- **Environment variables** for service discovery

---

## 📝 License

Proprietary - All rights reserved

---

## 📞 Support

For deployment issues:
1. Check Render dashboard logs
2. Verify all environment variables are set
3. Test health endpoints
4. Review CORS configuration

For code issues:
1. Check Python version (3.11+ required)
2. Verify all dependencies installed
3. Check database migrations
4. Review application logs

---

## 🎯 Next Steps

- [ ] Set up monitoring (Sentry, LogRocket)
- [ ] Add rate limiting to chatbot
- [ ] Implement caching (Redis)
- [ ] Add automated tests
- [ ] Set up CI/CD pipeline
- [ ] Add load balancing for high traffic
- [ ] Implement message queue for async processing
- [ ] Add analytics dashboard

---

**Last Updated:** November 2025
# vc_cb 
