"""
Simple REST API client for communicating with the backend.
"""
import requests
from typing import Dict, List, Optional


class NewsAPIClient:
    """Client for interacting with Cybersecurity News API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url.rstrip('/')
        
    def get_news(
        self,
        hours: int = 24,
        sources: Optional[List[str]] = None,
        search: Optional[str] = None,
        response_format: str = "json"
    ) -> Dict:
        """Get cybersecurity news.
        
        Args:
            hours: Filter news from last N hours
            sources: Filter by specific sources
            search: Search term
            response_format: 'json' or 'markdown'
            
        Returns:
            Dict with news data or error
        """
        payload = {
            "hours": hours,
            "response_format": response_format
        }
        
        if sources:
            payload["sources"] = sources
        
        if search:
            payload["search"] = search
        
        try:
            response = requests.post(
                f"{self.base_url}/api/news",
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_sources(self) -> Dict:
        """List available news sources.
            
        Returns:
            Dict with sources or error
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/sources",
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check if API server is healthy.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# Singleton instance
_api_client: Optional[NewsAPIClient] = None


def get_api_client(base_url: str = "http://localhost:8000") -> NewsAPIClient:
    """Get or create API client singleton.
    
    Args:
        base_url: Base URL of the API server
        
    Returns:
        NewsAPIClient instance
    """
    global _api_client
    
    if _api_client is None:
        _api_client = NewsAPIClient(base_url=base_url)
    
    return _api_client

