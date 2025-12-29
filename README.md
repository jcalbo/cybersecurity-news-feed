# 🔒 Cybersecurity News Feed

A real-time cybersecurity news aggregator powered by **MCP (Model Context Protocol)** server, **Streamlit** frontend, and **Elasticsearch** for persistence.

## 🌟 Features

- **Multi-Source Aggregation**: Fetches news from 5 trusted cybersecurity sources
- **MCP Server Backend**: RESTful API following Model Context Protocol with SSE support
- **Streamlit Frontend**: Interactive web interface with advanced filtering
- **Elasticsearch Storage**: Persistent news storage with full-text search capabilities
- **Real-time Updates**: Automatic feed refresh with intelligent caching (10-minute cache)
- **Advanced Filtering**: Filter by time period, source, and search terms
- **Microservices Architecture**: Separate frontend and backend services ready for containerization

## 📰 News Sources

- **BleepingComputer** - Breaking cybersecurity news and security alerts
- **The Hacker News** - Latest hacking news and cyber security updates
- **Wiz Blog** - Cloud security insights and research
- **StepSecurity** - Software supply chain security news
- **ReversingLabs** - Threat intelligence and malware analysis

## 🏗️ Architecture

```
┌─────────────────┐
│   User Browser   │
└────────┬─────────┘
         │ HTTP (8501)
         ↓
┌─────────────────┐
│ Streamlit       │  Frontend
│ Frontend        │  - User Interface
│ (Port 8501)     │  - Filters & Search
└────────┬─────────┘
         │ HTTP/SSE (8000)
         ↓
┌─────────────────┐
│ MCP Server      │  Backend
│ Backend         │  - MCP Protocol
│ (Port 8000)     │  - RSS Aggregation
└────────┬─────────┘
         │ HTTP (9200)
         ↓
┌─────────────────┐
│ Elasticsearch   │  Storage
│ (Port 9200)     │  - News Persistence
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Elasticsearch 8.x running on port 9200
- pip or uv package manager

### 1. Start Elasticsearch (if not running)

```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.15.2
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp env.example .env
# Edit .env if needed

# Run backend server
python3 mcp_server.py
```

The MCP server will start on `http://localhost:8000`

### 3. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp env.example .env
# Edit .env if needed

# Run frontend
streamlit run app.py
```

The frontend will open in your browser at `http://localhost:8501`

## 🛠️ Tech Stack

### Backend
- **FastMCP** - MCP server framework
- **aiohttp** - Async HTTP client for RSS feeds
- **feedparser** - RSS feed parsing
- **Elasticsearch** (8.15.0) - Search and storage
- **Pydantic** - Data validation
- **uvicorn** - ASGI server

### Frontend
- **Streamlit** - Web UI framework
- **requests** - HTTP client for MCP communication

### Infrastructure
- **Elasticsearch** 8.15.2 - Document store and search engine

## 📁 Project Structure

```
cybersecurity-news-feed/
│
├── backend/                    # MCP Server (Backend)
│   ├── mcp_server.py          # Main MCP server with tools
│   ├── elasticsearch_client.py # Elasticsearch integration
│   ├── test_backend.py        # Backend integration tests
│   ├── requirements.txt       # Backend dependencies
│   └── env.example            # Environment configuration template
│
├── frontend/                   # Streamlit Frontend
│   ├── app.py                 # Streamlit UI application
│   ├── mcp_client.py          # MCP HTTP client
│   ├── requirements.txt       # Frontend dependencies
│   └── env.example            # Environment configuration template
│
├── demo/                       # Demo videos
│   ├── mcp.mp4                # MCP server demo
│   └── streamlit.mp4          # Frontend demo
│
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# Elasticsearch Configuration
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Cache Configuration
CACHE_DURATION_MINUTES=10

# MCP Server Configuration
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=0.0.0.0
```

### Frontend Environment Variables

Create `frontend/.env`:

```bash
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000

# Streamlit Configuration
STREAMLIT_PORT=8501
REQUEST_TIMEOUT=60
```

## 📡 MCP Server API

The backend provides three MCP tools:

### 1. `get_news`

Get cybersecurity news with filters.

**Parameters:**
- `hours` (int, optional): Filter news from last N hours (default: 24, max: 720)
- `sources` (List[str], optional): Filter by specific sources
- `search` (str, optional): Search term for title/description
- `response_format` (str): Output format - 'markdown' or 'json' (default: 'markdown')

**Example:**
```python
{
  "hours": 24,
  "sources": ["BleepingComputer", "The Hacker News"],
  "search": "ransomware",
  "response_format": "json"
}
```

### 2. `list_sources`

List all available news sources.

**Parameters:**
- `response_format` (str): Output format - 'markdown' or 'json'

### 3. `get_elasticsearch_stats`

Get statistics about stored news in Elasticsearch.

**Returns:** JSON with document count, last fetch time, and configuration.

## 🧪 Testing

### Test Backend

```bash
cd backend
python3 test_backend.py
```

This will test:
- Elasticsearch connection
- RSS feed fetching
- Data storage in Elasticsearch
- MCP tool functionality

### Manual Testing

1. **Check Elasticsearch:**
   ```bash
   curl http://localhost:9200
   curl http://localhost:9200/cybersecurity_news/_count
   ```

2. **Test MCP Server:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Test Frontend:**
   Open http://localhost:8501 in your browser

## 📊 Features in Detail

### Frontend Features
- **Time Filtering**: Last 12h, 24h, 48h, week, or all time
- **Source Filtering**: Select specific news sources
- **Full-Text Search**: Search in titles and descriptions
- **Sorting**: Newest or oldest first
- **Statistics**: Total articles, active sources, recent news count
- **Connection Status**: Real-time MCP server connection indicator
- **Elasticsearch Stats**: View cached documents and last fetch time

### Backend Features
- **Intelligent Caching**: 10-minute cache in Elasticsearch
- **Bulk Operations**: Efficient bulk storage of news items
- **Duplicate Prevention**: SHA-256 based deduplication
- **Health Checks**: Automatic Elasticsearch health monitoring
- **Concurrent Fetching**: Async RSS feed fetching for speed
- **Error Handling**: Robust error handling and logging

## 🐳 Docker Deployment (Coming Soon)

The application is structured for easy containerization:

```bash
# Build and run all services
docker-compose up -d

# Individual services
docker-compose up elasticsearch  # Port 9200
docker-compose up backend       # Port 8000
docker-compose up frontend      # Port 8501
```

## 🔐 Security Considerations

- The Elasticsearch instance in this setup has security disabled for development
- For production, enable X-Pack security and use authentication
- Configure firewalls to restrict access to internal services
- Use HTTPS for frontend-backend communication in production

## 📝 Development

### Adding New RSS Sources

Edit `backend/mcp_server.py`:

```python
RSS_FEEDS = {
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "Your New Source": "https://example.com/feed.rss",
    # ... more sources
}
```

### Customizing Cache Duration

Edit `backend/.env`:

```bash
CACHE_DURATION_MINUTES=30  # Change to desired minutes
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

MIT License - feel free to use this project for your own purposes.

## 👤 Author

**Jorge Alvarez**

## 🙏 Acknowledgments

- FastMCP team for the excellent MCP framework
- Elasticsearch for powerful search capabilities
- Streamlit for the intuitive UI framework
- All the cybersecurity news sources for their valuable content

## 📚 Additional Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Model Context Protocol](https://modelcontextprotocol.io)

---

**Made with ❤️ for the cybersecurity community**
