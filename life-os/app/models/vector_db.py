import weaviate
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json
from ..config import settings

logger = logging.getLogger(__name__)

class WeaviateClient:
    def __init__(self):
        self.client = None
        self.class_name = "LifeOSMemory"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Weaviate client with authentication"""
        try:
            auth_config = None
            if settings.WEAVIATE_API_KEY:
                auth_config = weaviate.auth.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
            
            self.client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=auth_config,
                timeout_config=(5, 15)
            )
            
            # Check if schema exists, create if not
            self._setup_schema()
            logger.info("Weaviate client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Weaviate client: {e}")
            raise
    
    def _setup_schema(self):
        """Set up the schema for multimodal memory storage"""
        try:
            # Check if class already exists
            schema = self.client.schema.get()
            existing_classes = [cls['class'] for cls in schema.get('classes', [])]
            
            if self.class_name not in existing_classes:
                class_definition = {
                    "class": self.class_name,
                    "description": "Memory storage for Life OS with multimodal support",
                    "vectorizer": "text2vec-openai",
                    "moduleConfig": {
                        "text2vec-openai": {
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text"
                        }
                    },
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Main content of the memory"
                        },
                        {
                            "name": "content_type",
                            "dataType": ["string"],
                            "description": "Type of content: text, image, audio, document"
                        },
                        {
                            "name": "user_id",
                            "dataType": ["string"],
                            "description": "WhatsApp user ID"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "When the memory was created"
                        },
                        {
                            "name": "media_url",
                            "dataType": ["string"],
                            "description": "URL to associated media file"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["object"],
                            "description": "Additional metadata as JSON"
                        },
                        {
                            "name": "entities",
                            "dataType": ["string[]"],
                            "description": "Extracted entities from content"
                        },
                        {
                            "name": "sentiment",
                            "dataType": ["string"],
                            "description": "Sentiment analysis result"
                        },
                        {
                            "name": "keywords",
                            "dataType": ["string[]"],
                            "description": "Extracted keywords"
                        }
                    ]
                }
                
                self.client.schema.create_class(class_definition)
                logger.info(f"Created schema for class: {self.class_name}")
        
        except Exception as e:
            logger.error(f"Failed to setup schema: {e}")
            raise
    
    async def store_memory(self, 
                          content: str,
                          content_type: str,
                          user_id: str,
                          media_url: Optional[str] = None,
                          metadata: Optional[Dict] = None,
                          entities: Optional[List[str]] = None,
                          sentiment: Optional[str] = None,
                          keywords: Optional[List[str]] = None) -> str:
        """Store a memory in the vector database"""
        
        try:
            data_object = {
                "content": content,
                "content_type": content_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "media_url": media_url or "",
                "metadata": json.dumps(metadata or {}),
                "entities": entities or [],
                "sentiment": sentiment or "neutral",
                "keywords": keywords or []
            }
            
            # Store in Weaviate
            result = self.client.data_object.create(
                data_object=data_object,
                class_name=self.class_name
            )
            
            logger.info(f"Stored memory with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def search_memories(self, 
                             query: str,
                             user_id: Optional[str] = None,
                             content_type: Optional[str] = None,
                             limit: int = 10,
                             min_certainty: float = 0.7) -> List[Dict[str, Any]]:
        """Search for relevant memories using hybrid search"""
        
        try:
            # Build the query
            query_builder = (
                self.client.query
                .get(self.class_name, [
                    "content", "content_type", "user_id", "timestamp",
                    "media_url", "metadata", "entities", "sentiment", "keywords"
                ])
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )
            
            # Add filters if specified
            where_conditions = []
            if user_id:
                where_conditions.append({
                    "path": ["user_id"],
                    "operator": "Equal",
                    "valueString": user_id
                })
            
            if content_type:
                where_conditions.append({
                    "path": ["content_type"],
                    "operator": "Equal", 
                    "valueString": content_type
                })
            
            if where_conditions:
                if len(where_conditions) == 1:
                    query_builder = query_builder.with_where(where_conditions[0])
                else:
                    query_builder = query_builder.with_where({
                        "operator": "And",
                        "operands": where_conditions
                    })
            
            # Execute query
            result = query_builder.do()
            
            # Process results
            memories = []
            if "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][self.class_name]:
                    certainty = item.get("_additional", {}).get("certainty", 0)
                    if certainty >= min_certainty:
                        memory = {
                            "content": item["content"],
                            "content_type": item["content_type"],
                            "user_id": item["user_id"],
                            "timestamp": item["timestamp"],
                            "media_url": item["media_url"],
                            "metadata": json.loads(item["metadata"]) if item["metadata"] else {},
                            "entities": item["entities"],
                            "sentiment": item["sentiment"],
                            "keywords": item["keywords"],
                            "certainty": certainty
                        }
                        memories.append(memory)
            
            logger.info(f"Found {len(memories)} relevant memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def get_recent_memories(self, 
                                 user_id: str,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent memories for a user"""
        
        try:
            result = (
                self.client.query
                .get(self.class_name, [
                    "content", "content_type", "user_id", "timestamp",
                    "media_url", "metadata", "entities", "sentiment", "keywords"
                ])
                .with_where({
                    "path": ["user_id"],
                    "operator": "Equal",
                    "valueString": user_id
                })
                .with_sort([{"path": ["timestamp"], "order": "desc"}])
                .with_limit(limit)
                .do()
            )
            
            memories = []
            if "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][self.class_name]:
                    memory = {
                        "content": item["content"],
                        "content_type": item["content_type"],
                        "user_id": item["user_id"],
                        "timestamp": item["timestamp"],
                        "media_url": item["media_url"],
                        "metadata": json.loads(item["metadata"]) if item["metadata"] else {},
                        "entities": item["entities"],
                        "sentiment": item["sentiment"],
                        "keywords": item["keywords"]
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []
    
    def close(self):
        """Close the Weaviate client connection"""
        if self.client:
            self.client = None
            logger.info("Weaviate client connection closed") 