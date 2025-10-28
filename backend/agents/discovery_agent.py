import arxiv
from typing import List, Dict, Any
import logging
from models.schemas import PaperMetadata, PaperSource

logger = logging.getLogger(__name__)


class DiscoveryAgent:
    """Agent responsible for discovering and searching research papers"""
    
    def __init__(self):
        self.client = arxiv.Client()
        logger.info("DiscoveryAgent initialized")
    
    async def search_arxiv(self, query: str, max_results: int = 10) -> List[PaperMetadata]:
        """Search arXiv for papers matching the query"""
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            papers = []
            for result in self.client.results(search):
                paper = PaperMetadata(
                    paper_id=result.entry_id.split('/')[-1],
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    year=result.published.year,
                    source=PaperSource.ARXIV,
                    pdf_url=result.pdf_url,
                    arxiv_id=result.entry_id.split('/')[-1],
                    published_date=result.published.isoformat()
                )
                papers.append(paper)
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            return papers
        
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    async def get_paper_by_id(self, arxiv_id: str) -> PaperMetadata:
        """Get a specific paper by its arXiv ID"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            
            paper = PaperMetadata(
                paper_id=result.entry_id.split('/')[-1],
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                year=result.published.year,
                source=PaperSource.ARXIV,
                pdf_url=result.pdf_url,
                arxiv_id=result.entry_id.split('/')[-1],
                published_date=result.published.isoformat()
            )
            
            return paper
        
        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            raise


discovery_agent = DiscoveryAgent()