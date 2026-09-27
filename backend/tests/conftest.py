import os
import sys
import tempfile
import pathlib

import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Isolate side effects (csa.db, uploads/) away from the repository.
TEST_TMP = tempfile.mkdtemp(prefix="csa-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(TEST_TMP, "test.db").replace("\\", "/")
for _key in ("OPENAI_API_KEY", "PYANNOTE_AUTH_TOKEN", "SMTP_HOST", "SMTP_PORT",
             "SMTP_USER", "SMTP_PASSWORD"):
    os.environ.pop(_key, None)
os.chdir(TEST_TMP)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
import app.models  # noqa: F401  (register ORM tables on Base.metadata)
from main import app


_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=_engine)
    session = _TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_member(client, name="张农人", email=None, role="farmer", **extra):
    payload = {"name": name, "role": role}
    if email is not None:
        payload["email"] = email
    payload.update(extra)
    resp = client.post("/api/members/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def make_vegetable(client, name="番茄", season="summer", **extra):
    payload = {"name": name, "season": season}
    payload.update(extra)
    resp = client.post("/api/vegetables/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def make_conversation(client, member_id, title="测试对话"):
    resp = client.post("/api/conversations/", json={"member_id": member_id, "title": title})
    assert resp.status_code == 200, resp.text
    return resp.json()
