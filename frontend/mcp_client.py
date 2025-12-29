"""
MCP Client for communicating with the MCP Server via HTTP/SSE.
"""
import json
import requests
from typing import Dict, List, Optional, Any


class MCPClient:
    """Client for interacting with MCP Server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize MCP client.
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url.rstrip('/')
        self.tools_endpoint = f"{self.base_url}/tools"
        self.call_endpoint = f"{self.base_url}/call"
        
    def _call_tool(self, tool_name: str, params: Dict = None) -> Any:
        """Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            
        Returns:
            Tool response
            
        Raises:
            Exception: If the request fails
        """
        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params or {}
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/message",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract content from MCP response
            if "content" in result:
                if isinstance(result["content"], list) and len(result["content"]) > 0:
                    return result["content"][0].get("text", "")
                return result["content"]
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"MCP request failed: {str(e)}")
    
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
        params = {
            "hours": hours,
            "response_format": response_format
        }
        
        if sources:
            params["sources"] = sources
        
        if search:
            params["search"] = search
        
        try:
            result = self._call_tool("get_news", params)
            
            # If response_format is json, parse it
            if response_format == "json":
                if isinstance(result, str):
                    return json.loads(result)
                return result
            
            return {"content": result}
            
        except Exception as e:
            return {"error": str(e)}
    
    def list_sources(self, response_format: str = "json") -> Dict:
        """List available news sources.
        
        Args:
            response_format: 'json' or 'markdown'
            
        Returns:
            Dict with sources or error
        """
        params = {"response_format": response_format}
        
        try:
            result = self._call_tool("list_sources", params)
            
            if response_format == "json":
                if isinstance(result, str):
                    return json.loads(result)
                return result
            
            return {"content": result}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_elasticsearch_stats(self) -> Dict:
        """Get Elasticsearch statistics.
        
        Returns:
            Dict with Elasticsearch stats or error
        """
        try:
            result = self._call_tool("get_elasticsearch_stats", {})
            
            if isinstance(result, str):
                return json.loads(result)
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check if MCP server is healthy.
        
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
_mcp_client: Optional[MCPClient] = None


def get_mcp_client(base_url: str = "http://localhost:8000") -> MCPClient:
    """Get or create MCP client singleton.
    
    Args:
        base_url: Base URL of the MCP server
        
    Returns:
        MCPClient instance
    """
    global _mcp_client
    
    if _mcp_client is None:
        _mcp_client = MCPClient(base_url=base_url)
    
    return _mcp_client

