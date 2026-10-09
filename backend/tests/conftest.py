import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import backend.app.database as db_module
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

TEST_DB_PATH = (root_dir / "backend" / "tests" / "test_runner.db").as_posix()

test_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Direct all database calls in backend.app to isolated test engine
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

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
