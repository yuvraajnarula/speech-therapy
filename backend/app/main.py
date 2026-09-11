import asyncio
import json
import base64
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.app.core.config import settings
from backend.app.core.logging import app_logger, audit_logger
from backend.app.core.security import decode_access_token
from backend.app.db.session import init_db
from backend.app.api.auth import router as auth_router
from backend.app.api.sessions import router as sessions_router
from backend.app.api.exercises import router as exercises_router
from backend.app.services.live_ast_service import live_ast_service
from backend.app.services.phonetics_engine import phonetics_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Initializing database...")
    await init_db()
    app_logger.info("Database initialized.")

    # Warm up STT model to eliminate cold starts
    app_logger.info("Pre-warming speech engine in memory...")
    try:
        live_ast_service.load_model()
    except Exception as e:
        app_logger.warning(f"Could not warm up STT model on startup: {e}")

    yield

    app_logger.info("Shutting down speech therapy service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(sessions_router, prefix=settings.API_V1_STR)
app.include_router(exercises_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


# ==============================================================================
# Live AST & Indian Dialect WebSocket Streaming
# ==============================================================================

@app.websocket("/ws/live-ast")
async def live_ast_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    High-performance real-time WebSocket for Indian dialect speech therapy:
    - Receives 16-bit 16kHz PCM chunks
    - Applies Voice Activity Detection (VAD)
    - Performs live Speech-to-Text & Live Translation (AST)
    - Returns phonetic articulation breakdowns
    """
    await websocket.accept()
    audit_logger.info("Client connected to /ws/live-ast")
    await websocket.send_text("AST Engine Connected")

    # Audio session state
    audio_buffer = bytearray()
    target_text = "namaste"
    source_language = "hi"
    target_language = "en"

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            # Handle Control JSON Messages
            if message.get("text"):
                try:
                    payload = json.loads(message["text"])
                    action = payload.get("action")

                    if action == "configure":
                        target_text = payload.get("target", target_text)
                        source_language = payload.get("source_language", source_language)
                        target_language = payload.get("target_language", target_language)
                        await websocket.send_text(
                            f"Configured: target='{target_text}', src='{source_language}', tgt='{target_language}'"
                        )

                    elif action == "stop":
                        await websocket.send_text("Processing speech utterance...")

                        # Run AST & Diagnostics on buffered audio
                        result = live_ast_service.process_session_audio(
                            pcm_bytes=bytes(audio_buffer),
                            target_text=target_text,
                            source_language=source_language,
                            target_language=target_language
                        )

                        await websocket.send_json(result)
                        audio_buffer.clear()

                    elif action == "reset":
                        audio_buffer.clear()
                        await websocket.send_text("Audio buffer cleared")

                except json.JSONDecodeError:
                    await websocket.send_text("Invalid JSON payload")

            # Handle Streaming Binary PCM Chunks
            elif message.get("bytes"):
                chunk = message["bytes"]
                # Apply VAD check for real-time energy presence
                has_voice = live_ast_service.vad.is_speech(chunk)
                audio_buffer.extend(chunk)

                # Send continuous intermediate feedback if requested
                if len(audio_buffer) % 32000 == 0:  # Every 1 second of audio
                    await websocket.send_text(f"Voice detected: {has_voice}")

    except WebSocketDisconnect:
        app_logger.info("Client disconnected from /ws/live-ast")
    except Exception as e:
        app_logger.error(f"WebSocket Exception: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except Exception:
            pass


# Backward compatibility for existing frontend
@app.websocket("/ws/agent-therapy")
async def legacy_agent_websocket(websocket: WebSocket):
    await live_ast_websocket(websocket=websocket)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
