# Deployment Checklist

Quick checklist to get your Sui Blockchain AI Agent up and running.

## ☑️ Pre-Deployment

### 1. System Requirements
- [ ] Python 3.12+ installed
- [ ] pip installed
- [ ] Virtual environment support
- [ ] Internet connection (for OpenAI, Sui RPC, Walrus)

### 2. API Keys & Configuration
- [ ] OpenAI API key obtained from https://platform.openai.com
- [ ] `.env` file created (copy from `.env.example`)
- [ ] `OPENAI_API_KEY` added to `.env`
- [ ] Sui RPC URL verified (default: testnet)
- [ ] Walrus URLs verified (default: testnet)

### 3. Dependencies
- [ ] Virtual environment created: `python -m venv venv`
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip install -r requirements.txt`

## 🚀 Deployment Steps

### Step 1: Clone/Download Project
```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
```

### Step 2: Setup Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
```bash
# Copy example file
cp .env.example .env

# Edit .env and add:
# OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 5: Test Configuration
```bash
python -c "from config import settings; print('✅ Configuration loaded successfully')"
```

### Step 6: Start Server
```bash
# Option 1: Direct
python main.py

# Option 2: Using start script
# Windows: start.bat
# Linux/Mac: ./start.sh
```

### Step 7: Verify Running
Open browser to:
- http://localhost:8000 (API root)
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/api/v1/health (Health check)

## ✅ Post-Deployment Verification

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Sui Blockchain AI Agent",
  "version": "1.0.0-mvp"
}
```

### 2. Test OpenAI Integration
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my SUI balance?",
    "user_address": "0x0000000000000000000000000000000000000000000000000000000000000000"
  }'
```

Should return AI response (not error).

### 3. Test Walrus Integration
```bash
curl -X POST http://localhost:8000/api/v1/contacts/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "contact_name": "Test Contact",
    "contact_address": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
  }'
```

Should return blob_id.

### 4. Test Full Flow
```bash
# Save contact
curl -X POST http://localhost:8000/api/v1/contacts/save \
  -H "Content-Type: application/json" \
  -d '{"user_address": "0x1234...", "contact_name": "Alice", "contact_address": "0xabcd..."}'

# Transfer to contact
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Send 100 SUI to Alice", "user_address": "0x1234..."}'
```

Should return dry-run summary.

## 🔧 Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution:**
1. Check `.env` file exists in project root
2. Verify key is set: `OPENAI_API_KEY=sk-proj-...`
3. Restart server

### Issue: "Failed to connect to Sui RPC"
**Solution:**
1. Check internet connection
2. Verify `SUI_RPC_URL` in `.env`
3. Test RPC: `curl https://fullnode.testnet.sui.io:443`

### Issue: "Walrus upload failed"
**Solution:**
1. Check Walrus testnet status
2. Verify URLs in `.env`:
   - `WALRUS_PUBLISHER_URL`
   - `WALRUS_AGGREGATOR_URL`
3. Check network connectivity

### Issue: "Module not found" errors
**Solution:**
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: "Port 8000 already in use"
**Solution:**
1. Change port in `.env`: `API_PORT=8001`
2. Or kill process using port 8000
3. Restart server

## 📊 Monitoring

### Check Logs
Server logs appear in console. Look for:
- ✅ "Application started successfully!"
- ✅ "Uvicorn running on http://0.0.0.0:8000"

### Monitor API Calls
Use Swagger UI: http://localhost:8000/docs
- Interactive API testing
- Request/response inspection
- Schema validation

### Performance
- Normal response time: 1-3 seconds
- OpenAI calls: 0.5-2 seconds
- Walrus operations: 0.5-1 second
- Sui RPC: 0.2-0.5 seconds

## 🎯 Production Deployment

For production deployment beyond MVP:

### 1. Environment
- [ ] Use production OpenAI key with rate limits
- [ ] Use Sui mainnet RPC
- [ ] Use Walrus mainnet
- [ ] Set `DEBUG=False`
- [ ] Set `LOG_LEVEL=WARNING`

### 2. Security
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Add authentication
- [ ] Add rate limiting
- [ ] Configure CORS for specific domains

### 3. Persistence
- [ ] Setup SQLite or PostgreSQL
- [ ] Migrate contact storage to database
- [ ] Implement backup strategy

### 4. Monitoring
- [ ] Setup application logging
- [ ] Configure error tracking (Sentry)
- [ ] Monitor API metrics
- [ ] Setup health check monitoring

### 5. Deployment Platform
```bash
# Using Uvicorn with Gunicorn (production)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Or using Docker
docker build -t sui-ai-agent .
docker run -p 8000:8000 sui-ai-agent
```

## ✅ Final Checklist

- [ ] Server starts without errors
- [ ] Health check endpoint responds
- [ ] OpenAI integration working
- [ ] Sui RPC connection established
- [ ] Walrus upload/download working
- [ ] API documentation accessible
- [ ] All endpoints responding correctly

## 🎉 Success!

If all checks pass, your Sui Blockchain AI Agent is ready to use!

Next steps:
1. Read `README.md` for feature overview
2. Check `API_TESTING.md` for testing examples
3. Review `IMPLEMENTATION_SUMMARY.md` for architecture details

**Happy Building! 🚀**
