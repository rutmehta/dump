import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from cachetools import LRUCache
import json
import redis
from ..models.vector_db import WeaviateClient
from ..models.knowledge_graph import Neo4jClient
from ..config import settings

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        self.vector_db = WeaviateClient()
        self.knowledge_graph = Neo4jClient()
        self.cache = LRUCache(maxsize=settings.LRU_CACHE_SIZE)
        self.redis_client = None
        self._initialize_redis()
        
        # Check database availability for demo mode info
        self.demo_mode = not (self.vector_db.client and self.knowledge_graph.driver)
        if self.demo_mode:
            logger.info("🎭 Memory Manager running in DEMO MODE - databases not connected")
        else:
            logger.info("🗄️  Memory Manager running with full database support")
    
    def _initialize_redis(self):
        """Initialize Redis client for session management"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            # Continue without Redis - will use local cache only
    
    async def store_memory(self, 
                          content: str,
                          content_type: str,
                          user_id: str,
                          media_url: Optional[str] = None,
                          ai_response: Optional[Dict] = None) -> str:
        """Store a complete memory with vector, graph, and metadata"""
        
        try:
            memory_id = str(uuid.uuid4())
            
            # Extract data from AI response
            entities = ai_response.get('entities', []) if ai_response else []
            concepts = ai_response.get('concepts', []) if ai_response else []
            sentiment = ai_response.get('sentiment', 'neutral') if ai_response else 'neutral'
            keywords = ai_response.get('keywords', []) if ai_response else []
            relationships = ai_response.get('relationships', []) if ai_response else []
            metadata = ai_response.get('metadata', {}) if ai_response else {}
            
            # Enhanced metadata with new SDK capabilities
            enhanced_metadata = {
                **metadata,
                "model_used": ai_response.get("model_used", settings.DEFAULT_MODEL),
                "context_length": ai_response.get("context_length", 0),
                "sdk_version": "new_genai",
                "processing_capabilities": {
                    "multimodal": True,
                    "long_context": settings.ENABLE_LONG_CONTEXT,
                    "video_support": settings.ENABLE_VIDEO_PROCESSING,
                    "native_audio": settings.ENABLE_AUDIO_NATIVE
                }
            }
            
            # Store in vector database
            await self.vector_db.store_memory(
                content=content,
                content_type=content_type,
                user_id=user_id,
                media_url=media_url,
                metadata=enhanced_metadata,
                entities=entities,
                sentiment=sentiment,
                keywords=keywords
            )
            
            # Store in knowledge graph
            await self.knowledge_graph.create_user_node(user_id)
            await self.knowledge_graph.create_memory_node(
                memory_id=memory_id,
                user_id=user_id,
                content=content,
                content_type=content_type,
                entities=entities,
                metadata=enhanced_metadata
            )
            
            # Create concept relationships
            if relationships:
                concept_tuples = [
                    (rel['concept1'], rel['concept2'], rel.get('strength', 0.5))
                    for rel in relationships
                ]
                await self.knowledge_graph.create_concept_relationships(concept_tuples)
            
            # Update cache
            cache_key = f"memory:{memory_id}"
            memory_data = {
                "id": memory_id,
                "content": content,
                "content_type": content_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "entities": entities,
                "concepts": concepts,
                "sentiment": sentiment,
                "keywords": keywords,
                "enhanced_metadata": enhanced_metadata
            }
            self.cache[cache_key] = memory_data
            
            # Store session context in Redis
            if self.redis_client:
                await self._update_session_context(user_id, memory_data)
            
            logger.info(f"Stored memory {memory_id} for user {user_id} with enhanced capabilities")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def retrieve_context(self, 
                              query: str,
                              user_id: str,
                              k: int = None,
                              include_graph: bool = True,
                              use_long_context: bool = None) -> List[Dict[str, Any]]:
        """Enhanced hybrid context retrieval using vector similarity + graph traversal"""
        
        # Use enhanced defaults from settings
        if k is None:
            k = settings.VECTOR_SEARCH_LIMIT
        
        if use_long_context is None:
            use_long_context = settings.ENABLE_LONG_CONTEXT
        
        # Increase context size for long context mode
        if use_long_context:
            k = min(k * 2, settings.CONTEXT_MEMORY_LIMIT)
        
        try:
            # Check cache first
            cache_key = f"context:{user_id}:{hash(query)}:{k}:{include_graph}"
            if cache_key in self.cache:
                logger.debug(f"Retrieved context from cache for user {user_id}")
                return self.cache[cache_key]
            
            # Enhanced vector-based retrieval
            vector_memories = await self.vector_db.search_memories(
                query=query,
                user_id=user_id,
                limit=k//2,
                min_certainty=0.65  # Slightly lower threshold for more context
            )
            
            # Enhanced graph-based concept retrieval
            graph_concepts = []
            if include_graph:
                query_concepts = self._extract_query_concepts(query)
                for concept in query_concepts:
                    related = await self.knowledge_graph.find_related_concepts(
                        concept=concept,
                        depth=settings.GRAPH_TRAVERSE_DEPTH,
                        limit=8  # Increased for better relationships
                    )
                    graph_concepts.extend(related)
            
            # Get more recent memories for enhanced temporal context
            recent_memories = await self.vector_db.get_recent_memories(
                user_id=user_id,
                limit=k//3
            )
            
            # Combine and rank results with enhanced scoring
            all_memories = self._combine_and_rank_memories(
                vector_memories, 
                recent_memories,
                graph_concepts,
                query,
                use_long_context
            )
            
            # Apply enhanced temporal relevance scoring
            ranked_memories = self._apply_temporal_scoring(all_memories, use_long_context)
            
            # Limit to top k results
            final_memories = ranked_memories[:k]
            
            # Cache the results
            self.cache[cache_key] = final_memories
            
            logger.info(f"Retrieved {len(final_memories)} contextual memories for user {user_id} (long_context: {use_long_context})")
            return final_memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
    
    async def get_proactive_context(self, 
                                   user_id: str,
                                   current_input: str = "",
                                   max_memories: int = None) -> List[Dict[str, Any]]:
        """Enhanced proactive context retrieval leveraging larger context windows"""
        
        if max_memories is None:
            max_memories = settings.CONTEXT_MEMORY_LIMIT
        
        try:
            # Get trending entities for the user
            trending_entities = await self.knowledge_graph.get_trending_entities(
                user_id=user_id,
                days=7,
                limit=15  # Increased for better trend analysis
            )
            
            # Get entity network for relationship-based retrieval
            entity_network = await self.knowledge_graph.get_user_entity_network(
                user_id=user_id,
                limit=20  # Increased for richer entity understanding
            )
            
            # Enhanced proactive query building
            proactive_query_parts = []
            if current_input:
                proactive_query_parts.append(current_input)
            
            # Add trending entity names with weights
            trending_names = [entity['entity'] for entity in trending_entities[:8]]
            proactive_query_parts.extend(trending_names)
            
            # Add highly connected entities
            if entity_network:
                connected_entities = [entity['entity'] for entity in entity_network[:5]]
                proactive_query_parts.extend(connected_entities)
            
            proactive_query = " ".join(proactive_query_parts)
            
            # Retrieve memories using the enhanced proactive query
            memories = await self.retrieve_context(
                query=proactive_query,
                user_id=user_id,
                k=max_memories,
                include_graph=True,
                use_long_context=True
            )
            
            # Enhance with cross-memory connections
            enhanced_memories = await self._add_memory_connections(memories, user_id)
            
            logger.info(f"Retrieved {len(enhanced_memories)} proactive context memories with enhanced capabilities")
            return enhanced_memories
            
        except Exception as e:
            logger.error(f"Failed to get proactive context: {e}")
            return []
    
    async def _add_memory_connections(self, 
                                    memories: List[Dict], 
                                    user_id: str) -> List[Dict[str, Any]]:
        """Add connection information between memories with enhanced analysis"""
        
        enhanced_memories = []
        for memory in memories:
            memory_id = memory.get('id', '')
            if memory_id:
                connections = await self.knowledge_graph.find_memory_connections(
                    memory_id=memory_id,
                    user_id=user_id,
                    limit=5  # Increased for richer connections
                )
                memory['connections'] = connections
                
                # Add enhanced metadata if available
                if 'enhanced_metadata' in memory:
                    memory['sdk_capabilities'] = memory['enhanced_metadata'].get('processing_capabilities', {})
            
            enhanced_memories.append(memory)
        
        return enhanced_memories
    
    def _extract_query_concepts(self, query: str) -> List[str]:
        """Enhanced concept extraction for better graph traversal"""
        import re
        from collections import Counter
        
        # Extract meaningful words (3+ characters)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        
        # Enhanced stop words list
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 
            'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 
            'two', 'who', 'boy', 'did', 'man', 'too', 'way', 'she', 'use',
            'will', 'been', 'from', 'they', 'have', 'said', 'each', 'which',
            'what', 'were', 'when', 'where', 'more', 'some', 'like', 'into',
            'time', 'very', 'then', 'come', 'back', 'only', 'think', 'also'
        }
        
        concepts = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Enhanced concept scoring with frequency and position
        word_freq = Counter(concepts)
        concept_scores = {}
        
        for i, concept in enumerate(concepts):
            # Position weight (earlier words get higher weight)
            position_weight = 1.0 - (i / len(concepts)) * 0.3
            frequency_weight = word_freq[concept]
            concept_scores[concept] = position_weight * frequency_weight
        
        # Return top concepts sorted by score
        top_concepts = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)
        return [concept for concept, score in top_concepts[:8]]
    
    def _combine_and_rank_memories(self, 
                                  vector_memories: List[Dict],
                                  recent_memories: List[Dict],
                                  graph_concepts: List[Dict],
                                  query: str,
                                  use_long_context: bool = False) -> List[Dict[str, Any]]:
        """Enhanced memory combination and ranking with improved scoring"""
        
        combined = {}
        
        # Enhanced scoring weights for long context mode
        semantic_weight = 0.7 if not use_long_context else 0.6
        temporal_weight = 0.3 if not use_long_context else 0.25
        graph_weight = 0.2 if not use_long_context else 0.25
        
        # Add vector memories with enhanced semantic weight
        for memory in vector_memories:
            mem_id = memory.get('timestamp', '') + memory.get('content', '')[:50]
            certainty = memory.get('certainty', 0.5)
            memory['score'] = certainty * semantic_weight
            memory['source'] = 'vector'
            combined[mem_id] = memory
        
        # Add recent memories with enhanced temporal weight
        for memory in recent_memories:
            mem_id = memory.get('timestamp', '') + memory.get('content', '')[:50]
            if mem_id in combined:
                combined[mem_id]['score'] += temporal_weight  # Boost if also semantically relevant
            else:
                memory['score'] = temporal_weight
                memory['source'] = 'temporal'
                combined[mem_id] = memory
        
        # Enhanced graph concept boosting
        for concept_data in graph_concepts:
            concept = concept_data.get('concept', '')
            strength = concept_data.get('strength', 0.5)
            
            for mem_id, memory in combined.items():
                content_lower = memory.get('content', '').lower()
                entities_lower = [e.lower() for e in memory.get('entities', [])]
                keywords_lower = [k.lower() for k in memory.get('keywords', [])]
                
                # Enhanced matching with entities and keywords
                concept_matches = 0
                if concept.lower() in content_lower:
                    concept_matches += 2
                if concept.lower() in entities_lower:
                    concept_matches += 3
                if concept.lower() in keywords_lower:
                    concept_matches += 1
                
                if concept_matches > 0:
                    boost = strength * graph_weight * concept_matches
                    combined[mem_id]['score'] += boost
        
        # Convert to list and sort by enhanced score
        ranked_memories = list(combined.values())
        ranked_memories.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return ranked_memories
    
    def _apply_temporal_scoring(self, memories: List[Dict], use_long_context: bool = False) -> List[Dict[str, Any]]:
        """Enhanced temporal relevance scoring with configurable decay"""
        
        current_time = datetime.utcnow()
        
        # Adjust decay factors for long context mode
        base_decay = 0.9 if not use_long_context else 0.95  # Slower decay for long context
        recent_boost = 1.5 if not use_long_context else 1.3
        
        for memory in memories:
            try:
                timestamp_str = memory.get('timestamp', '')
                if timestamp_str:
                    memory_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    time_diff = (current_time - memory_time).total_seconds() / 86400  # Days
                    
                    # Enhanced temporal factor calculation
                    temporal_factor = base_decay ** time_diff
                    
                    # Boost very recent memories (< 1 hour)
                    if time_diff < 1/24:
                        temporal_factor *= recent_boost
                    # Moderate boost for recent memories (< 24 hours)
                    elif time_diff < 1:
                        temporal_factor *= (recent_boost * 0.8)
                    # Small boost for memories within a week
                    elif time_diff < 7:
                        temporal_factor *= 1.1
                    
                    # Enhanced score combination
                    original_score = memory.get('score', 0.5)
                    context_weight = 0.7 if not use_long_context else 0.65
                    temporal_influence = 1.0 - context_weight
                    
                    memory['score'] = (original_score * context_weight) + (temporal_factor * temporal_influence)
                    memory['temporal_factor'] = temporal_factor
                    memory['time_diff_days'] = time_diff
                    
            except Exception as e:
                logger.debug(f"Enhanced temporal scoring failed for memory: {e}")
                continue
        
        # Re-sort by updated scores
        memories.sort(key=lambda x: x.get('score', 0), reverse=True)
        return memories
    
    async def _update_session_context(self, user_id: str, memory_data: Dict):
        """Enhanced session context update with richer metadata"""
        try:
            if not self.redis_client:
                return
            
            session_key = f"session:{user_id}"
            
            # Enhanced memory data for session storage
            session_memory = {
                **memory_data,
                "session_timestamp": datetime.utcnow().isoformat(),
                "context_window_support": settings.MAX_CONTEXT_TOKENS,
                "sdk_version": "enhanced_genai"
            }
            
            # Add new memory to session
            memory_json = json.dumps(session_memory)
            self.redis_client.lpush(session_key, memory_json)
            
            # Keep more memories in session for enhanced context
            session_limit = min(75, settings.CONTEXT_MEMORY_LIMIT * 2)
            self.redis_client.ltrim(session_key, 0, session_limit - 1)
            
            # Extended expiration for richer context retention
            self.redis_client.expire(session_key, 172800)  # 48 hours
            
        except Exception as e:
            logger.error(f"Failed to update enhanced session context: {e}")
    
    async def get_session_context(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get enhanced session context from Redis"""
        if limit is None:
            limit = settings.CONTEXT_MEMORY_LIMIT
            
        try:
            if not self.redis_client:
                return []
            
            session_key = f"session:{user_id}"
            context_data = self.redis_client.lrange(session_key, 0, limit - 1)
            
            session_memories = []
            for data in context_data:
                try:
                    memory = json.loads(data)
                    session_memories.append(memory)
                except json.JSONDecodeError:
                    continue
            
            logger.debug(f"Retrieved {len(session_memories)} session memories with enhanced context")
            return session_memories
            
        except Exception as e:
            logger.error(f"Failed to get enhanced session context: {e}")
            return []
    
    async def get_memory_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate enhanced insights about user's memory patterns"""
        try:
            # Get trending entities with enhanced analysis
            trending = await self.knowledge_graph.get_trending_entities(
                user_id=user_id,
                days=30,
                limit=25
            )
            
            # Get enhanced entity network
            entity_network = await self.knowledge_graph.get_user_entity_network(
                user_id=user_id,
                limit=40
            )
            
            # Get more recent memory stats for better analysis
            recent_memories = await self.vector_db.get_recent_memories(
                user_id=user_id,
                limit=150
            )
            
            # Enhanced pattern analysis
            content_types = {}
            sentiments = {'positive': 0, 'negative': 0, 'neutral': 0}
            sdk_capabilities = {'multimodal': 0, 'long_context': 0, 'video': 0, 'audio': 0}
            
            for memory in recent_memories:
                content_type = memory.get('content_type', 'text')
                content_types[content_type] = content_types.get(content_type, 0) + 1
                
                sentiment = memory.get('sentiment', 'neutral')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                
                # Analyze SDK capabilities usage
                metadata = memory.get('metadata', {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                capabilities = metadata.get('processing_capabilities', {})
                if capabilities.get('multimodal'):
                    sdk_capabilities['multimodal'] += 1
                if capabilities.get('long_context'):
                    sdk_capabilities['long_context'] += 1
                if capabilities.get('video_support'):
                    sdk_capabilities['video'] += 1
                if capabilities.get('native_audio'):
                    sdk_capabilities['audio'] += 1
            
            enhanced_insights = {
                "trending_entities": trending[:15],
                "entity_network_size": len(entity_network),
                "total_memories": len(recent_memories),
                "content_type_distribution": content_types,
                "sentiment_distribution": sentiments,
                "sdk_capabilities_usage": sdk_capabilities,
                "most_connected_entities": entity_network[:8] if entity_network else [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "enhanced_features": {
                    "long_context_enabled": settings.ENABLE_LONG_CONTEXT,
                    "video_processing_enabled": settings.ENABLE_VIDEO_PROCESSING,
                    "native_audio_enabled": settings.ENABLE_AUDIO_NATIVE,
                    "max_context_tokens": settings.MAX_CONTEXT_TOKENS,
                    "context_memory_limit": settings.CONTEXT_MEMORY_LIMIT
                }
            }
            
            return enhanced_insights
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced memory insights: {e}")
            return {}
    
    async def cleanup_old_memories(self, days: int = 365):
        """Enhanced cleanup with better retention policies"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            logger.info(f"Enhanced memory cleanup requested for memories older than {days} days")
            logger.info(f"Current configuration: {settings.MAX_CONTEXT_TOKENS:,} token context window")
            
            # Enhanced cleanup implementation would go here
            # - Selective cleanup based on memory importance
            # - Preserve high-value memories regardless of age
            # - Archive rather than delete for long-term insights
            
        except Exception as e:
            logger.error(f"Enhanced memory cleanup failed: {e}")
    
    def close(self):
        """Close all database connections"""
        try:
            self.vector_db.close()
            self.knowledge_graph.close()
            if self.redis_client:
                self.redis_client.close()
            logger.info("Enhanced memory manager connections closed")
        except Exception as e:
            logger.error(f"Error closing enhanced memory manager: {e}") 