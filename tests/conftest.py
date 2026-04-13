"""
Test fixtures for all phases.
Sets up a test database (in-memory SQLite) and a FastAPI test client.
"""
import sys
import os
import uuid
import pytest
from datetime import datetime, timezone

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models.user import User


# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_freelancer.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

# Enable foreign keys for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Fixed test user IDs
TEST_USER_ID = "11111111-1111-1111-1111-111111111111"
TEST_USER_ID_2 = "22222222-2222-2222-2222-222222222222"


def override_get_db():
    """Override the database dependency for tests."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create clean database tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()

    # Create test user
    user = User(
        id=TEST_USER_ID,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$test_hash_placeholder",
    )
    session.add(user)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def second_user(db):
    """Create a second test user for isolation tests."""
    user = User(
        id=TEST_USER_ID_2,
        username="testuser2",
        email="test2@example.com",
        password_hash="$2b$12$test_hash_placeholder_2",
    )
    db.add(user)
    db.commit()
    return user
