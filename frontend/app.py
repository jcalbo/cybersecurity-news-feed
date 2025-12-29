import os
from datetime import datetime
from typing import List, Dict

import streamlit as st
from mcp_client import get_mcp_client

# Configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Cybersecurity News Feed - MCP Client",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .news-item {
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        border-left: 4px solid #4CAF50;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)


def format_time_ago(published_str: str) -> str:
    """Format ISO timestamp to human-readable time ago."""
    try:
        if isinstance(published_str, str):
            # Remove timezone info if present
            published_str = published_str.replace('Z', '+00:00')
            published = datetime.fromisoformat(published_str)
        else:
            published = published_str
        
        time_diff = datetime.now() - published.replace(tzinfo=None)
        
        if time_diff.days > 0:
            return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds >= 3600:
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    except:
        return "Unknown"


def display_news_item(item: Dict):
    """Display a single news item."""
    time_ago = format_time_ago(item.get("published", ""))
    
    st.markdown(f"### [{item['title']}]({item['link']})")
    st.markdown(
        f"**Source:** {item['source']} | **Author:** {item.get('author', 'Unknown')} | "
        f"**Published:** {time_ago}"
    )
    st.markdown(item['description'])
    st.markdown("---")


def display_connection_status(mcp_client):
    """Display MCP server connection status."""
    with st.sidebar:
        st.subheader("🔌 Connection Status")
        
        is_healthy = mcp_client.health_check()
        
        if is_healthy:
            st.success("✅ Connected to MCP Server")
        else:
            st.error("❌ Cannot connect to MCP Server")
            st.info(f"Server URL: {MCP_SERVER_URL}")
            
        # Get Elasticsearch stats
        try:
            stats = mcp_client.get_elasticsearch_stats()
            if "error" not in stats:
                st.subheader("📊 Elasticsearch Stats")
                st.metric("Total Documents", stats.get("total_documents", 0))
                
                latest_fetch = stats.get("latest_fetch")
                if latest_fetch:
                    st.text(f"Last fetch: {format_time_ago(latest_fetch)}")
                else:
                    st.text("No data fetched yet")
        except Exception as e:
            st.warning(f"Could not get ES stats: {e}")


def main():
    """Main application."""
    
    # Header
    st.title("🔒 Cybersecurity News Feed")
    st.markdown("**Powered by MCP Server & Elasticsearch**")
    
    # Initialize MCP client
    mcp_client = get_mcp_client(MCP_SERVER_URL)
    
    # Display connection status
    display_connection_status(mcp_client)
    
    # Sidebar - Filters
    with st.sidebar:
        st.header("⚙️ Filters")
        
        # Time filter
        st.subheader("📅 Time Period")
        time_filter = st.radio(
            "Show news from:",
            ["Last 12 hours", "Last 24 hours", "Last 48 hours", "Last week", "All time"],
            index=1
        )
        
        time_map = {
            "Last 12 hours": 12,
            "Last 24 hours": 24,
            "Last 48 hours": 48,
            "Last week": 168,
            "All time": 720
        }
        
        # Get available sources
        sources_result = mcp_client.list_sources()
        available_sources = []
        
        if "error" not in sources_result and "sources" in sources_result:
            available_sources = [s["name"] for s in sources_result["sources"]]
        else:
            # Fallback to known sources
            available_sources = [
                "BleepingComputer",
                "The Hacker News",
                "Wiz Blog",
                "StepSecurity",
                "ReversingLabs"
            ]
        
        # Source filter
        st.subheader("📰 Sources")
        selected_sources = st.multiselect(
            "Select sources:",
            options=available_sources,
            default=available_sources
        )
        
        # Search
        st.subheader("🔍 Search")
        search_term = st.text_input("Search keyword:", "")
        
        if search_term:
            st.caption(f"🔍 Searching: '{search_term}'")
        
        # Sorting
        st.subheader("📊 Sorting")
        sort_order = st.radio(
            "Sort by:",
            ["Newest first", "Oldest first"]
        )
        
        # Refresh button
        st.markdown("---")
        if st.button("🔄 Fetch News", use_container_width=True, type="primary"):
            st.rerun()
    
    # Fetch news
    with st.spinner("Fetching news from MCP server..."):
        result = mcp_client.get_news(
            hours=time_map[time_filter],
            sources=selected_sources if selected_sources else None,
            search=search_term if search_term else None,
            response_format="json"
        )
    
    # Handle errors
    if "error" in result:
        st.error(f"❌ Error fetching news: {result['error']}")
        st.info("💡 Make sure the MCP server is running on http://localhost:8000")
        return
    
    # Get news items
    news_items = result.get("news_items", [])
    
    # Sort
    reverse = sort_order == "Newest first"
    news_items = sorted(
        news_items,
        key=lambda x: x.get("published", ""),
        reverse=reverse
    )
    
    # Statistics
    st.markdown("### 📊 Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📰 Total Articles", len(news_items))
    
    with col2:
        sources_count = len(set(item["source"] for item in news_items))
        st.metric("📡 Active Sources", sources_count)
    
    with col3:
        # Count from last 24h
        recent_count = sum(
            1 for item in news_items
            if format_time_ago(item.get("published", "")).endswith(("hour ago", "hours ago", "minute ago", "minutes ago"))
        )
        st.metric("🆕 Last 24h", recent_count)
    
    st.markdown("---")
    
    # Display news
    if news_items:
        st.markdown(f"### 📰 Showing {len(news_items)} article{'s' if len(news_items) > 1 else ''}")
        
        for item in news_items:
            display_news_item(item)
    else:
        st.warning("⚠️ No news items found matching your criteria.")
        st.info("💡 Try adjusting your filters or force refresh to fetch new data.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<div style='text-align: center; color: gray;'>"
        f"🔒 Cybersecurity News Feed via MCP Server | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

