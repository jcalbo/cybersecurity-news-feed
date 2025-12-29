# 🔧 Fixed Setup Guide

## ✅ Problem Solved!

Your backend was using **STDIO transport** (designed for CLI tools like Claude Desktop), but your Streamlit frontend needed **HTTP/REST communication**.

## 🏗️ New Architecture

```
┌──────────────┐
│   Frontend   │  Streamlit UI
│  (Port 8501) │
└──────┬───────┘
       │ HTTP REST
       ↓
┌──────────────┐
│   REST API   │  FastAPI Server
│  (Port 8000) │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  RSS Feeds   │  News Sources
└──────────────┘
```

## 🚀 **How to Run (NEW)**

### Terminal 1 - Backend (REST API)

```bash
cd backend

# Install dependencies (first time only)
uv sync

# Run the REST API server
uv run python server_with_rest.py
```

**Expected Output:**
```
🚀 Starting Cybersecurity News API Server...
📡 REST API: http://0.0.0.0:8000
📰 Endpoints:
  - GET  /health
  - POST /api/news
  - GET  /api/sources

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 2 - Frontend (Streamlit)

```bash
cd frontend

# Install dependencies (first time only)
uv sync

# Run the Streamlit frontend
uv run streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 📋 **What Changed**

### Backend Changes

1. **Fixed `mcp_server.py`**
   - Changed transport from `stdio` to `sse`
   - Now properly configured for MCP clients

2. **Added `server_with_rest.py`** (NEW - Use This!)
   - FastAPI REST API server
   - Simple HTTP endpoints
   - Easy for frontend to consume

3. **Added `test_rest_api.py`**
   - Test script for REST API
   - Run: `uv run python test_rest_api.py`

### Frontend Changes

1. **Added `api_client.py`** (NEW)
   - Simple HTTP client
   - Replaces complex MCP client

2. **Updated `app.py`**
   - Uses `api_client` instead of `mcp_client`
   - Connects to REST API endpoints

---

## 🔌 **API Endpoints**

### Health Check
```bash
GET http://localhost:8000/health
```

### Get News
```bash
POST http://localhost:8000/api/news
Content-Type: application/json

{
  "hours": 24,
  "sources": ["BleepingComputer"],
  "search": "ransomware",
  "response_format": "json"
}
```

### List Sources
```bash
GET http://localhost:8000/api/sources
```

---

## 🧪 **Testing**

### Test Backend API
```bash
cd backend

# Start the server in another terminal first!
# Then run:
uv run python test_rest_api.py
```

Expected output:
```
🧪 Testing Cybersecurity News REST API

Testing /health endpoint...
✅ Status: 200
Response: {'status': 'healthy', 'service': 'cybersecurity_news_api'}

Testing /api/sources endpoint...
✅ Status: 200
Total sources: 5
  - BleepingComputer
  - The Hacker News
  - Wiz Blog

Testing /api/news endpoint...
✅ Status: 200
Total articles: 150
First article: Fortinet warns of 5-year-old FortiOS 2FA bypass...

✅ Tests complete!
```

### Test Frontend
1. Start backend: `cd backend && uv run python server_with_rest.py`
2. Start frontend: `cd frontend && uv run streamlit run app.py`
3. Open http://localhost:8501 in browser
4. Check sidebar shows "✅ Connected to Backend API"
5. Click "🔄 Fetch News"

---

## ❓ **FAQs**

### Q: What about the MCP server?

**A:** The MCP server (`mcp_server.py`) is still there with SSE transport for AI assistants like Claude Desktop. But for the Streamlit frontend, we now use the simpler REST API (`server_with_rest.py`).

### Q: Which server should I run?

**For Streamlit Frontend:**
- ✅ Run `server_with_rest.py` (REST API)

**For MCP Clients (Claude, Cline, etc.):**
- ✅ Run `mcp_server.py` (MCP with SSE)

### Q: Can I run both?

**A:** Not on the same port! They both use port 8000. Choose one:
- For development with Streamlit → use `server_with_rest.py`
- For MCP clients → use `mcp_server.py`

### Q: Where's Elasticsearch?

**A:** You removed it earlier (which is fine!). The system now works directly with RSS feeds without caching. If you want Elasticsearch back, we can add it to the REST API later.

---

## 🎯 **Quick Commands**

### Start Backend (REST API)
```bash
cd backend && uv run python server_with_rest.py
```

### Start Frontend
```bash
cd frontend && uv run streamlit run app.py
```

### Test Backend
```bash
cd backend && uv run python test_rest_api.py
```

### View Logs
Backend logs show in Terminal 1
Frontend logs show in Terminal 2

---

## ✅ **Verification Checklist**

- [ ] Backend starts on port 8000
- [ ] Can access http://localhost:8000/health
- [ ] Frontend starts on port 8501
- [ ] Sidebar shows "✅ Connected to Backend API"
- [ ] Can click "Fetch News" and see articles
- [ ] Can filter by time, source, search

---

## 🚨 **Troubleshooting**

### "Cannot connect to Backend API"

**Solutions:**
1. Make sure backend is running: `cd backend && uv run python server_with_rest.py`
2. Check port 8000 is not in use: `lsof -i :8000`
3. Try accessing http://localhost:8000/health in browser

### "Port already in use"

**Solution:**
```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>

# Then restart backend
cd backend && uv run python server_with_rest.py
```

### "Module not found"

**Solution:**
```bash
# Backend
cd backend && uv sync

# Frontend
cd frontend && uv sync
```

---

## 📚 **Summary**

✅ **Backend:** Simple REST API with FastAPI  
✅ **Frontend:** Streamlit UI with HTTP client  
✅ **Communication:** Standard HTTP/REST (no complex MCP protocol)  
✅ **Fast:** UV package manager for quick installs  
✅ **Simple:** Easy to understand and extend  

**Your system is now working! 🎉**

