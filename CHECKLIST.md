# 🚀 Deployment Checklist

Use this checklist before deploying to production.

---

## ✅ Pre-Deployment

### Code & Repository
- [ ] All code committed to git
- [ ] `.env` file is NOT committed (check .gitignore)
- [ ] `.env.example` is committed and up-to-date
- [ ] README.md is accurate and complete
- [ ] No sensitive data in code (API keys, passwords, etc.)
- [ ] All TODOs and debug code removed
- [ ] Code reviewed and tested locally

### Local Testing
- [ ] Both services start without errors
- [ ] `python test_services.py` passes all tests
- [ ] Health checks return 200 OK
- [ ] Authentication flow works (signup → login → status)
- [ ] Chatbot responds to messages correctly
- [ ] VoiceCoach WebSocket connects
- [ ] Database operations work (user creation, retrieval)
- [ ] CORS configured for your domains

### Environment Configuration
- [ ] `.env` file created and configured locally
- [ ] All required API keys obtained:
  - [ ] OPENAI_API_KEY
  - [ ] ELEVENLABS_API_KEY (optional)
  - [ ] QDRANT_URL and QDRANT_API_KEY
- [ ] Strong secrets generated for production:
  - [ ] SECRET_KEY (32+ chars)
  - [ ] FLASK_SECRET_KEY (32+ chars)
  - [ ] JWT_SECRET_KEY (32+ chars)
- [ ] CORS origins configured for production domains
- [ ] Database URLs ready (will be auto-provided by Render)

### Dependencies
- [ ] `requirements.txt` up-to-date for VoiceCoach
- [ ] `web_chatbot-main/requirements.txt` up-to-date for Chatbot
- [ ] No version conflicts
- [ ] All imports work locally

---

## 🌐 Render Deployment

### Account Setup
- [ ] Render account created
- [ ] Payment method added (if using paid plans)
- [ ] GitHub repository connected to Render

### Blueprint Deployment (Recommended)
- [ ] Repository contains `render.yaml` in root
- [ ] `render.yaml` reviewed and customized if needed
- [ ] Blueprint created in Render dashboard
- [ ] All secrets configured in Blueprint setup

### Environment Variables (Render Dashboard)
- [ ] VoiceCoach API secrets set:
  - [ ] OPENAI_API_KEY
  - [ ] SECRET_KEY (auto-generated)
  - [ ] ELEVENLABS_API_KEY (optional)
  - [ ] ALLOWED_ORIGINS (production URLs)
- [ ] Web Chatbot secrets set:
  - [ ] OPENAI_API_KEY
  - [ ] FLASK_SECRET_KEY (auto-generated)
  - [ ] JWT_SECRET_KEY (auto-generated)
  - [ ] QDRANT_URL
  - [ ] QDRANT_API_KEY
  - [ ] CORS_ORIGINS (production URLs)
  - [ ] AUTH_SERVICE_URL (optional)

### Database Configuration
- [ ] PostgreSQL databases created (or auto-created by Blueprint)
- [ ] DATABASE_URL linked to services
- [ ] Database region matches service region
- [ ] Backups enabled (recommended for production)

### Service Configuration
- [ ] VoiceCoach API service created:
  - [ ] Root directory: `voiceCoach-master`
  - [ ] Build command correct
  - [ ] Start command correct
  - [ ] Health check path: `/health`
- [ ] Web Chatbot service created:
  - [ ] Root directory: `voiceCoach-master/web_chatbot-main`
  - [ ] Build command correct
  - [ ] Start command correct
  - [ ] Health check path: `/health`
- [ ] Both services use Python 3.11+
- [ ] Auto-deploy enabled on git push

---

## ✅ Post-Deployment

### Initial Verification
- [ ] Both services show "Live" status in Render
- [ ] Health checks passing (green checkmark)
- [ ] No errors in deployment logs
- [ ] Services accessible via public URLs

### Functional Testing
- [ ] VoiceCoach health endpoint works:
  ```
  curl https://voicecoach-api.onrender.com/health
  ```
- [ ] Chatbot health endpoint works:
  ```
  curl https://voicecoach-chatbot.onrender.com/health
  ```
- [ ] Can create account (signup)
- [ ] Can login with credentials
- [ ] Auth tokens work correctly
- [ ] Chatbot responds to messages
- [ ] VoiceCoach WebSocket connects
- [ ] Database persists data correctly

### Performance & Monitoring
- [ ] Response times acceptable (<5s)
- [ ] No memory leaks (check Render metrics)
- [ ] Database connections stable
- [ ] CORS working (no browser errors)
- [ ] SSL certificates active (HTTPS)

### Security Verification
- [ ] All endpoints use HTTPS
- [ ] CORS restricted to trusted domains only
- [ ] Auth tokens expire correctly
- [ ] Password validation enforced
- [ ] No API keys exposed in responses/logs
- [ ] Database not publicly accessible
- [ ] Rate limiting working (if applicable)

---

## 🔧 Configuration Updates

### Update CORS After Deployment
Once services are deployed, update CORS to use actual URLs:

**VoiceCoach API:**
```
ALLOWED_ORIGINS=https://voicecoach-chatbot.onrender.com,https://your-frontend.com
```

**Web Chatbot:**
```
CORS_ORIGINS=https://voicecoach-api.onrender.com,https://your-frontend.com
```

### Update Frontend URLs
If you have a frontend application, update API URLs:
- VoiceCoach API: `https://voicecoach-api.onrender.com`
- Web Chatbot: `https://voicecoach-chatbot.onrender.com`

---

## 📊 Monitoring Setup

### Recommended Tools
- [ ] Set up Render email alerts (in service settings)
- [ ] Configure external uptime monitoring (e.g., UptimeRobot)
- [ ] Set up error tracking (e.g., Sentry - optional)
- [ ] Configure log aggregation (e.g., LogDNA - optional)
- [ ] Monitor API costs (OpenAI dashboard)

### Key Metrics to Watch
- [ ] Service uptime percentage
- [ ] Response time averages
- [ ] Error rates (4xx, 5xx)
- [ ] Database connection count
- [ ] API usage/costs (OpenAI, ElevenLabs, Qdrant)
- [ ] Memory usage trends
- [ ] Request volume

---

## 🐛 Troubleshooting Quick Reference

### Service Won't Start
1. Check logs in Render dashboard
2. Verify all environment variables set
3. Check build logs for dependency errors
4. Verify root directory path is correct

### Database Connection Failed
1. Verify DATABASE_URL is set
2. Check database is in same region as service
3. Ensure service is using correct connection string
4. Check database logs for errors

### Health Check Failing
1. Test endpoint locally: `curl http://localhost:8000/health`
2. Verify health check path in service settings
3. Check logs for startup errors
4. Ensure service binds to `0.0.0.0:$PORT`

### CORS Errors
1. Update ALLOWED_ORIGINS / CORS_ORIGINS
2. Include protocol (https://)
3. No trailing slashes in URLs
4. Restart service after changes

### Authentication Not Working
1. Verify SECRET_KEY, JWT_SECRET_KEY set
2. Check database connection
3. Test with curl commands
4. Review auth logs for errors

---

## 📝 Documentation Updates

After deployment, document:
- [ ] Production URLs for both services
- [ ] API endpoint URLs
- [ ] Database names and regions
- [ ] Monitoring dashboard links
- [ ] Admin credentials (store securely!)
- [ ] Support contacts
- [ ] Deployment dates and versions

---

## 🎯 Success Criteria

✅ **Deployment is successful when:**
- Both services show "Live" status
- Health checks return 200 OK
- Users can signup and login
- Chatbot responds to messages
- VoiceCoach voice chat works
- No critical errors in logs
- Response times < 5 seconds
- HTTPS working on all endpoints
- Database persistence confirmed

---

## 🔄 Rollback Plan

If deployment fails:
1. Go to Render service dashboard
2. Click "Events" tab
3. Find last successful deploy
4. Click "Rollback to this deploy"
5. Investigate issue in separate environment
6. Fix and redeploy

---

## 📞 Emergency Contacts

**Render Support:**
- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Status: https://status.render.com

**OpenAI Support:**
- Dashboard: https://platform.openai.com
- Status: https://status.openai.com

**Emergency Actions:**
- Disable service: Settings → "Suspend"
- Scale down: Settings → Change plan
- Enable maintenance mode: (implement custom endpoint)

---

## ✨ Final Steps

- [ ] Notify team of deployment
- [ ] Update documentation with production URLs
- [ ] Schedule first backup verification
- [ ] Set calendar reminder for monthly review
- [ ] Celebrate successful deployment! 🎉

---

**Deployment Checklist Version:** 1.0  
**Last Updated:** November 24, 2025

---

## 📋 Quick Command Reference

**Test Health Locally:**
```cmd
curl http://localhost:8000/health
curl http://localhost:5001/health
```

**Test Health Production:**
```cmd
curl https://voicecoach-api.onrender.com/health
curl https://voicecoach-chatbot.onrender.com/health
```

**Generate Secret Key:**
```cmd
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**View Logs (Render CLI):**
```cmd
render logs voicecoach-api --tail
render logs voicecoach-chatbot --tail
```

**Manual Deploy (Render CLI):**
```cmd
render deploy voicecoach-api
render deploy voicecoach-chatbot
```

---

Save this checklist and use it for every deployment! ✅
