import re
import json
from enum import Enum
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import aiohttp
import asyncio
import feedparser
from fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Initialize MCP server
mcp = FastMCP("cybersecurity_news_mcp")

# RSS Feed sources
RSS_FEEDS = {
    "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
    "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
    "Wiz Blog": "https://www.wiz.io/feed/rss.xml",
    "StepSecurity": "https://www.stepsecurity.io/blog/rss.xml",
    "ReversingLabs": "https://www.reversinglabs.com/blog/rss.xml",
}


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


async def _fetch_feed(session: aiohttp.ClientSession, name: str, url: str) -> List[Dict]:
    """Fetch and parse a single RSS feed."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            content = await response.text()
            feed = feedparser.parse(content)

            news_items = []
            for entry in feed.entries:
                # Extract publication date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    pub_date = datetime.now()

                # Extract description
                description = ""
                if hasattr(entry, "description"):
                    description = entry.description
                elif hasattr(entry, "summary"):
                    description = entry.summary

                # Clean HTML tags from description
                description = re.sub(r"<[^>]+>", "", description).strip()

                news_items.append(
                    {
                        "title": entry.title if hasattr(entry, "title") else "Untitled",
                        "link": entry.link if hasattr(entry, "link") else "",
                        "description": description[:300] + "..." if len(description) > 300 else description,
                        "published": pub_date,
                        "source": name,
                        "author": entry.author if hasattr(entry, "author") else name,
                    }
                )

            return news_items

    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []


async def _fetch_all_feeds() -> List[Dict]:
    """Fetch all RSS feeds concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [_fetch_feed(session, name, url) for name, url in RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks)

        # Combine all results
        all_news = []
        for news_list in results:
            all_news.extend(news_list)

        return all_news


def _filter_by_time(news_items: List[Dict], hours: Optional[int]) -> List[Dict]:
    """Filter news by time period."""
    if hours is None:
        return news_items

    cutoff_time = datetime.now() - timedelta(hours=hours)
    return [item for item in news_items if item["published"] >= cutoff_time]


def _filter_by_search(news_items: List[Dict], search_term: Optional[str]) -> List[Dict]:
    """Filter news by search term."""
    if not search_term:
        return news_items

    search_term = search_term.lower()
    return [item for item in news_items if search_term in item["title"].lower() or search_term in item["description"].lower()]


def _filter_by_sources(news_items: List[Dict], sources: Optional[List[str]]) -> List[Dict]:
    """Filter news by sources."""
    if not sources:
        return news_items

    return [item for item in news_items if item["source"] in sources]


def _format_time_ago(published: datetime) -> str:
    """Convert datetime to human-readable time ago string."""
    time_diff = datetime.now() - published
    if time_diff.days > 0:
        return f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
    elif time_diff.seconds >= 3600:
        hours = time_diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    else:
        minutes = time_diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"


def _format_markdown(news_items: List[Dict]) -> str:
    """Format news items as markdown."""
    if not news_items:
        return "No news items found matching your criteria."

    output = [f"# Cybersecurity News ({len(news_items)} articles)\n"]

    for item in news_items:
        time_ago = _format_time_ago(item["published"])
        output.append(f"## {item['title']}")
        output.append(f"**Source:** {item['source']} | **Published:** {time_ago}")
        output.append(f"**Link:** {item['link']}")
        output.append(f"\n{item['description']}\n")
        output.append("---\n")

    return "\n".join(output)


def _format_json(news_items: List[Dict]) -> str:
    """Format news items as JSON."""
    # Create serializable copy
    serializable_items = []
    for item in news_items:
        item_copy = item.copy()
        if "published" in item_copy and isinstance(item_copy["published"], datetime):
            item_copy["published"] = item_copy["published"].isoformat()
            item_copy["time_ago"] = _format_time_ago(item["published"])
        serializable_items.append(item_copy)

    result = {"total_count": len(serializable_items), "news_items": serializable_items}
    return json.dumps(result, indent=2, ensure_ascii=False)


# =============================================================================
# MCP Tools
# =============================================================================
class GetNewsInput(BaseModel):
    """Input parameters for getting cybersecurity news."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    hours: int | None = Field(
        default=24, description="Filter news from the last N hours (e.g., 12, 24, 48). Default: 24 hours", ge=1, le=720
    )
    sources: List[str] | None = Field(
        default=None, description=f"Filter by specific sources. Available: {', '.join(RSS_FEEDS.keys())}", max_length=len(RSS_FEEDS)
    )
    search: str | None = Field(default=None, description="Search term to filter news by title or description", max_length=200)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'")

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate that all sources are known."""
        if v is not None:
            invalid_sources = [s for s in v if s not in RSS_FEEDS]
            if invalid_sources:
                raise ValueError(f"Invalid sources: {', '.join(invalid_sources)}. " f"Available: {', '.join(RSS_FEEDS.keys())}")
        return v


@mcp.tool(
    name="get_news",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def get_news(params: GetNewsInput) -> str:
    """Get cybersecurity news from multiple trusted sources.

    Fetches and filters cybersecurity news from BleepingComputer, The Hacker News,
    Wiz Blog, StepSecurity, and ReversingLabs.

    Args:
        params (GetNewsInput): Filtering parameters:
            - hours (int): Filter news from last N hours (default: 24)
            - sources (List[str]): Filter by specific sources (optional)
            - search (str): Search term for title/description (optional)
            - response_format (str): Output format - 'markdown' or 'json'

    Returns:
        str: Formatted news articles with title, link, source, and description.
    """
    try:
        # Fetch news from all feeds
        news_items = await _fetch_all_feeds()

        # Apply filters
        filtered_news = _filter_by_time(news_items, params.hours)
        filtered_news = _filter_by_search(filtered_news, params.search)
        filtered_news = _filter_by_sources(filtered_news, params.sources)

        # Sort by publication date (newest first)
        filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)

        # Format output
        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_markdown(filtered_news)
        else:
            return _format_json(filtered_news)

    except Exception as e:
        return f"Error: Failed to retrieve news: {type(e).__name__}: {str(e)}"


class ListSourcesInput(BaseModel):
    """Input parameters for listing available news sources."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' or 'json'")


@mcp.tool(
    name="list_sources",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def list_sources(params: ListSourcesInput) -> str:
    """List all available cybersecurity news sources.

    Returns information about all configured news sources and their RSS feeds.

    Args:
        params (ListSourcesInput): Output formatting:
            - response_format (str): Output format - 'markdown' or 'json'

    Returns:
        str: List of available news sources with their RSS feed URLs.
    """
    try:
        if params.response_format == ResponseFormat.MARKDOWN:
            output = ["# Available Cybersecurity News Sources\n"]
            for i, (name, url) in enumerate(RSS_FEEDS.items(), 1):
                output.append(f"{i}. **{name}**")
                output.append(f"   - Feed URL: `{url}`\n")
            return "\n".join(output)
        else:
            result = {"total_sources": len(RSS_FEEDS), "sources": [{"name": name, "feed_url": url} for name, url in RSS_FEEDS.items()]}
            return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error: Failed to list sources: {type(e).__name__}: {str(e)}"


if __name__ == "__main__":
#    mcp.run(transport="sse")
    mcp.run(transport="stdio")
    

