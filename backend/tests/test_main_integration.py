"""
Integration tests for the IndicAST FastAPI app (backend/app/main.py).

Covers: health check, auth register/login, memory API endpoints, and WebSocket
endpoints (/ws/live-ast, /ws/live-tutor). Uses FastAPI TestClient with dependency
overrides so no real database or Redis is required.
"""
import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.db.session import get_db


# ---------------------------------------------------------------------------
# Mock DB session (plain class, not AsyncSession subclass)
# ---------------------------------------------------------------------------

class MockResult:
    def __init__(self, scalar=None, scalars_list=None):
        self._scalar = scalar
        self._scalars_list = scalars_list or []

    def scalars(self):
        return self

    def first(self):
        return self._scalar

    def all(self):
        return self._scalars_list


class MockAsyncSession:
    """In-memory mock of AsyncSession sufficient for auth/sessions/exercises endpoints."""

    # Shared state across instances (each HTTP request gets a fresh session)
    _users = {}
    _sessions = {}
    _attempts = {}
    _consents = {}
    _id_counter = 0

    def __init__(self):
        self.users = self._users
        self.sessions = self._sessions
        self.attempts = self._attempts
        self.consents = self._consents
        self.committed = False
        self.sync_session = SimpleNamespace()

    async def execute(self, stmt):
        import re
        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        if "INSERT INTO users" in sql:
            m = re.search(r"'([^']+@[^']+)'", sql)
            email = m.group(1) if m else "unknown"
            uid = f"uid-{len(self.users)}"
            self.users[email] = SimpleNamespace(
                id=uid, email=email, hashed_password="hashed",
                full_name="Test User", role="patient", preferred_locale="en-IN",
                is_active=True, created_at="2026-01-01T00:00:00+00:00",
            )
            return MockResult(scalar=self.users[email])
        if "SELECT" in sql and "users" in sql and "WHERE" in sql:
            m = re.search(r"'([^']+@[^']+)'", sql)
            if m:
                return MockResult(scalar=self.users.get(m.group(1)))
            m = re.search(r"users\.id = '([^']+)'", sql)
            if m:
                uid = m.group(1)
                user = next((u for u in self.users.values() if u.id == uid), None)
                return MockResult(scalar=user)
            return MockResult()
        if "SELECT" in sql and "therapy_sessions" in sql:
            return MockResult(scalars_list=list(self.sessions.values()))
        if "SELECT" in sql and "exercise_attempts" in sql:
            return MockResult(scalars_list=list(self.attempts.values()))
        if "SELECT" in sql and "consent_records" in sql:
            m = re.search(r"'([^']+)'", sql)
            uid = m.group(1) if m else ""
            consent = self.consents.get(uid)
            return MockResult(scalar=consent)
        return MockResult()

    def add(self, obj):
        if hasattr(obj, "email"):
            self.users[obj.email] = obj
        if not hasattr(obj, "id") or obj.id is None:
            MockAsyncSession._id_counter += 1
            obj.id = f"obj-{MockAsyncSession._id_counter}"

    async def flush(self):
        pass

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def close(self):
        pass


@pytest.fixture
def client():
    """TestClient with DB and memory service mocked out."""
    async def mock_get_db():
        session = MockAsyncSession()
        yield session

    app.dependency_overrides[get_db] = mock_get_db

    # Bypass the lifespan (which calls init_db + memory_service.connect + model warmup)
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Enterprise Speech Therapy MBP"


# ---------------------------------------------------------------------------
# Auth: register + login
# ---------------------------------------------------------------------------

def test_auth_register_and_login(client):
    # Register a new patient user
    resp = client.post("/api/v1/auth/register", json={
        "email": "alice@clinic.org",
        "password": "SecurePass123!",
        "full_name": "Alice Therapist",
        "role": "therapist",
        "preferred_locale": "en-IN",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["role"] == "therapist"
    assert data["user_id"] is not None
    assert "access_token" in data

    token = data["access_token"]

    # Login with same credentials
    resp = client.post("/api/v1/auth/login", json={
        "email": "alice@clinic.org",
        "password": "SecurePass123!",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["role"] == "therapist"
    assert data["access_token"] == token  # same deterministic token

    # Wrong password should fail
    resp = client.post("/api/v1/auth/login", json={
        "email": "alice@clinic.org",
        "password": "WrongPass123!",
    })
    assert resp.status_code == 401

    # Register duplicate email should fail
    resp = client.post("/api/v1/auth/register", json={
        "email": "alice@clinic.org",
        "password": "SecurePass123!",
        "full_name": "Alice",
        "role": "patient",
    })
    assert resp.status_code == 400


def test_auth_get_me(client):
    # Register + login to get a token
    client.post("/api/v1/auth/register", json={
        "email": "bob@clinic.org", "password": "SecurePass123!",
        "full_name": "Bob Patient", "role": "patient",
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "bob@clinic.org", "password": "SecurePass123!",
    })
    token = login.json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == "bob@clinic.org"
    assert data["role"] == "patient"

    # No token should fail
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Memory API (RBAC-protected)
# ---------------------------------------------------------------------------

def test_memory_api_patient_only_own(client):
    # Register two patients
    client.post("/api/v1/auth/register", json={
        "email": "p1@clinic.org", "password": "Pass123!", "full_name": "P1", "role": "patient",
    })
    t1 = client.post("/api/v1/auth/login", json={
        "email": "p1@clinic.org", "password": "Pass123!",
    }).json()["access_token"]

    client.post("/api/v1/auth/register", json={
        "email": "p2@clinic.org", "password": "Pass123!", "full_name": "P2", "role": "patient",
    })

    # p1 tries to read p2's memory -> 403
    resp = client.get("/api/v1/memory/00000000-0000-0000-0000-000000000002",
                      headers={"Authorization": f"Bearer {t1}"})
    assert resp.status_code == 403


def test_memory_api_therapist_can_read_any(client):
    # Register therapist + patient
    client.post("/api/v1/auth/register", json={
        "email": "therapist@clinic.org", "password": "Pass123!",
        "full_name": "Dr. Therapy", "role": "therapist",
    })
    ttok = client.post("/api/v1/auth/login", json={
        "email": "therapist@clinic.org", "password": "Pass123!",
    }).json()["access_token"]

    client.post("/api/v1/auth/register", json={
        "email": "patient@clinic.org", "password": "Pass123!",
        "full_name": "Pat", "role": "patient",
    })

    # Therapist reads any patient memory
    resp = client.get("/api/v1/memory/00000000-0000-0000-0000-000000000001",
                      headers={"Authorization": f"Bearer {ttok}"})
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# WebSocket /ws/live-ast
# ---------------------------------------------------------------------------

def test_ws_live_ast_connect_and_stop(client):
    with client.websocket_connect("/ws/live-ast") as ws:
        data = ws.receive_text()
        assert data == "AST Engine Connected"

        # Send stop with empty buffer -> should process and return diagnostic
        ws.send_text(json.dumps({"action": "stop"}))
        ws.receive_text()  # consume "Processing speech utterance..." text
        raw = ws.receive_text()
        result = json.loads(raw)
        assert result["type"] == "diagnostic"
        assert result["target"] == "namaste"


def test_ws_live_ast_configure_and_stop(client):
    with client.websocket_connect("/ws/live-ast") as ws:
        ws.receive_text()  # consume welcome

        ws.send_text(json.dumps({
            "action": "configure",
            "target": "khana",
            "source_language": "hi",
            "target_language": "en",
        }))
        resp = ws.receive_text()
        assert "Configured" in resp

        ws.send_text(json.dumps({"action": "stop"}))
        ws.receive_text()  # consume "Processing speech utterance..." text
        raw = ws.receive_text()
        result = json.loads(raw)
        assert result["target"] == "khana"


# ---------------------------------------------------------------------------
# WebSocket /ws/live-tutor
# ---------------------------------------------------------------------------

def test_ws_live_tutor_connect_and_start(client):
    with client.websocket_connect("/ws/live-tutor") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"

        ws.send_text(json.dumps({
            "action": "start",
            "patient_id": "test-patient",
            "dialect": "hi",
        }))
        result = ws.receive_json()
        assert result["type"] == "tutor_cue"
        assert "target_word" in result


def test_ws_live_tutor_stop(client):
    with client.websocket_connect("/ws/live-tutor") as ws:
        ws.receive_json()  # connected
        ws.send_text(json.dumps({"action": "start", "patient_id": "p1", "dialect": "hi"}))
        ws.receive_json()  # tutor_cue

        ws.send_text(json.dumps({"action": "stop"}))
        result = ws.receive_json()
        assert result["type"] == "session_complete"


# ---------------------------------------------------------------------------
# Token creation helper
# ---------------------------------------------------------------------------

def test_create_access_token_deterministic():
    t1 = create_access_token(subject="u1", role="patient")
    t2 = create_access_token(subject="u1", role="patient")
    assert t1 == t2  # same subject/role/expiry window => same token
