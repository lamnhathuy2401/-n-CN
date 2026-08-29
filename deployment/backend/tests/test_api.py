"""API integration tests for auth, permissions and submission lifecycle."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Use isolated temp DB/storage before importing app modules that create engine.
@pytest.fixture(scope="session")
def client(tmp_path_factory):
    root = tmp_path_factory.mktemp("eduverify")
    data_dir = root / "data"
    storage = root / "uploads"
    data_dir.mkdir()
    storage.mkdir()

    import os

    os.environ["EDUVERIFY_DATA_DIR"] = str(data_dir)
    os.environ["STORAGE_DIR"] = str(storage)
    os.environ["DATABASE_URL"] = f"sqlite:///{(data_dir / 'test.db').as_posix()}"
    os.environ["MODEL_PATH"] = str(root / "missing_model.pth")
    os.environ["SECRET_KEY"] = "test-secret"

    # Ensure fresh import of app with test env.
    import importlib
    import sys

    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    for mod in list(sys.modules):
        if mod == "app" or mod.startswith("app.") or mod in {"main", "model_service"}:
            del sys.modules[mod]

    import main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as c:
        yield c


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color=(120, 40, 200)).save(buf, format="PNG")
    return buf.getvalue()


def test_login_and_me(client: TestClient):
    token = _login(client, "lecturer@eduverify.example", "lecturer123")
    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "lecturer"
    assert body["email"] == "lecturer@eduverify.example"


def test_student_cannot_access_review_queue(client: TestClient):
    token = _login(client, "student@eduverify.example", "student123")
    res = client.get("/api/reviews/queue", headers=_auth(token))
    assert res.status_code == 403


def test_submission_lifecycle_and_review(client: TestClient):
    student_token = _login(client, "student@eduverify.example", "student123")
    courses = client.get("/api/courses", headers=_auth(student_token))
    assert courses.status_code == 200
    course_id = courses.json()[0]["id"]

    files = {"files": ("demo.png", _png_bytes(), "image/png")}
    data = {
        "course_id": str(course_id),
        "title": "Bai tap demo",
        "description": "Nop anh minh hoa",
    }
    created = client.post(
        "/api/submissions",
        headers=_auth(student_token),
        data=data,
        files=files,
    )
    assert created.status_code == 200, created.text
    submission = created.json()
    assert submission["title"] == "Bai tap demo"
    assert len(submission["images"]) == 1
    assert submission["status"] in {"approved", "pending_review"}
    assert "disclaimer" in submission

    lecturer_token = _login(client, "lecturer@eduverify.example", "lecturer123")
    if submission["status"] == "pending_review":
        queue = client.get("/api/reviews/queue", headers=_auth(lecturer_token))
        assert queue.status_code == 200
        assert any(item["id"] == submission["id"] for item in queue.json())

    decision = client.post(
        f"/api/reviews/{submission['id']}",
        headers=_auth(lecturer_token),
        json={"decision": "flagged", "note": "Can lam ro nguon anh"},
    )
    assert decision.status_code == 200, decision.text
    body = decision.json()
    assert body["status"] == "flagged"
    assert body["review"]["decision"] == "flagged"

    stats = client.get("/api/dashboard/stats", headers=_auth(lecturer_token))
    assert stats.status_code == 200
    assert stats.json()["total_submissions"] >= 1


def test_health_endpoint(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in {"ok", "degraded"}
    assert "model_loaded" in body
