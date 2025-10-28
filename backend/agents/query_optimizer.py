import google.generativeai as genai
from typing import Dict, Any
import logging
import json
from config import settings
from models.schemas import GraphIntent

logger = logging.getLogger(__name__)


class QueryOptimizerAgent:
    """Agent to convert natural language queries into structured graph intents"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
        logger.info("QueryOptimizerAgent initialized")
    
    async def optimize_query(self, query: str, selected_text: str = None) -> GraphIntent:
        """Convert natural language query into structured graph intent"""
        
        context = f"\nSelected text: {selected_text}" if selected_text else ""
        
        prompt = f"""
You are a query optimization agent for a research paper knowledge graph.

Graph Schema:
- Nodes: Paper, Chunk, Author, Method, Concept
- Relationships: HAS_CHUNK, AUTHORED_BY, CITES, USES, MENTIONS

User Query: {query}{context}

Analyze the query and extract:
1. intent_type: The type of query (definition, comparison, methodology, citation, general)
2. entities: Key entities mentioned (paper titles, authors, methods, concepts)
3. relations: Relevant relationships to explore
4. semantic_query: A refined semantic search query
5. retrieval_params: Parameters for retrieval (e.g., focus_on_citations, expand_depth)

Return your analysis as a JSON object with these fields.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            graph_intent = GraphIntent(
                intent_type=result.get('intent_type', 'general'),
                entities=result.get('entities', []),
                relations=result.get('relations', []),
                semantic_query=result.get('semantic_query', query),
                retrieval_params=result.get('retrieval_params', {})
            )
            
            logger.info(f"Optimized query: {graph_intent.intent_type}")
            return graph_intent
        
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            # Fallback to basic intent
            return GraphIntent(
                intent_type='general',
                entities=[],
                relations=[],
                semantic_query=query,
                retrieval_params={}
            )


query_optimizer_agent = QueryOptimizerAgent()