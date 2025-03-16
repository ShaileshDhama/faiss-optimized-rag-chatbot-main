from fastapi import FastAPI, WebSocket, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
import asyncio
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.models.chat import ChatMessage, ChatResponse, StreamResponse
from app.services.faiss_service import FAISSService
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.market_analysis import MarketAnalysisService
from app.services.task_manager import celery_app, batch_market_analysis, update_knowledge_base, TaskManager
from app.services.telemetry import TelemetryService
from app.services.quality_monitor import QualityMonitorService

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
faiss_service = FAISSService()
llm_service = LLMService()
cache_service = CacheService()
market_service = MarketAnalysisService()
telemetry_service = TelemetryService()
quality_monitor = QualityMonitorService()
task_manager = TaskManager()

# Setup telemetry
telemetry_service.instrument_fastapi(app)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
async def startup_event():
    # Start Prometheus metrics server
    telemetry_service.start_prometheus_server(settings.PROMETHEUS_PORT)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Serve the chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/chat", response_model=ChatResponse)
@telemetry_service.track_performance("chat_request")
async def chat(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme)
):
    """
    Process a chat message and return a response
    """
    try:
        start_time = datetime.utcnow()
        
        # Check cache first
        cache_key = cache_service.generate_key("chat", message.content)
        cached_response = await cache_service.get(cache_key)
        if cached_response:
            telemetry_service.record_cache_hit()
            return ChatResponse(**cached_response)

        # Get relevant context from FAISS
        context_results = faiss_service.hybrid_search(message.content, k=3)
        context_docs = [doc for doc, _ in context_results]
        confidence_score = context_results[0][1] if context_results else 0.0

        # Generate response using LLM
        async for response in llm_service.generate_response(
            message.content,
            context_docs,
            stream=False
        ):
            if response.done:
                # Analyze sentiment
                sentiment = await llm_service.analyze_sentiment(response.content)
                
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Analyze response quality in background
                background_tasks.add_task(
                    quality_monitor.analyze_response_quality,
                    message.content,
                    response.content,
                    context_docs,
                    response_time
                )
                
                chat_response = ChatResponse(
                    message=response.content,
                    sources=context_docs,
                    confidence_score=confidence_score,
                    sentiment=sentiment
                )
                
                # Cache the response
                await cache_service.set(cache_key, chat_response.dict())
                
                return chat_response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.websocket("/api/v1/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses
    """
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            
            # Get relevant context from FAISS
            context_results = faiss_service.hybrid_search(message, k=3)
            context_docs = [doc for doc, _ in context_results]
            
            # Stream response using LLM
            async for response in llm_service.generate_response(
                message,
                context_docs,
                stream=True
            ):
                await websocket.send_text(response.content)
                if response.done:
                    break
                
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

@app.post("/api/v1/market/analysis/{symbol}")
@telemetry_service.track_performance("market_analysis")
async def get_market_analysis(
    symbol: str,
    token: str = Depends(oauth2_scheme)
):
    """
    Get technical analysis for a specific symbol
    """
    try:
        return await market_service.get_market_report(symbol)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/v1/market/batch-analysis")
async def analyze_multiple_symbols(
    symbols: List[str],
    token: str = Depends(oauth2_scheme)
):
    """
    Analyze multiple symbols in parallel using Celery
    """
    try:
        task = batch_market_analysis.delay(symbols)
        return {"task_id": task.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/monitoring/quality-report")
async def get_quality_report(
    token: str = Depends(oauth2_scheme)
):
    """
    Get the latest quality monitoring report
    """
    try:
        return await quality_monitor.generate_quality_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/api/v1/monitoring/performance")
async def get_performance_metrics(
    token: str = Depends(oauth2_scheme)
):
    """
    Get current performance metrics
    """
    try:
        return await telemetry_service.generate_performance_report()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# API endpoints for market analysis
@app.get("/api/v1/market/analysis/{symbol}")
@telemetry_service.track_performance("market_analysis")
async def get_market_analysis(symbol: str):
    """Get market analysis for a specific symbol"""
    return await market_service.get_market_signals(symbol)

# Monitoring endpoints
@app.get("/api/v1/monitoring/performance")
async def get_performance_metrics():
    """Get system performance metrics"""
    return await telemetry_service.get_metrics()

@app.get("/api/v1/monitoring/quality-report")
async def get_quality_report():
    """Get response quality report"""
    return await quality_monitor.get_quality_report()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.VERSION}
