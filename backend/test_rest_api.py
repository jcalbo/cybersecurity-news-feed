#!/usr/bin/env python3
"""
Test script for REST API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sources():
    print("\nTesting /api/sources endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/sources", timeout=10)
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"Total sources: {data.get('total_sources', 0)}")
        for source in data.get('sources', [])[:3]:
            print(f"  - {source['name']}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_news():
    print("\nTesting /api/news endpoint...")
    try:
        payload = {
            "hours": 24,
            "response_format": "json"
        }
        response = requests.post(f"{BASE_URL}/api/news", json=payload, timeout=60)
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        
        if "total_count" in data:
            print(f"Total articles: {data['total_count']}")
            if data['news_items']:
                first = data['news_items'][0]
                print(f"First article: {first['title'][:60]}...")
        elif "error" in data:
            print(f"❌ Error in response: {data['error']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Cybersecurity News REST API\n")
    print(f"Server: {BASE_URL}\n")
    print("="*60)
    
    test_health()
    test_sources()
    test_news()
    
    print("\n" + "="*60)
    print("✅ Tests complete!")


