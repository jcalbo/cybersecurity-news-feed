#!/usr/bin/env python3
"""
Startup script for MCP Server with SSE transport.
"""
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import mcp, get_elasticsearch_client
from mcp_server import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, CACHE_DURATION_MINUTES

if __name__ == "__main__":
    print("🚀 Starting MCP Server...")
    print(f"📊 Elasticsearch: {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
    print(f"⏱️  Cache duration: {CACHE_DURATION_MINUTES} minutes")
    
    try:
        es_client = get_elasticsearch_client(ELASTICSEARCH_HOST, ELASTICSEARCH_PORT)
        if es_client.health_check():
            print("✅ Elasticsearch connection successful")
            doc_count = es_client.count_documents()
            print(f"📚 Current documents in index: {doc_count}")
        else:
            print("⚠️  Elasticsearch health check failed")
    except Exception as e:
        print(f"⚠️  Could not connect to Elasticsearch: {e}")
    
    print("🌐 Starting SSE server on http://0.0.0.0:8000...")
    
    # Run with uvicorn for SSE support
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    
    # Create SSE app
    sse = SseServerTransport("/messages")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as streams:
            await mcp.run(
                streams[0],
                streams[1],
                mcp.create_initialization_options(),
            )
    
    async def health_check(request):
        from starlette.responses import JSONResponse
        return JSONResponse({"status": "healthy", "service": "cybersecurity_news_mcp"})
    
    app = Starlette(
        routes=[
            Route("/messages", endpoint=handle_sse),
            Route("/health", endpoint=health_check),
        ],
    )
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

