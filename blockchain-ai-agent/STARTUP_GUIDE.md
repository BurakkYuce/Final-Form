# Startup Guide - Sui Blockchain AI Agent

## Quick Start Commands

### Method 1: Direct Python (Recommended)
```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
python main.py
```

### Method 2: Uvicorn Command
```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Use Startup Scripts

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

---

## Why This Works

Because we're using **relative imports**, you need to:
1. Be in the `blockchain-ai-agent` directory
2. Use `main:app` (NOT `blockchain-ai-agent.main:app`)

### Breakdown of `uvicorn main:app`:
- `main` = the file `main.py`
- `app` = the FastAPI instance variable in that file
- No package name needed because we're running from the project directory

---

## Common Mistakes ❌

### ❌ WRONG:
```bash
uvicorn blockchain-ai-agent.main:app
# Error: Invalid module name (hyphens not allowed)
```

### ❌ WRONG:
```bash
uvicorn blockchain_ai_agent.main:app
# Error: Module not found (no such package)
```

### ✅ CORRECT:
```bash
cd blockchain-ai-agent
uvicorn main:app
```

---

## Full Command Options

### Development Mode (Auto-reload on code changes):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
```

### Production Mode:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning
```

### Custom Port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Only Localhost (More Secure):
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Environment Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Make sure `.env` file exists with your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Verify Setup
```bash
python verify_imports.py
```

Should show:
```
[OK] All imports successful!
[OK] Application is ready to run
```

---

## Accessing the Application

Once started, access:

| Endpoint | URL | Description |
|----------|-----|-------------|
| API Root | http://localhost:8000 | Service info |
| Swagger UI | http://localhost:8000/docs | Interactive API docs |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/api/v1/health | Health status |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'main'"
**Solution:** Make sure you're in the correct directory:
```bash
cd C:\Users\byrock\Desktop\a\blockchain-ai-agent
pwd  # Should show: .../blockchain-ai-agent
```

### Issue: "ModuleNotFoundError: No module named 'config'"
**Solution:** Dependencies not installed:
```bash
pip install -r requirements.txt
```

### Issue: "pydantic_core._pydantic_core.ValidationError"
**Solution:** Missing environment variables. Check your `.env` file:
```bash
# .env must contain:
OPENAI_API_KEY=sk-proj-...
```

### Issue: Port already in use
**Solution:** Kill the process or use a different port:
```bash
# Use different port
uvicorn main:app --port 8001

# Or kill existing process (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Using with Gunicorn (Production)

For production deployment with multiple workers:

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 worker processes
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

---

## Using with Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t sui-ai-agent .
docker run -p 8000:8000 --env-file .env sui-ai-agent
```

---

## Logs and Monitoring

### View Logs
Uvicorn outputs to stdout. To save logs:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > app.log 2>&1
```

### Log Levels
```bash
--log-level debug    # Most verbose
--log-level info     # Default
--log-level warning  # Warnings only
--log-level error    # Errors only
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `python main.py` |
| Start with uvicorn | `uvicorn main:app --reload` |
| Check imports | `python verify_imports.py` |
| Test health | `curl http://localhost:8000/api/v1/health` |
| View docs | Open `http://localhost:8000/docs` |
| Stop server | `Ctrl+C` |

---

## Next Steps

1. ✅ Start the server using one of the methods above
2. ✅ Open http://localhost:8000/docs in your browser
3. ✅ Test the `/api/v1/health` endpoint
4. ✅ Try the chat endpoint with a test message
5. ✅ Read `API_TESTING.md` for more examples

---

**Happy Building! 🚀**
