from typing import List, Dict, Any, Optional
import logging
from services.neo4j_service import neo4j_service
from services.embedding_service import embedding_service
from models.schemas import GraphIntent, RetrievedContext

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Agent for hybrid retrieval combining vector search and graph traversal"""
    
    def __init__(self):
        logger.info("HybridRetriever initialized")
    
    async def retrieve(
        self, 
        graph_intent: GraphIntent, 
        paper_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[RetrievedContext]:
        """Perform hybrid retrieval using vector search and graph expansion"""
        
        try:
            # Step 1: Generate query embedding
            query_embedding = await embedding_service.generate_query_embedding(
                graph_intent.semantic_query
            )
            
            # Step 2: Vector search for relevant chunks
            vector_results = await neo4j_service.vector_search(
                query_embedding=query_embedding,
                limit=top_k,
                paper_id=paper_id
            )
            
            contexts = []
            
            # Step 3: Process vector search results
            for result in vector_results:
                context = RetrievedContext(
                    text=result['text'],
                    paper_id=result['paper_id'],
                    chunk_id=result['chunk_id'],
                    score=result['score'],
                    metadata={
                        'chunk_index': result['chunk_index'],
                        'retrieval_type': 'vector_search'
                    }
                )
                contexts.append(context)
            
            # Step 4: Graph expansion if citations or related papers are relevant
            if paper_id and ('citation' in graph_intent.intent_type.lower() or 
                           'related' in graph_intent.semantic_query.lower()):
                related_papers = await neo4j_service.graph_expand(paper_id, depth=1)
                
                # Add related paper information to context
                for related in related_papers[:5]:
                    context = RetrievedContext(
                        text=f"Related paper: {related['title']}",
                        paper_id=related['paper_id'],
                        chunk_id=f"related_{related['paper_id']}",
                        score=0.8 - (related['distance'] * 0.1),
                        metadata={
                            'retrieval_type': 'graph_expansion',
                            'distance': related['distance']
                        }
                    )
                    contexts.append(context)
            
            # Step 5: Re-rank and limit results
            contexts.sort(key=lambda x: x.score, reverse=True)
            contexts = contexts[:top_k]
            
            logger.info(f"Retrieved {len(contexts)} contexts")
            return contexts
        
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []


hybrid_retriever = HybridRetriever()