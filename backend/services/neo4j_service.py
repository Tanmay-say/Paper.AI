from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
import logging
from urllib.parse import urlparse
import socket
from config import settings

logger = logging.getLogger(__name__)


class Neo4jService:
    def __init__(self):
        try:
            self._init_driver(settings.NEO4J_URI)
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise
    
    async def close(self):
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j driver closed")
    
    async def verify_connectivity(self):
        """Verify connection to Neo4j"""
        try:
            # Use driver's built-in connectivity check
            await self.driver.verify_connectivity()
            async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = await session.run("RETURN 1 as num")
                record = await result.single()
                logger.info(f"✅ Neo4j connectivity verified successfully")
                return record["num"] == 1
        except Exception as e:
            logger.error(f"❌ Failed to verify Neo4j connectivity: {e}")
            logger.info("Tip: Ensure Neo4j Aura database is active and credentials are correct")
            return False

    def _init_driver(self, uri: str) -> None:
        parsed = urlparse(uri)

        # For Neo4j Aura (neo4j+s), encryption is already built-in
        # No need to specify encrypted or trust parameters
        self.driver = AsyncGraphDatabase.driver(
            uri,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=3600
        )
        safe_host = f"{parsed.scheme}://{parsed.hostname}" if parsed.hostname else uri
        logger.info(f"Neo4j driver initialized for {safe_host} (db={settings.NEO4J_DATABASE})")
    
    async def setup_schema(self):
        """Create constraints and indexes for the graph schema"""
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            # Create constraints
            constraints = [
                "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE",
                "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
                "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
                "CREATE CONSTRAINT method_id_unique IF NOT EXISTS FOR (m:Method) REQUIRE m.method_id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint might already exist: {e}")
            
            # Create indexes
            indexes = [
                "CREATE INDEX paper_title_index IF NOT EXISTS FOR (p:Paper) ON (p.title)",
                "CREATE INDEX paper_year_index IF NOT EXISTS FOR (p:Paper) ON (p.year)",
                "CREATE INDEX chunk_paper_index IF NOT EXISTS FOR (c:Chunk) ON (c.paper_id)"
            ]
            
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index might already exist: {e}")
    
    async def create_vector_index(self):
        """Create vector index for chunk embeddings"""
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            query = """
            CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
            FOR (c:Chunk)
            ON c.embedding
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: $dimensions,
                    `vector.similarity_function`: 'cosine'
                }
            }
            """
            try:
                await session.run(query, dimensions=settings.EMBEDDING_DIMENSION)
                logger.info("Vector index created successfully")
            except Exception as e:
                logger.warning(f"Vector index might already exist: {e}")
    
    async def store_paper(self, paper_data: Dict[str, Any]) -> bool:
        """Store a paper and its chunks in Neo4j"""
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                # Create paper node
                paper_query = """
                MERGE (p:Paper {paper_id: $paper_id})
                SET p.title = $title,
                    p.abstract = $abstract,
                    p.year = $year,
                    p.source = $source,
                    p.arxiv_id = $arxiv_id,
                    p.pdf_path = $pdf_path,
                    p.published_date = $published_date,
                    p.created_at = datetime()
                RETURN p.paper_id as paper_id
                """
                
                await session.run(paper_query, **paper_data['paper'])
                
                # Create author nodes and relationships
                for author in paper_data.get('authors', []):
                    author_query = """
                    MERGE (a:Author {author_id: $author_id})
                    SET a.name = $name
                    WITH a
                    MATCH (p:Paper {paper_id: $paper_id})
                    MERGE (p)-[:AUTHORED_BY]->(a)
                    """
                    await session.run(author_query, **author, paper_id=paper_data['paper']['paper_id'])
                
                # Create chunk nodes with embeddings
                for chunk in paper_data.get('chunks', []):
                    chunk_query = """
                    CREATE (c:Chunk {chunk_id: $chunk_id})
                    SET c.text = $text,
                        c.paper_id = $paper_id,
                        c.chunk_index = $chunk_index,
                        c.embedding = $embedding
                    WITH c
                    MATCH (p:Paper {paper_id: $paper_id})
                    MERGE (p)-[:HAS_CHUNK]->(c)
                    """
                    await session.run(chunk_query, **chunk)
                
                logger.info(f"Successfully stored paper: {paper_data['paper']['paper_id']}")
                return True
            except Exception as e:
                logger.error(f"Error storing paper {paper_data['paper']['paper_id']}: {e}")
                return False
    
    async def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve paper details from Neo4j"""
        try:
            async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                query = """
                MATCH (p:Paper {paper_id: $paper_id})
                OPTIONAL MATCH (p)-[:AUTHORED_BY]->(a:Author)
                OPTIONAL MATCH (p)-[:CITES]->(cited:Paper)
                RETURN p, collect(DISTINCT a.name) as authors, collect(DISTINCT cited.paper_id) as citations
                """
                result = await session.run(query, paper_id=paper_id)
                record = await result.single()
                
                if record:
                    paper = dict(record['p'])
                    paper['authors'] = record['authors']
                    paper['related_papers'] = record['citations']
                    paper['citation_count'] = len(record['citations'])
                    return paper
                return None
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {e}")
            return None
    
    async def vector_search(self, query_embedding: List[float], limit: int = 10, paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform vector similarity search on chunk embeddings"""
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                if paper_id:
                    query = """
                    CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_embedding)
                    YIELD node, score
                    WHERE node.paper_id = $paper_id
                    RETURN node.chunk_id as chunk_id, 
                           node.text as text, 
                           node.paper_id as paper_id,
                           node.chunk_index as chunk_index,
                           score
                    ORDER BY score DESC
                    """
                    result = await session.run(query, query_embedding=query_embedding, limit=limit, paper_id=paper_id)
                else:
                    query = """
                    CALL db.index.vector.queryNodes('chunk_embeddings', $limit, $query_embedding)
                    YIELD node, score
                    RETURN node.chunk_id as chunk_id, 
                           node.text as text, 
                           node.paper_id as paper_id,
                           node.chunk_index as chunk_index,
                           score
                    ORDER BY score DESC
                    """
                    result = await session.run(query, query_embedding=query_embedding, limit=limit)
                
                records = await result.values()
                return [{
                    'chunk_id': record[0],
                    'text': record[1],
                    'paper_id': record[2],
                    'chunk_index': record[3],
                    'score': record[4]
                } for record in records]
            except Exception as e:
                logger.error(f"Error during vector search: {e}")
                return []
    
    async def graph_expand(self, paper_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Expand graph to find related papers through citations and authors"""
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                query = """
                MATCH (p:Paper {paper_id: $paper_id})
                MATCH path = (p)-[*1..$depth]-(related:Paper)
                WHERE related.paper_id <> $paper_id
                RETURN DISTINCT related.paper_id as paper_id, 
                       related.title as title,
                       length(path) as distance
                ORDER BY distance
                LIMIT 20
                """
                result = await session.run(query, paper_id=paper_id, depth=depth)
                records = await result.values()
                return [{
                    'paper_id': record[0],
                    'title': record[1],
                    'distance': record[2]
                } for record in records]
            except Exception as e:
                logger.error(f"Error during graph expansion for paper {paper_id}: {e}")
                return []

    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Return aggregate metrics for the dashboard.

        Includes:
        - total_papers
        - total_authors
        - total_chunks
        - papers_per_year: [{year, count}]
        - top_authors: [{author, count}]
        """
        async with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                # Run counts in parallel transactions
                total_papers_result = await session.run("MATCH (p:Paper) RETURN count(p) AS total")
                total_authors_result = await session.run("MATCH (a:Author) RETURN count(a) AS total")
                total_chunks_result = await session.run("MATCH (c:Chunk) RETURN count(c) AS total")

                tp_record = await total_papers_result.single()
                ta_record = await total_authors_result.single()
                tc_record = await total_chunks_result.single()

                # Papers per year
                ppy_query = (
                    "MATCH (p:Paper) WHERE exists(p.year) "
                    "RETURN p.year AS year, count(p) AS count ORDER BY year"
                )
                ppy_result = await session.run(ppy_query)
                ppy_records = await ppy_result.values()
                papers_per_year = [
                    { 'year': record[0], 'count': record[1] } for record in ppy_records
                ]

                # Top authors by paper count
                ta_query = (
                    "MATCH (a:Author)<-[:AUTHORED_BY]-(:Paper) "
                    "RETURN a.name AS author, count(*) AS count "
                    "ORDER BY count DESC LIMIT 10"
                )
                ta_result = await session.run(ta_query)
                ta_records = await ta_result.values()
                top_authors = [
                    { 'author': record[0], 'count': record[1] } for record in ta_records
                ]

                return {
                    'total_papers': tp_record[0] if tp_record else 0,
                    'total_authors': ta_record[0] if ta_record else 0,
                    'total_chunks': tc_record[0] if tc_record else 0,
                    'papers_per_year': papers_per_year,
                    'top_authors': top_authors
                }
            except Exception as e:
                logger.error(f"Error building dashboard overview: {e}")
                return {
                    'total_papers': 0,
                    'total_authors': 0,
                    'total_chunks': 0,
                    'papers_per_year': [],
                    'top_authors': []
                }


neo4j_service = Neo4jService()