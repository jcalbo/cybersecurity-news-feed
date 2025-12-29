"""
Elasticsearch client for managing cybersecurity news articles.
"""
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from elasticsearch import Elasticsearch, helpers


class ElasticsearchNewsClient:
    """Client for interacting with Elasticsearch for news storage."""
    
    INDEX_NAME = "cybersecurity_news"
    
    def __init__(self, host: str = "localhost", port: int = 9200):
        """Initialize Elasticsearch client.
        
        Args:
            host: Elasticsearch host
            port: Elasticsearch port
        """
        self.es = Elasticsearch(
            [f"http://{host}:{port}"],
            request_timeout=30
        )
        self.index_name = self.INDEX_NAME
        
    def create_index(self):
        """Create the news index with appropriate mappings."""
        if self.es.indices.exists(index=self.index_name):
            print(f"Index '{self.index_name}' already exists")
            return
        
        index_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "link": {"type": "keyword"},
                    "description": {"type": "text"},
                    "published": {"type": "date"},
                    "source": {"type": "keyword"},
                    "author": {"type": "keyword"},
                    "fetched_at": {"type": "date"},
                    "raw_content": {"type": "text"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        }
        
        self.es.indices.create(index=self.index_name, body=index_mapping)
        print(f"✅ Created index '{self.index_name}'")
    
    def _generate_doc_id(self, news_item: Dict) -> str:
        """Generate a unique ID for a news item based on link.
        
        Args:
            news_item: News item dictionary
            
        Returns:
            Unique document ID
        """
        link = news_item.get("link", "")
        return hashlib.sha256(link.encode()).hexdigest()[:16]
    
    def store_news_item(self, news_item: Dict) -> bool:
        """Store a single news item in Elasticsearch.
        
        Args:
            news_item: News item dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            doc_id = self._generate_doc_id(news_item)
            
            # Prepare document
            doc = {
                "id": doc_id,
                "title": news_item.get("title"),
                "link": news_item.get("link"),
                "description": news_item.get("description"),
                "published": news_item.get("published").isoformat() if isinstance(news_item.get("published"), datetime) else news_item.get("published"),
                "source": news_item.get("source"),
                "author": news_item.get("author"),
                "fetched_at": datetime.now().isoformat()
            }
            
            # Use update with upsert to avoid duplicates
            self.es.update(
                index=self.index_name,
                id=doc_id,
                body={
                    "doc": doc,
                    "doc_as_upsert": True
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing news item: {e}")
            return False
    
    def bulk_store_news(self, news_items: List[Dict]) -> tuple:
        """Store multiple news items in bulk.
        
        Args:
            news_items: List of news item dictionaries
            
        Returns:
            Tuple of (success_count, failed_count)
        """
        if not news_items:
            return (0, 0)
        
        actions = []
        for item in news_items:
            doc_id = self._generate_doc_id(item)
            
            doc = {
                "_index": self.index_name,
                "_id": doc_id,
                "_source": {
                    "id": doc_id,
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "description": item.get("description"),
                    "published": item.get("published").isoformat() if isinstance(item.get("published"), datetime) else item.get("published"),
                    "source": item.get("source"),
                    "author": item.get("author"),
                    "fetched_at": datetime.now().isoformat()
                }
            }
            actions.append(doc)
        
        try:
            success, failed = helpers.bulk(
                self.es,
                actions,
                raise_on_error=False,
                stats_only=False
            )
            
            success_count = len(news_items) - len(failed) if failed else len(news_items)
            failed_count = len(failed) if failed else 0
            
            print(f"✅ Stored {success_count} news items, {failed_count} failed")
            return (success_count, failed_count)
            
        except Exception as e:
            print(f"Error in bulk storage: {e}")
            return (0, len(news_items))
    
    def get_news(
        self,
        hours: Optional[int] = None,
        sources: Optional[List[str]] = None,
        search: Optional[str] = None,
        size: int = 100
    ) -> List[Dict]:
        """Retrieve news from Elasticsearch with filters.
        
        Args:
            hours: Filter news from last N hours
            sources: Filter by specific sources
            search: Search term for title/description
            size: Maximum number of results
            
        Returns:
            List of news items
        """
        query = {"bool": {"must": []}}
        
        # Time filter
        if hours:
            query["bool"]["must"].append({
                "range": {
                    "published": {
                        "gte": f"now-{hours}h",
                        "lte": "now"
                    }
                }
            })
        
        # Source filter
        if sources:
            query["bool"]["must"].append({
                "terms": {"source": sources}
            })
        
        # Search filter
        if search:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search,
                    "fields": ["title^2", "description"],
                    "type": "best_fields"
                }
            })
        
        # If no filters, match all
        if not query["bool"]["must"]:
            query = {"match_all": {}}
        
        try:
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": query,
                    "sort": [{"published": {"order": "desc"}}],
                    "size": size
                }
            )
            
            news_items = []
            for hit in response["hits"]["hits"]:
                item = hit["_source"]
                # Convert published back to datetime for consistency
                if "published" in item:
                    item["published"] = datetime.fromisoformat(item["published"].replace('Z', '+00:00'))
                news_items.append(item)
            
            return news_items
            
        except Exception as e:
            print(f"Error retrieving news: {e}")
            return []
    
    def get_latest_fetch_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent fetch.
        
        Returns:
            Datetime of latest fetch, or None if no data
        """
        try:
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": {"match_all": {}},
                    "sort": [{"fetched_at": {"order": "desc"}}],
                    "size": 1
                }
            )
            
            if response["hits"]["hits"]:
                fetched_at = response["hits"]["hits"][0]["_source"]["fetched_at"]
                return datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
            
            return None
            
        except Exception as e:
            print(f"Error getting latest fetch time: {e}")
            return None
    
    def count_documents(self) -> int:
        """Count total documents in index.
        
        Returns:
            Number of documents
        """
        try:
            response = self.es.count(index=self.index_name)
            return response["count"]
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0
    
    def health_check(self) -> bool:
        """Check if Elasticsearch is healthy and index exists.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.es.ping():
                return False
            
            if not self.es.indices.exists(index=self.index_name):
                self.create_index()
            
            return True
            
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Singleton instance
_es_client: Optional[ElasticsearchNewsClient] = None


def get_elasticsearch_client(host: str = "localhost", port: int = 9200) -> ElasticsearchNewsClient:
    """Get or create Elasticsearch client singleton.
    
    Args:
        host: Elasticsearch host
        port: Elasticsearch port
        
    Returns:
        ElasticsearchNewsClient instance
    """
    global _es_client
    
    if _es_client is None:
        _es_client = ElasticsearchNewsClient(host=host, port=port)
        _es_client.health_check()
    
    return _es_client

