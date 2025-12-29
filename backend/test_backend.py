#!/usr/bin/env python3
"""
Test script to verify backend functionality.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from elasticsearch_client import get_elasticsearch_client
from mcp_server import _fetch_all_feeds, GetNewsInput, get_news


async def test_elasticsearch():
    """Test Elasticsearch connection and operations."""
    print("=" * 80)
    print("TEST 1: Elasticsearch Connection")
    print("=" * 80)
    
    try:
        es_client = get_elasticsearch_client("localhost", 9200)
        
        if es_client.health_check():
            print("✅ Elasticsearch connection successful")
            doc_count = es_client.count_documents()
            print(f"📚 Current documents: {doc_count}")
            
            latest_fetch = es_client.get_latest_fetch_time()
            if latest_fetch:
                print(f"⏰ Latest fetch: {latest_fetch}")
            else:
                print("📭 No data fetched yet")
            
            return True
        else:
            print("❌ Elasticsearch health check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_rss_fetch():
    """Test fetching from RSS feeds."""
    print("\n" + "=" * 80)
    print("TEST 2: RSS Feed Fetching")
    print("=" * 80)
    
    try:
        print("Fetching news from RSS feeds...")
        news_items = await _fetch_all_feeds()
        
        print(f"✅ Fetched {len(news_items)} news items")
        
        if news_items:
            print("\nSample item:")
            item = news_items[0]
            print(f"  Title: {item['title'][:60]}...")
            print(f"  Source: {item['source']}")
            print(f"  Published: {item['published']}")
            
        return len(news_items) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_elasticsearch_storage():
    """Test storing news in Elasticsearch."""
    print("\n" + "=" * 80)
    print("TEST 3: Store News in Elasticsearch")
    print("=" * 80)
    
    try:
        # Fetch fresh news
        news_items = await _fetch_all_feeds()
        print(f"📥 Fetched {len(news_items)} items")
        
        # Store in Elasticsearch
        es_client = get_elasticsearch_client("localhost", 9200)
        success, failed = es_client.bulk_store_news(news_items)
        
        print(f"✅ Stored: {success}, ❌ Failed: {failed}")
        
        # Verify storage
        doc_count = es_client.count_documents()
        print(f"📚 Total documents in index: {doc_count}")
        
        return success > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_mcp_get_news():
    """Test the MCP get_news tool."""
    print("\n" + "=" * 80)
    print("TEST 4: MCP get_news Tool")
    print("=" * 80)
    
    try:
        params = GetNewsInput(
            hours=24,
            response_format="json"
        )
        
        print("Calling get_news tool...")
        result = await get_news(params)
        
        print(f"✅ Result length: {len(result)} characters")
        
        # Try to parse JSON result
        import json
        data = json.loads(result)
        print(f"📰 Found {data.get('total_count', 0)} articles")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n🧪 Backend Integration Tests\n")
    
    results = []
    
    # Test 1: Elasticsearch connection
    results.append(await test_elasticsearch())
    
    # Test 2: RSS fetching
    results.append(await test_rss_fetch())
    
    # Test 3: Elasticsearch storage
    results.append(await test_elasticsearch_storage())
    
    # Test 4: MCP tool
    results.append(await test_mcp_get_news())
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Backend is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    asyncio.run(main())

