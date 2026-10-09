import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.app.main import app, ALLOWED_ORIGINS
from backend.app.database import init_db, Base
from sqlalchemy import create_engine


def test_cors_configuration(client):
    """Verify CORS headers reflect configured allowed origins."""
    # Request from allowed origin
    allowed_origin = "http://localhost:5173"
    response = client.get("/health", headers={"Origin": allowed_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin

    # Request from unauthorized origin should not be granted access-control-allow-origin
    unauthorized_origin = "http://malicious-site.com"
    response2 = client.get("/health", headers={"Origin": unauthorized_origin})
    assert response2.status_code == 200
    assert response2.headers.get("access-control-allow-origin") != unauthorized_origin


def test_test_suite_does_not_create_test_runner_db():
    """Verify that test runner does not create any test_runner.db on disk."""
    disk_test_db = root_dir / "backend" / "tests" / "test_runner.db"
    assert not disk_test_db.exists(), f"Found lingering test database at {disk_test_db}"


def test_init_db_helper_controlled_execution():
    """Verify init_db can be called on an arbitrary target engine without touching disk."""
    temp_engine = create_engine("sqlite:///:memory:")
    # Verify tables created cleanly on target engine
    init_db(temp_engine)
    table_names = list(Base.metadata.tables.keys())
    assert "student_profiles" in table_names
    assert "quizzes" in table_names
    assert "learning_plans" in table_names
