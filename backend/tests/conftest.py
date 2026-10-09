import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Enforce isolated in-memory database in environment BEFORE importing app or database modules (SB-009)
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Create isolated in-memory SQLite engine with StaticPool so concurrent/threaded requests share state
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Redirect database engine and session factory
import backend.app.database as db_module
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

from backend.app.models import (
    StudentProfile,
    AssessedSkill,
    LearningPlan,
    LearningPlanTask,
    TeachingSession,
    AssessmentAttempt,
    ProgressRecord
)
from backend.app.main import app

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[db_module.get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_database_per_test():
    db_module.Base.metadata.drop_all(bind=test_engine)
    db_module.Base.metadata.create_all(bind=test_engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
