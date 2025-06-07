from neo4j import GraphDatabase
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
from ..config import settings

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.driver = None
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize Neo4j driver with authentication"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            logger.info("Neo4j driver initialized successfully")
            self._create_constraints()
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise
    
    def _create_constraints(self):
        """Create constraints and indexes for better performance"""
        try:
            with self.driver.session() as session:
                # Create constraints
                constraints = [
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                    "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                    "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        # Constraint might already exist
                        logger.debug(f"Constraint creation note: {e}")
                
                # Create indexes
                indexes = [
                    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
                    "CREATE INDEX memory_timestamp IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)",
                    "CREATE INDEX relationship_strength IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.strength)"
                ]
                
                for index in indexes:
                    try:
                        session.run(index)
                    except Exception as e:
                        logger.debug(f"Index creation note: {e}")
                        
            logger.info("Neo4j constraints and indexes created")
            
        except Exception as e:
            logger.error(f"Failed to create constraints: {e}")
    
    async def create_user_node(self, user_id: str, metadata: Optional[Dict] = None) -> bool:
        """Create or update a user node"""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (u:User {id: $user_id})
                SET u.last_active = datetime(),
                    u.metadata = $metadata
                RETURN u
                """
                
                result = session.run(query, {
                    "user_id": user_id,
                    "metadata": json.dumps(metadata or {})
                })
                
                logger.info(f"Created/updated user node: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create user node: {e}")
            return False
    
    async def create_memory_node(self, 
                                memory_id: str,
                                user_id: str,
                                content: str,
                                content_type: str,
                                entities: List[str],
                                metadata: Optional[Dict] = None) -> bool:
        """Create a memory node and link to user"""
        try:
            with self.driver.session() as session:
                # Create memory node
                query = """
                MERGE (u:User {id: $user_id})
                CREATE (m:Memory {
                    id: $memory_id,
                    content: $content,
                    content_type: $content_type,
                    timestamp: datetime(),
                    metadata: $metadata
                })
                CREATE (u)-[:HAS_MEMORY]->(m)
                RETURN m
                """
                
                session.run(query, {
                    "memory_id": memory_id,
                    "user_id": user_id,
                    "content": content,
                    "content_type": content_type,
                    "metadata": json.dumps(metadata or {})
                })
                
                # Create entity nodes and relationships
                for entity in entities:
                    await self._create_entity_relationship(memory_id, entity)
                
                logger.info(f"Created memory node: {memory_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create memory node: {e}")
            return False
    
    async def _create_entity_relationship(self, memory_id: str, entity: str):
        """Create entity and link to memory"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Memory {id: $memory_id})
                MERGE (e:Entity {name: $entity})
                SET e.last_mentioned = datetime()
                MERGE (m)-[:MENTIONS]->(e)
                """
                
                session.run(query, {
                    "memory_id": memory_id,
                    "entity": entity
                })
                
        except Exception as e:
            logger.error(f"Failed to create entity relationship: {e}")
    
    async def create_concept_relationships(self, 
                                         concepts: List[Tuple[str, str, float]]) -> bool:
        """Create relationships between concepts with strength scores"""
        try:
            with self.driver.session() as session:
                for concept1, concept2, strength in concepts:
                    query = """
                    MERGE (c1:Concept {name: $concept1})
                    MERGE (c2:Concept {name: $concept2})
                    MERGE (c1)-[r:RELATED_TO]-(c2)
                    SET r.strength = CASE 
                        WHEN r.strength IS NULL THEN $strength
                        ELSE (r.strength + $strength) / 2
                    END,
                    r.last_updated = datetime()
                    """
                    
                    session.run(query, {
                        "concept1": concept1,
                        "concept2": concept2,
                        "strength": strength
                    })
                
                logger.info(f"Created {len(concepts)} concept relationships")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create concept relationships: {e}")
            return False
    
    async def find_related_concepts(self, 
                                   concept: str,
                                   depth: int = 2,
                                   min_strength: float = 0.5,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Find concepts related to a given concept using graph traversal"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Concept {name: $concept})
                CALL apoc.path.expandConfig(c, {
                    relationshipFilter: "RELATED_TO",
                    minLevel: 1,
                    maxLevel: $depth,
                    limit: $limit
                }) YIELD path
                UNWIND relationships(path) AS r
                WITH endNode(path) AS related, 
                     avg(r.strength) AS avg_strength,
                     length(path) AS distance
                WHERE avg_strength >= $min_strength
                RETURN related.name AS concept_name,
                       avg_strength AS strength,
                       distance
                ORDER BY avg_strength DESC, distance ASC
                LIMIT $limit
                """
                
                result = session.run(query, {
                    "concept": concept,
                    "depth": depth,
                    "min_strength": min_strength,
                    "limit": limit
                })
                
                related_concepts = []
                for record in result:
                    related_concepts.append({
                        "concept": record["concept_name"],
                        "strength": record["strength"],
                        "distance": record["distance"]
                    })
                
                logger.info(f"Found {len(related_concepts)} related concepts for: {concept}")
                return related_concepts
                
        except Exception as e:
            logger.error(f"Failed to find related concepts: {e}")
            return []
    
    async def get_user_entity_network(self, 
                                     user_id: str,
                                     limit: int = 20) -> List[Dict[str, Any]]:
        """Get the entity network for a specific user"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m:Memory)-[:MENTIONS]->(e:Entity)
                WITH e, count(m) AS mention_count
                ORDER BY mention_count DESC
                LIMIT $limit
                MATCH (e)-[:RELATED_TO]-(related:Entity)
                RETURN e.name AS entity,
                       mention_count,
                       collect(DISTINCT related.name) AS related_entities
                """
                
                result = session.run(query, {
                    "user_id": user_id,
                    "limit": limit
                })
                
                entities = []
                for record in result:
                    entities.append({
                        "entity": record["entity"],
                        "mention_count": record["mention_count"],
                        "related_entities": record["related_entities"]
                    })
                
                return entities
                
        except Exception as e:
            logger.error(f"Failed to get user entity network: {e}")
            return []
    
    async def find_memory_connections(self, 
                                     memory_id: str,
                                     user_id: str,
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """Find memories connected through shared entities"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m1:Memory {id: $memory_id})-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(m2:Memory)
                MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m2)
                WHERE m1 <> m2
                WITH m2, e, count(*) AS shared_entities
                ORDER BY shared_entities DESC
                LIMIT $limit
                RETURN m2.id AS memory_id,
                       m2.content AS content,
                       m2.timestamp AS timestamp,
                       shared_entities,
                       collect(e.name) AS shared_entity_names
                """
                
                result = session.run(query, {
                    "memory_id": memory_id,
                    "user_id": user_id,
                    "limit": limit
                })
                
                connections = []
                for record in result:
                    connections.append({
                        "memory_id": record["memory_id"],
                        "content": record["content"],
                        "timestamp": record["timestamp"],
                        "shared_entities": record["shared_entities"],
                        "shared_entity_names": record["shared_entity_names"]
                    })
                
                return connections
                
        except Exception as e:
            logger.error(f"Failed to find memory connections: {e}")
            return []
    
    async def get_trending_entities(self, 
                                   user_id: Optional[str] = None,
                                   days: int = 7,
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending entities based on recent mentions"""
        try:
            with self.driver.session() as session:
                if user_id:
                    query = """
                    MATCH (u:User {id: $user_id})-[:HAS_MEMORY]->(m:Memory)-[:MENTIONS]->(e:Entity)
                    WHERE m.timestamp >= datetime() - duration({days: $days})
                    WITH e, count(m) AS recent_mentions
                    ORDER BY recent_mentions DESC
                    LIMIT $limit
                    RETURN e.name AS entity,
                           recent_mentions,
                           e.type AS entity_type
                    """
                    params = {"user_id": user_id, "days": days, "limit": limit}
                else:
                    query = """
                    MATCH (m:Memory)-[:MENTIONS]->(e:Entity)
                    WHERE m.timestamp >= datetime() - duration({days: $days})
                    WITH e, count(m) AS recent_mentions
                    ORDER BY recent_mentions DESC
                    LIMIT $limit
                    RETURN e.name AS entity,
                           recent_mentions,
                           e.type AS entity_type
                    """
                    params = {"days": days, "limit": limit}
                
                result = session.run(query, params)
                
                trending = []
                for record in result:
                    trending.append({
                        "entity": record["entity"],
                        "mentions": record["recent_mentions"],
                        "type": record.get("entity_type", "unknown")
                    })
                
                return trending
                
        except Exception as e:
            logger.error(f"Failed to get trending entities: {e}")
            return []
    
    def close(self):
        """Close the Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver connection closed") 