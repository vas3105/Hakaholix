# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path
from datetime import datetime
import os

from app.config import settings
# LLMHandler may import heavy dependencies (transformers). Import lazily in startup to avoid startup failures
LLMHandler = None
_LLM_IMPORT_ERROR = None
from app.models.rag_pipeline import RAGPipeline
from app.agents.travel_agent import TravelAgent
from app.agents.booking_agent import BookingAgent
from app.agents.price_comparison_agent import PriceComparisonAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.services.voice_service import VoiceService
from app.services.user_profile import UserProfileService
from app.services.knowledge_base import KnowledgeBase
from app.api.routes import router
from app.api.websocket import manager, handle_websocket_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(_name_)

# Initialize FastAPI
app = FastAPI(
    title="Kerala Travel Assistant API",
    description="Conversational AI for intelligent travel planning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances (will be set during startup)
llm_handler = None
rag_pipeline = None
travel_agent = None
booking_agent = None
price_comparison_agent = None
itinerary_agent = None
voice_service = None
user_profile_service = None
knowledge_base = None
preferences_model = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global llm_handler, rag_pipeline, travel_agent, voice_service, user_profile_service
    global booking_agent, price_comparison_agent, itinerary_agent, knowledge_base, preferences_model

    logger.info("Initializing services...")

    try:
        # Initialize LLM
        logger.info("Loading LLM...")
        # Try to import LLMHandler here so missing heavy deps (e.g. transformers) don't crash startup
        try:
            from app.models.llm_handler import LLMHandler as _LLMHandler
            _LLM_IMPORT_ERROR = None
        except Exception as _e:
            _LLMHandler = None
            _LLM_IMPORT_ERROR = _e

        if _LLM_IMPORT_ERROR:
            logger.warning(f"LLMHandler import failed: {_LLM_IMPORT_ERROR}. Continuing without LLM (fallback mode).")
            llm_handler = None
        else:
            # LLMHandler signature: adapt args if your LLMHandler expects different param names
            llm_handler = _LLMHandler(
                model_name=getattr(settings, "LLM_MODEL_NAME", "meta-llama/Llama-3.2-1B"),
                hf_token=getattr(settings, "HF_TOKEN", "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")
            )

        # Initialize RAG pipeline
        logger.info("Loading RAG pipeline...")
        rag_pipeline = RAGPipeline(
            embedding_model=getattr(settings, "EMBEDDING_MODEL", settings.EMBEDDING_MODEL),
            persist_directory=getattr(settings, "CHROMA_PERSIST_DIRECTORY", settings.CHROMA_PERSIST_DIRECTORY)
        )

        # Load data into RAG if persist dir doesn't exist and raw files exist
        persist_dir = Path(getattr(settings, "CHROMA_PERSIST_DIRECTORY", settings.CHROMA_PERSIST_DIRECTORY))
        if not persist_dir.exists():
            logger.info("Vector store not found - attempting to load raw data into vector store...")
            hotels_path = getattr(settings, "HOTELS_JSON", None)
            attractions_path = getattr(settings, "ATTRACTIONS_JSON", None)
            itineraries_path = getattr(settings, "ITINERARIES_JSON", None)

            # Only attempt to load if all raw JSON files exist
            if hotels_path and attractions_path and itineraries_path and \
               Path(hotels_path).exists() and Path(attractions_path).exists() and Path(itineraries_path).exists():
                try:
                    rag_pipeline.load_data(
                        hotels_path=str(hotels_path),
                        attractions_path=str(attractions_path),
                        itineraries_path=str(itineraries_path)
                    )
                    logger.info("Raw data loaded into vector store.")
                except Exception:
                    logger.exception("Failed to load raw data into vector store.")
            else:
                logger.warning("Raw data files not found — vector store will remain empty for now.")
        else:
            logger.info("Vector store found; skipping raw data load.")

        # Initialize services
        logger.info("Initializing user/profile/knowledge services...")
        user_profile_service = UserProfileService()
        knowledge_base = KnowledgeBase()

        # Initialize preferences model (embedding model)
        logger.info("Initializing preferences model...")
        from app.models.user_preferences import UserPreferences
        preferences_model = UserPreferences(embedding_model=getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

        # Initialize agents (pass required dependencies)
        logger.info("Initializing agents...")
        booking_agent = BookingAgent(rag_pipeline, user_profile_service)
        # PriceComparisonAgent expected (rag_pipeline, llm_handler) in your code — pass both
        price_comparison_agent = PriceComparisonAgent(rag_pipeline)
        itinerary_agent = ItineraryAgent(rag_pipeline, llm_handler)

        # Initialize main travel agent and attach sub-agents
        travel_agent = TravelAgent(
            llm_handler=llm_handler,
            rag_pipeline=rag_pipeline,
            user_profile_service=user_profile_service
        )
        travel_agent.booking_agent = BookingAgent(rag_pipeline, user_profile_service)
        travel_agent.price_comparison_agent = PriceComparisonAgent(rag_pipeline)
        travel_agent.itinerary_agent = ItineraryAgent(rag_pipeline, llm_handler)


        # Initialize voice service
        try:
            from app.services.voice_service import VoiceService, StreamingVoiceService
            voice_service = VoiceService(whisper_model="openai/whisper-tiny")
            streaming_voice_service = StreamingVoiceService(voice_service)
            logger.info("Voice service initialized successfully (Whisper + gTTS).")
        except Exception as e:
            voice_service = None
            streaming_voice_service = None
            logger.warning(f"Voice service initialization failed: {e}")


        logger.info("All services initialized successfully!")

    except Exception as e:
        # Log full traceback and re-raise to surface the error to the server logs
        logger.exception(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down services...")

# Include API routes
# Voice routes disabled
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kerala Travel Assistant API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": "/api/chat",
            "hotels": "/api/hotels/search",
            "attractions": "/api/attractions/search",
            "itinerary": "/api/itinerary/generate",
            "booking": "/api/booking/initiate",
            "prices": "/api/prices/compare",
            "websocket": "/ws/chat"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "llm": llm_handler is not None,
            "rag": rag_pipeline is not None,
            "travel_agent": travel_agent is not None,
            "voice": voice_service is not None
        }
    }

@app.websocket("/ws/voice")
async def websocket_voice(websocket: WebSocket):
    """WebSocket endpoint for real-time voice chat"""
    import base64
    import numpy as np
    import io
    import soundfile as sf
    from app.services.voice_service import VoiceService, StreamingVoiceService
    from fastapi import WebSocketDisconnect

    await websocket.accept()

    # Initialize voice service for this session
    voice_service = VoiceService()
    stream_service = StreamingVoiceService(voice_service)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start_recording":
                await stream_service.start_recording()
                await websocket.send_json({"type": "status", "message": "Recording started"})

            elif msg_type == "audio_chunk":
                audio_data = base64.b64decode(data["audio"])
                await stream_service.process_audio_chunk(audio_data)

            elif msg_type == "stop_recording":
                transcription = await stream_service.stop_recording()
                await websocket.send_json({
                    "type": "transcription",
                    "text": transcription
                })

                # Generate simple bot response
                reply = f"You said: {transcription}"
                await websocket.send_json({
                    "type": "response",
                    "data": {"message": reply}
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown type: {msg_type}"
                })

    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected")


if _name_ == "_main_":
    # DEV NOTE: if you get "only one usage of each socket address" (10048),
    # either change the port or kill the existing process holding the port.
    # Windows: netstat -ano | findstr :8001 -> then taskkill /PID <pid> /F
    uvicorn.run(
        "main:app",
        host=getattr(settings, 'API_HOST', '127.0.0.1'),
        port=getattr(settings, 'API_PORT', 8001),
        reload=True,
        log_level="info"
    )
