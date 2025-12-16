import pytest
from app.database import Base, URLMapping
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.routes import get_db

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool # Ensures one db session for all tests
)

TestSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=test_engine
)

@pytest.fixture(autouse=True, scope="function")
def test_db():
    print(f"\n=== BEFORE CREATE: Tables in Base.metadata: {list(Base.metadata.tables.keys())}")
    Base.metadata.create_all(bind=test_engine)
    print(f"=== AFTER CREATE: Tables created!")
    yield
    Base.metadata.drop_all(bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override to use test database
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)