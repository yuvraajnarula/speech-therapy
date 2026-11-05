import json
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.api.auth import router as auth_router
from backend.app.api.exercises import router as exercises_router
from backend.app.api.memory import router as memory_router
from backend.app.api.sessions import router as sessions_router
from backend.app.core.config import settings
from backend.app.core.logging import app_logger, audit_logger
from backend.app.core.security import decode_access_token
from backend.app.db.session import engine, init_db
from backend.app.services.live_ast_service import live_ast_service
from backend.app.services.live_tutor_service import (
    LiveTutorSession,
    get_adaptive_target,
)
from backend.app.services.memory_service import memory_service  # noqa: F401 (memory layer singleton)
from backend.app.services.storage_service import storage_service

# ==============================================================================
# App Lifespan
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Initializing database...")
    await init_db()
    app_logger.info("Database initialized.")

    # Connect memory service (Redis; falls back to in-memory silently)
    await memory_service.connect()

    # Warm up STT model to eliminate cold starts
    app_logger.info("Pre-warming speech engine in memory...")
    try:
        live_ast_service.load_model()
    except Exception as e:
        app_logger.warning(f"Could not warm up STT model on startup: {e}")

    yield

    app_logger.info("Shutting down speech therapy service...")
    await memory_service.disconnect()


# ==============================================================================
# FastAPI Application
# ==============================================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# OpenTelemetry Instrumentation
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    _otel_resource = Resource.create(
        {
            "service.name": settings.PROJECT_NAME,
            "service.version": "2.0.0",
            "deployment.environment": settings.ENVIRONMENT,
        }
    )
    _otel_tracer_provider = TracerProvider(resource=_otel_resource)

    # Export to OTLP endpoint if configured (default: localhost:4318)
    _otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    _otel_exporter = OTLPSpanExporter(endpoint=_otel_endpoint)
    _otel_tracer_provider.add_span_processor(BatchSpanProcessor(_otel_exporter))
    trace.set_tracer_provider(_otel_tracer_provider)

    # Instrument FastAPI routes with OpenTelemetry spans
    FastAPIInstrumentor.instrument_app(app)
    _otel_enabled = True
    app_logger.info(f"OpenTelemetry instrumentation enabled (endpoint={_otel_endpoint})")
except Exception as _otel_err:
    _otel_enabled = False
    app_logger.warning(f"OpenTelemetry not available: {_otel_err}. Install opentelemetry packages.")

# ---------------------------------------------------------------------------
# Prometheus Instrumentation
# ---------------------------------------------------------------------------
try:
    from prometheus_client import Counter, Gauge, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Custom clinical metrics
    WS_ACTIVE_CONNECTIONS = Gauge(
        "indicast_ws_active_connections", "Active WebSocket connections",
        labelnames=["endpoint"]
    )
    AST_INFERENCE_LATENCY = Histogram(
        "indicast_ast_inference_latency_seconds", "AST inference latency",
        labelnames=["dialect"]
    )
    PHONEME_ERROR_TOTAL = Counter(
        "indicast_phoneme_error_total", "Total phoneme errors by type and dialect",
        labelnames=["phoneme", "dialect"]
    )
    TUTOR_SESSION_TOTAL = Counter(
        "indicast_tutor_sessions_total", "Total live tutor sessions started",
        labelnames=["dialect"]
    )
    _prometheus_enabled = True
    app_logger.info("Prometheus instrumentation enabled at /metrics")
except Exception as _prom_err:
    _prometheus_enabled = False
    app_logger.warning(f"Prometheus not available: {_prom_err}. Install prometheus-fastapi-instrumentator.")

    # Stub metrics so the rest of the code doesn't need conditionals
    class _NoopMetric:
        def labels(self, **_): return self
        def inc(self, *a, **k): pass
        def observe(self, *a, **k): pass
        def set(self, *a, **k): pass

    WS_ACTIVE_CONNECTIONS = _NoopMetric()  # type: ignore[assignment]
    AST_INFERENCE_LATENCY = _NoopMetric()  # type: ignore[assignment]
    PHONEME_ERROR_TOTAL = _NoopMetric()  # type: ignore[assignment]
    TUTOR_SESSION_TOTAL = _NoopMetric()  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# CORS — strict origin allow-list (comma-separated CORS_ORIGINS env var).
# Never allow "*" together with credentials: that combination would let any
# website issue authenticated requests against the clinical APIs.
# ---------------------------------------------------------------------------
_cors_origins = [o for o in (s.strip() for s in settings.CORS_ORIGINS.split(",")) if o]
app_logger.info(f"CORS allow-list: {_cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ---------------------------------------------------------------------------
# REST API Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(sessions_router, prefix=settings.API_V1_STR)
app.include_router(exercises_router, prefix=settings.API_V1_STR)
app.include_router(memory_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    deps = {}
    overall = "healthy"

    # Database connectivity
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        deps["database"] = "ok"
    except Exception as e:
        deps["database"] = f"error: {type(e).__name__}"
        overall = "degraded"

    # Redis / memory service
    if memory_service._redis_available:
        deps["redis"] = "ok"
    else:
        deps["redis"] = "unavailable (in-memory fallback)"
        overall = "degraded"

    return {
        "status": overall,
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "dependencies": deps,
    }


# ==============================================================================
# Live AST WebSocket  (/ws/live-ast)
# ==============================================================================

@app.websocket("/ws/live-ast")
async def live_ast_websocket(
    websocket: WebSocket,
    token: str | None = Query(None)
):
    """
    High-performance real-time WebSocket for Indian dialect speech therapy:
    - Receives 16-bit 16kHz PCM chunks
    - Applies Voice Activity Detection (VAD)
    - Performs live Speech-to-Text & Live Translation (AST)
    - Returns phonetic articulation breakdowns
    - Updates clinical memory layer after each utterance
    """
    await websocket.accept()
    authenticated_user = None
    if token:
        try:
            authenticated_user = await decode_access_token(token)
            audit_logger.info(
                f"WebSocket authenticated for user: {authenticated_user.sub} (role: {authenticated_user.role})"
            )
        except Exception as e:
            audit_logger.warning(f"WebSocket token validation failed: {e}")

    WS_ACTIVE_CONNECTIONS.labels(endpoint="live-ast").inc()
    audit_logger.info("Client connected to /ws/live-ast")
    await websocket.send_text("AST Engine Connected")

    # Session state
    audio_buffer = bytearray()
    target_text = "namaste"
    source_language = "hi"
    target_language = "en"

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

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
                        import time
                        t0 = time.perf_counter()

                        await websocket.send_text("Processing speech utterance...")
                        raw_pcm = bytes(audio_buffer)

                        result = live_ast_service.process_session_audio(
                            pcm_bytes=raw_pcm,
                            target_text=target_text,
                            source_language=source_language,
                            target_language=target_language,
                        )

                        latency = time.perf_counter() - t0
                        AST_INFERENCE_LATENCY.labels(dialect=source_language).observe(latency)

                        # Update clinical memory
                        if authenticated_user:
                            try:
                                await memory_service.update_from_diagnostic(
                                    patient_id=authenticated_user.sub,
                                    dialect=source_language,
                                    diagnostic=result,
                                )
                            except Exception as me:
                                app_logger.warning(f"Memory update failed: {me}")

                        # Track phoneme errors
                        for error in result.get("errors", []):
                            ph = error.get("target_slice", "").strip().upper()
                            if ph:
                                PHONEME_ERROR_TOTAL.labels(phoneme=ph, dialect=source_language).inc()

                        # Persist audio
                        if len(raw_pcm) > 0:
                            try:
                                wav_io = live_ast_service.pcm_to_wav(raw_pcm)
                                storage_key = storage_service.upload_audio_bytes(
                                    wav_io.getvalue(),
                                    filename_prefix=f"{source_language}_{target_text}",
                                )
                                result["audio_storage_key"] = storage_key
                            except Exception as e:
                                app_logger.warning(f"Could not persist audio take: {e}")

                        await websocket.send_json(result)
                        audio_buffer.clear()

                    elif action == "reset":
                        audio_buffer.clear()
                        await websocket.send_text("Audio buffer cleared")

                except json.JSONDecodeError:
                    await websocket.send_text("Invalid JSON payload")

            elif message.get("bytes"):
                chunk = message["bytes"]
                has_voice = live_ast_service.vad.is_speech(chunk)
                audio_buffer.extend(chunk)
                if len(audio_buffer) % 32000 == 0:
                    await websocket.send_text(f"Voice detected: {has_voice}")

    except WebSocketDisconnect:
        app_logger.info("Client disconnected from /ws/live-ast")
    except Exception as e:
        app_logger.error(f"WebSocket Exception: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except Exception:
            pass
    finally:
        WS_ACTIVE_CONNECTIONS.labels(endpoint="live-ast").inc(-1)


# ==============================================================================
# Live Tutor WebSocket  (/ws/live-tutor)
# ==============================================================================

@app.websocket("/ws/live-tutor")
async def live_tutor_websocket(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    """
    Adaptive real-time tutoring WebSocket.

    Protocol (client → server):
      {action: "start",   patient_id, dialect}      — start a tutor session
      {action: "attempt", audio_base64}              — submit spoken audio (optional)
      {action: "stop"}                               — terminate session

    Protocol (server → client):
      {type: "tutor_cue",  target_word, phoneme_target, cue_text, native_script, ipa}
      {type: "feedback",   diagnostic, encouragement, next_cue, memory_snapshot}
      {type: "error",      message}
      {type: "connected",  message}

    Adaptive rules:
      - 2 consecutive correct  → escalate to harder phoneme (less common target)
      - 3 consecutive incorrect → de-escalate to easier target
      - Memory layer updated after every attempt
    """
    await websocket.accept()

    # Authenticate
    authenticated_user = None
    if token:
        try:
            authenticated_user = await decode_access_token(token)
        except Exception:
            await websocket.send_json({"type": "error", "message": "Invalid authentication token"})
            await websocket.close()
            return

    WS_ACTIVE_CONNECTIONS.labels(endpoint="live-tutor").inc()
    await websocket.send_json({"type": "connected", "message": "Live Tutor Engine Connected"})

    tutor_session = LiveTutorSession()

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("text"):
                try:
                    payload = json.loads(message["text"])
                    action = payload.get("action")

                    # --------------------------------------------------------
                    # START: initialise tutor session
                    # --------------------------------------------------------
                    if action == "start":
                        patient_id = payload.get("patient_id") or (
                            authenticated_user.sub if authenticated_user else "anonymous"
                        )
                        dialect = payload.get("dialect", "hi")

                        tutor_session.start(patient_id, dialect)
                        TUTOR_SESSION_TOTAL.labels(dialect=dialect).inc()

                        # Pull memory context + select adaptive target
                        current_target, ctx = await get_adaptive_target(patient_id, dialect)
                        tutor_session.current_target = current_target

                        await websocket.send_json(
                            tutor_session.first_cue_payload(current_target, ctx.weak_phonemes)
                        )

                    # --------------------------------------------------------
                    # SUBMIT: process spoken audio
                    # --------------------------------------------------------
                    elif action == "submit" and tutor_session.started:
                        raw_pcm = tutor_session.drain_audio()
                        current_target = tutor_session.current_target
                        dialect = tutor_session.dialect
                        patient_id = tutor_session.patient_id

                        # Run AST diagnostic
                        diagnostic = live_ast_service.process_session_audio(
                            pcm_bytes=raw_pcm,
                            target_text=current_target["word"],
                            source_language=dialect,
                            target_language="en",
                        )

                        # Update memory
                        mem = await memory_service.update_from_diagnostic(
                            patient_id=patient_id,
                            dialect=dialect,
                            diagnostic=diagnostic,
                        )

                        is_correct = diagnostic.get("is_correct", False)
                        tutor_session.track_result(is_correct)

                        # Track phoneme errors in Prometheus
                        for error in diagnostic.get("errors", []):
                            ph = error.get("target_slice", "").strip().upper()
                            if ph:
                                PHONEME_ERROR_TOTAL.labels(phoneme=ph, dialect=dialect).inc()

                        # Select next adaptive target from refreshed memory
                        next_target, ctx_new = await get_adaptive_target(patient_id, dialect)
                        tutor_session.current_target = next_target

                        await websocket.send_json(
                            tutor_session.feedback_payload(
                                diagnostic=diagnostic,
                                memory_snapshot={
                                    "weak_phonemes": mem.weak_phonemes_ranked[:5],
                                    "consecutive_correct": mem.consecutive_correct,
                                    "consecutive_incorrect": mem.consecutive_incorrect,
                                    "total_attempts": mem.total_attempts,
                                },
                                next_target=next_target,
                                weak_phonemes=ctx_new.weak_phonemes,
                            )
                        )

                    # --------------------------------------------------------
                    # STOP: end session gracefully
                    # --------------------------------------------------------
                    elif action == "stop":
                        await websocket.send_json(tutor_session.completion_payload())
                        break

                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})

            elif message.get("bytes"):
                # Accumulate PCM audio for the current attempt
                tutor_session.append_audio(message["bytes"])

    except WebSocketDisconnect:
        app_logger.info(f"Live Tutor client disconnected (patient={str(patient_id)[:8]}...)")
    except Exception as e:
        app_logger.error(f"Live Tutor WebSocket Exception: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        WS_ACTIVE_CONNECTIONS.labels(endpoint="live-tutor").inc(-1)


# Backward compatibility
@app.websocket("/ws/agent-therapy")
async def legacy_agent_websocket(websocket: WebSocket):
    await live_ast_websocket(websocket=websocket)


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
