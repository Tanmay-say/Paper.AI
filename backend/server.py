from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from typing import List
import json

from config import settings
from models.schemas import (
    PaperSearchRequest, PaperMetadata, PaperDetail,
    ChatQueryRequest, ChatResponse, IngestionRequest, IngestionStatus
)
from agents.discovery_agent import discovery_agent
from agents.query_optimizer import query_optimizer_agent
from agents.hybrid_retriever import hybrid_retriever
from agents.answer_generator import answer_generator
from services.neo4j_service import neo4j_service
from workers.ingestion_tasks import ingest_paper_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("Starting PaperAI application...")
    
    try:
        # Verify Neo4j connectivity
        is_connected = await neo4j_service.verify_connectivity()
        if is_connected:
            logger.info("Neo4j connection successful")
            
            # Setup Neo4j schema
            await neo4j_service.setup_schema()
            await neo4j_service.create_vector_index()
            logger.info("Neo4j schema initialized")
        else:
            logger.error("Failed to connect to Neo4j")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PaperAI application...")
    await neo4j_service.close()


# Create the main app
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Paper Endpoints
@api_router.post("/papers/search", response_model=List[PaperMetadata])
async def search_papers(request: PaperSearchRequest):
    """Search for research papers"""
    try:
        if request.source == "arxiv":
            papers = await discovery_agent.search_arxiv(
                query=request.query,
                max_results=request.max_results
            )
            return papers
        else:
            raise HTTPException(status_code=400, detail="Unsupported source")
    except Exception as e:
        logger.error(f"Error searching papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/papers/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: str):
    """Get detailed information about a specific paper"""
    try:
        paper = await neo4j_service.get_paper(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return PaperDetail(**paper)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving paper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/papers/{paper_id}/pdf")
async def get_paper_pdf(paper_id: str):
    """Stream the PDF file for a paper.

    Behavior:
    - If the paper exists in Neo4j with a valid `pdf_path`, serve it from disk.
    - Otherwise, fetch metadata from arXiv and download the PDF on-the-fly to
      `settings.PDF_STORAGE_PATH`, then serve it. Best-effort trigger of
      background ingestion is attempted when available.
    """
    try:
        # Try Neo4j first (best source of truth if ingested)
        try:
            is_connected = await neo4j_service.verify_connectivity()
        except Exception:
            is_connected = False

        if is_connected:
            paper = await neo4j_service.get_paper(paper_id)
            if paper and paper.get('pdf_path'):
                pdf_path = Path(paper['pdf_path'])
                if pdf_path.exists():
                    logger.info(f"Serving PDF for paper {paper_id} from {pdf_path}")
                    return FileResponse(
                        path=str(pdf_path),
                        media_type='application/pdf',
                        filename=f"{paper_id}.pdf"
                    )

        # Fallback: fetch from arXiv and download immediately
        logger.info(f"Falling back to arXiv download for {paper_id}")
        metadata = await discovery_agent.get_paper_by_id(paper_id)

        from workers.ingestion_tasks import download_paper_pdf  # local import to avoid cycles
        storage_dir = Path(settings.PDF_STORAGE_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)
        pdf_path_str = download_paper_pdf(paper_id, metadata.arxiv_id)
        pdf_path = Path(pdf_path_str)

        # Best-effort: kick off background ingestion so future requests hit DB
        try:
            from workers.ingestion_tasks import ingest_single_paper
            ingest_single_paper.delay(paper_id)
        except Exception as bg_e:
            logger.warning(f"Background ingestion not started (non-fatal): {bg_e}")

        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found after download")

        logger.info(f"Serving freshly downloaded PDF for {paper_id} from {pdf_path}")
        return FileResponse(
            path=str(pdf_path),
            media_type='application/pdf',
            filename=f"{paper_id}.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving PDF for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF: {str(e)}")


# Chat Endpoints
@api_router.post("/chat/query", response_model=ChatResponse)
async def chat_query(request: ChatQueryRequest):
    """Process a chat query (non-streaming, for testing)"""
    try:
        # Step 1: Optimize query
        graph_intent = await query_optimizer_agent.optimize_query(
            query=request.query,
            selected_text=request.selected_text
        )
        
        # Step 2: Retrieve relevant contexts
        contexts = await hybrid_retriever.retrieve(
            graph_intent=graph_intent,
            paper_id=request.paper_id,
            top_k=10
        )
        
        # Step 3: Generate answer
        answer = await answer_generator.generate_answer(
            query=request.query,
            contexts=contexts,
            selected_text=request.selected_text,
            chat_history=request.chat_history
        )
        
        # Step 4: Format response
        sources = [
            {
                'chunk_id': ctx.chunk_id,
                'paper_id': ctx.paper_id,
                'text': ctx.text[:200] + "..." if len(ctx.text) > 200 else ctx.text,
                'score': ctx.score
            }
            for ctx in contexts[:5]
        ]
        
        return ChatResponse(
            response=answer,
            sources=sources,
            paper_id=request.paper_id
        )
    
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time chat with streaming"""
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            paper_id = message_data.get('paper_id')
            query = message_data.get('query')
            selected_text = message_data.get('selected_text')
            chat_history = message_data.get('chat_history', [])
            
            # Step 1: Optimize query
            graph_intent = await query_optimizer_agent.optimize_query(
                query=query,
                selected_text=selected_text
            )
            
            # Step 2: Retrieve contexts
            contexts = await hybrid_retriever.retrieve(
                graph_intent=graph_intent,
                paper_id=paper_id,
                top_k=10
            )
            
            # Send sources first
            sources = [
                {
                    'chunk_id': ctx.chunk_id,
                    'paper_id': ctx.paper_id,
                    'text': ctx.text[:200] + "..." if len(ctx.text) > 200 else ctx.text,
                    'score': ctx.score
                }
                for ctx in contexts[:5]
            ]
            
            await websocket.send_json({
                'type': 'sources',
                'data': sources
            })
            
            # Step 3: Stream answer
            async for chunk in answer_generator.generate_streaming_answer(
                query=query,
                contexts=contexts,
                selected_text=selected_text,
                chat_history=chat_history
            ):
                await websocket.send_json({
                    'type': 'content',
                    'data': chunk
                })
            
            # Send completion signal
            await websocket.send_json({
                'type': 'done',
                'data': None
            })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            'type': 'error',
            'data': str(e)
        })


# Ingestion Endpoints
@api_router.post("/ingest/papers", response_model=IngestionStatus)
async def ingest_papers(request: IngestionRequest):
    """Trigger batch paper ingestion"""
    try:
        result = ingest_paper_batch.delay(
            paper_ids=request.paper_ids,
            source=request.source
        )
        
        return IngestionStatus(
            job_id=result.id,
            status='pending',
            total_papers=len(request.paper_ids),
            processed_papers=0,
            message="Ingestion job started"
        )
    
    except Exception as e:
        logger.error(f"Error starting ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/ingest/status/{job_id}", response_model=IngestionStatus)
async def get_ingestion_status(job_id: str):
    """Check the status of an ingestion job"""
    # This is a simplified version - in production, you'd track this in Redis
    return IngestionStatus(
        job_id=job_id,
        status='processing',
        total_papers=0,
        processed_papers=0,
        message="Status tracking to be implemented with Redis"
    )


@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        neo4j_ok = await neo4j_service.verify_connectivity()
        return {
            "status": "healthy",
            "neo4j": "connected" if neo4j_ok else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
