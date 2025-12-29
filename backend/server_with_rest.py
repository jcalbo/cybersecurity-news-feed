#!/usr/bin/env python3
"""
MCP Server with REST API wrapper for Streamlit frontend.
Runs both MCP (SSE) and REST API on the same port.
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import MCP server functions
from mcp_server import (
    _fetch_all_feeds,
    _filter_by_time,
    _filter_by_search,
    _filter_by_sources,
    _format_json,
    _format_markdown,
    RSS_FEEDS,
)

# Create FastAPI app
app = FastAPI(title="Cybersecurity News API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class GetNewsRequest(BaseModel):
    hours: Optional[int] = 24
    sources: Optional[List[str]] = None
    search: Optional[str] = None
    response_format: str = "json"


class ListSourcesRequest(BaseModel):
    response_format: str = "json"


# REST API Endpoints
@app.get("/")
async def root():
    return {
        "service": "Cybersecurity News API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "get_news": "/api/news",
            "list_sources": "/api/sources",
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cybersecurity_news_api"}


@app.post("/api/news")
async def get_news(request: GetNewsRequest):
    """Get cybersecurity news with filters."""
    try:
        # Fetch news from RSS feeds
        news_items = await _fetch_all_feeds()
        
        # Apply filters
        filtered_news = _filter_by_time(news_items, request.hours)
        filtered_news = _filter_by_search(filtered_news, request.search)
        filtered_news = _filter_by_sources(filtered_news, request.sources)
        
        # Sort by publication date (newest first)
        filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
        
        # Format response
        if request.response_format == "markdown":
            return {"content": _format_markdown(filtered_news)}
        else:
            import json
            return json.loads(_format_json(filtered_news))
            
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/sources")
async def list_sources():
    """List all available news sources."""
    try:
        sources = [
            {"name": name, "feed_url": url}
            for name, url in RSS_FEEDS.items()
        ]
        return {
            "total_sources": len(sources),
            "sources": sources
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("🚀 Starting Cybersecurity News API Server...")
    print("📡 REST API: http://0.0.0.0:8000")
    print("📰 Endpoints:")
    print("  - GET  /health")
    print("  - POST /api/news")
    print("  - GET  /api/sources")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

