from __future__ import annotations

import sys
from pathlib import Path

# Add server to python path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import User
from security import hash_password, create_token

# In-memory SQLite for testing
DATABASE_URL = "sqlite://"

@pytest.fixture(name="db_engine")
def fixture_db_engine():
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="db_session")
def fixture_db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def fixture_client(db_session: Session):
    # Override get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        # Fetch CSRF token
        response = test_client.get("/api/health")
        csrf_token = test_client.cookies.get("csrftoken")
        if csrf_token:
            test_client.headers.update({"x-csrftoken": csrf_token})
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_admin")
def fixture_test_admin(db_session: Session) -> User:
    admin = User(
        username="testadmin",
        full_name="Test Admin User",
        password_hash=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(name="test_operator")
def fixture_test_operator(db_session: Session) -> User:
    operator = User(
        username="testoperator",
        full_name="Test Operator User",
        password_hash=hash_password("operatorpass"),
        role="operator",
        is_active=True
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    return operator


@pytest.fixture(name="admin_token")
def fixture_admin_token(test_admin: User) -> str:
    return create_token(test_admin.username, test_admin.role)


@pytest.fixture(name="operator_token")
def fixture_operator_token(test_operator: User) -> str:
    return create_token(test_operator.username, test_operator.role)



@pytest.fixture(name="admin_headers")
def fixture_admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(name="operator_headers")
def fixture_operator_headers(operator_token: str) -> dict:
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture(name="agent_token")
def fixture_agent_token() -> str:
    return create_token("PC-REQ-DEV", "agent")


@pytest.fixture(name="agent_headers")
def fixture_agent_headers(agent_token: str) -> dict:
    return {"Authorization": f"Bearer {agent_token}"}

