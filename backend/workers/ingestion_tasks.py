import asyncio
import arxiv
import fitz  # PyMuPDF
import uuid
import os
from pathlib import Path
from typing import List, Dict, Any
import logging
from workers.celery_app import celery_app
from config import settings
from services.neo4j_service import neo4j_service
from services.embedding_service import embedding_service
from agents.discovery_agent import discovery_agent

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < text_length:
            last_period = chunk.rfind('.')
            if last_period > chunk_size * 0.7:  # If period is in the last 30%
                end = start + last_period + 1
                chunk = text[start:end]
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""


def download_paper_pdf(paper_id: str, arxiv_id: str) -> str:
    """Download PDF from arXiv"""
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(client.results(search))
        
        # Create directory if it doesn't exist
        storage_path = Path(settings.PDF_STORAGE_PATH)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Download PDF
        pdf_path = storage_path / f"{paper_id}.pdf"
        paper.download_pdf(filename=str(pdf_path))
        
        logger.info(f"Downloaded PDF for paper {paper_id}")
        return str(pdf_path)
    
    except Exception as e:
        logger.error(f"Error downloading PDF for {arxiv_id}: {e}")
        raise


@celery_app.task(name='ingest_paper_batch')
def ingest_paper_batch(paper_ids: List[str], source: str = 'arxiv'):
    """Trigger ingestion for multiple papers"""
    job_id = str(uuid.uuid4())
    logger.info(f"Starting batch ingestion {job_id} for {len(paper_ids)} papers")
    
    for paper_id in paper_ids:
        ingest_single_paper.delay(paper_id, source, job_id)
    
    return {
        'job_id': job_id,
        'total_papers': len(paper_ids),
        'status': 'processing'
    }


@celery_app.task(name='ingest_single_paper')
def ingest_single_paper(paper_id: str, source: str = 'arxiv', job_id: str = None):
    """Ingest a single paper into the system"""
    try:
        logger.info(f"Ingesting paper: {paper_id}")
        
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Step 1: Get paper metadata
            paper_metadata = loop.run_until_complete(
                discovery_agent.get_paper_by_id(paper_id)
            )
            
            # Step 2: Download PDF
            pdf_path = download_paper_pdf(paper_id, paper_metadata.arxiv_id)
            
            # Step 3: Extract text
            text = extract_text_from_pdf(pdf_path)
            if not text:
                raise Exception("Failed to extract text from PDF")
            
            # Step 4: Chunk text
            chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            logger.info(f"Created {len(chunks)} chunks for paper {paper_id}")
            
            # Step 5: Generate embeddings
            embeddings = loop.run_until_complete(
                embedding_service.generate_embeddings_batch(chunks)
            )
            
            # Step 6: Prepare data for Neo4j
            paper_data = {
                'paper': {
                    'paper_id': paper_metadata.paper_id,
                    'title': paper_metadata.title,
                    'abstract': paper_metadata.abstract,
                    'year': paper_metadata.year,
                    'source': paper_metadata.source,
                    'arxiv_id': paper_metadata.arxiv_id,
                    'pdf_path': pdf_path,
                    'published_date': paper_metadata.published_date
                },
                'authors': [
                    {'author_id': f"author_{i}", 'name': name}
                    for i, name in enumerate(paper_metadata.authors)
                ],
                'chunks': [
                    {
                        'chunk_id': f"{paper_id}_chunk_{i}",
                        'text': chunk,
                        'paper_id': paper_id,
                        'chunk_index': i,
                        'embedding': embedding
                    }
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
            }
            
            # Step 7: Store in Neo4j with a new service instance
            # Create a fresh Neo4j service for this task to avoid event loop conflicts
            from services.neo4j_service import Neo4jService
            neo4j_task_service = Neo4jService()
            
            success = loop.run_until_complete(
                neo4j_task_service.store_paper(paper_data)
            )
            
            # Close the task-specific Neo4j service
            loop.run_until_complete(neo4j_task_service.close())
            
            if success:
                logger.info(f"Successfully ingested paper: {paper_id}")
                return {'status': 'success', 'paper_id': paper_id, 'job_id': job_id}
            else:
                raise Exception("Failed to store paper in Neo4j")
        
        finally:
            # Clean up the event loop
            loop.close()
    
    except Exception as e:
        logger.error(f"Error ingesting paper {paper_id}: {e}")
        return {'status': 'failed', 'paper_id': paper_id, 'error': str(e), 'job_id': job_id}