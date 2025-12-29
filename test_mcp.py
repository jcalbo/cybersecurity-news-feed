#!/usr/bin/env python3
"""
Simple test script for the MCP server.
Run this to test the server functions directly.
"""
import asyncio
import sys
sys.path.insert(0, '/home/jorge/Desktop/jalvarez/cybersecurity-news-feed')

from mcp_server import (
    _fetch_all_feeds,
    _filter_by_time,
    _filter_by_search,
    _filter_by_sources,
    _format_markdown,
    _format_json,
    RSS_FEEDS,
    ResponseFormat
)


async def test_list_sources():
    """Test listing all sources."""
    print("=" * 80)
    print("TEST 1: List all sources")
    print("=" * 80)
    
    output = ["# Available Cybersecurity News Sources\n"]
    for i, (name, url) in enumerate(RSS_FEEDS.items(), 1):
        output.append(f"{i}. **{name}**")
        output.append(f"   - Feed URL: `{url}`\n")
    result = "\n".join(output)
    print(result)
    print()


async def test_get_all_news():
    """Test getting all news from last 24 hours."""
    print("=" * 80)
    print("TEST 2: Get all news (last 24 hours)")
    print("=" * 80)
    
    news_items = await _fetch_all_feeds()
    filtered_news = _filter_by_time(news_items, 24)
    filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
    result = _format_markdown(filtered_news[:5])  # Show first 5 only
    print(result)
    print()


async def test_search_news():
    """Test searching for specific topics."""
    print("=" * 80)
    print("TEST 3: Search for 'malware' news")
    print("=" * 80)
    
    news_items = await _fetch_all_feeds()
    filtered_news = _filter_by_time(news_items, 48)
    filtered_news = _filter_by_search(filtered_news, "malware")
    filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
    result = _format_markdown(filtered_news[:5])  # Show first 5 only
    print(result)
    print()


async def test_filter_by_source():
    """Test filtering by specific source."""
    print("=" * 80)
    print("TEST 4: Get news from BleepingComputer only")
    print("=" * 80)
    
    news_items = await _fetch_all_feeds()
    filtered_news = _filter_by_time(news_items, 24)
    filtered_news = _filter_by_sources(filtered_news, ["BleepingComputer"])
    filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
    result = _format_markdown(filtered_news[:5])  # Show first 5 only
    print(result)
    print()


async def test_json_format():
    """Test JSON output format."""
    print("=" * 80)
    print("TEST 5: Get news in JSON format")
    print("=" * 80)
    
    news_items = await _fetch_all_feeds()
    filtered_news = _filter_by_time(news_items, 12)
    filtered_news = sorted(filtered_news, key=lambda x: x["published"], reverse=True)
    result = _format_json(filtered_news[:3])  # Show first 3 only
    print(result)
    print()


async def main():
    """Run all tests."""
    print("\n🚀 Testing Cybersecurity News MCP Server\n")
    
    # Run tests
    await test_list_sources()
    await test_get_all_news()
    await test_search_news()
    await test_filter_by_source()
    await test_json_format()
    
    print("=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

