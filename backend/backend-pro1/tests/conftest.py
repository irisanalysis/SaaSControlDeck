"""
Pytest configuration and fixtures for data source connection tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio

# Import application modules
from shared.database import Database
from shared.redis_client import RedisClient
from shared.models.user import User
from shared.models.data_source import (
    DataSource, DataSourceCreate, UploadSession, UploadSessionCreate,
    DataSourceStatus, UploadSessionStatus, DataSourceType
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_upload_dir():
    """Create temporary directory for file uploads during tests"""
    temp_dir = tempfile.mkdtemp(prefix="test_uploads_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_csv_file(temp_upload_dir):
    """Create a sample CSV file for testing"""
    file_path = temp_upload_dir / "sample_data.csv"

    # Create sample data
    data = {
        'id': range(1, 101),
        'name': [f'User {i}' for i in range(1, 101)],
        'email': [f'user{i}@example.com' for i in range(1, 101)],
        'age': [20 + (i % 50) for i in range(1, 101)],
        'score': [50.5 + (i * 0.5) for i in range(1, 101)],
        'active': [i % 2 == 0 for i in range(1, 101)]
    }

    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)

    return file_path


@pytest.fixture
def sample_json_file(temp_upload_dir):
    """Create a sample JSON file for testing"""
    file_path = temp_upload_dir / "sample_data.json"

    data = [
        {"id": i, "name": f"Item {i}", "value": i * 10, "category": "A" if i % 2 == 0 else "B"}
        for i in range(1, 51)
    ]

    import json
    with open(file_path, 'w') as f:
        json.dump(data, f)

    return file_path


@pytest.fixture
def sample_excel_file(temp_upload_dir):
    """Create a sample Excel file for testing"""
    file_path = temp_upload_dir / "sample_data.xlsx"

    data = {
        'Product': [f'Product {i}' for i in range(1, 26)],
        'Price': [19.99 + (i * 5) for i in range(1, 26)],
        'Category': ['Electronics' if i % 3 == 0 else 'Clothing' for i in range(1, 26)],
        'Stock': [100 - (i * 2) for i in range(1, 26)]
    }

    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)

    return file_path


@pytest.fixture
def invalid_file(temp_upload_dir):
    """Create an invalid file for testing"""
    file_path = temp_upload_dir / "invalid.txt"
    with open(file_path, 'w') as f:
        f.write("This is not a valid data file")
    return file_path


@pytest.fixture
def empty_file(temp_upload_dir):
    """Create an empty file for testing"""
    file_path = temp_upload_dir / "empty.csv"
    file_path.touch()
    return file_path


@pytest.fixture
def large_file(temp_upload_dir):
    """Create a large file for testing file size limits"""
    file_path = temp_upload_dir / "large_file.csv"

    # Create a file larger than MAX_FILE_SIZE (100MB)
    with open(file_path, 'w') as f:
        f.write("id,data\n")
        for i in range(2000000):  # Write 2M rows to exceed size limit
            f.write(f"{i},{'x' * 50}\n")

    return file_path


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_project():
    """Create a mock project for testing"""
    return {
        "id": 1,
        "name": "Test Project",
        "user_id": 1,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    mock_db = AsyncMock()

    # Mock common database operations
    mock_db.fetch_one = AsyncMock()
    mock_db.fetch_all = AsyncMock()
    mock_db.fetch_val = AsyncMock()
    mock_db.execute = AsyncMock()

    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    mock_redis = AsyncMock()

    mock_redis.get = AsyncMock()
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.exists = AsyncMock()

    return mock_redis


@pytest.fixture
def sample_upload_session():
    """Create a sample upload session for testing"""
    return UploadSession(
        id="test-session-123",
        user_id=1,
        project_id=1,
        filename="test_file.csv",
        file_size=1024,
        uploaded_size=0,
        chunk_size=512,
        total_chunks=2,
        uploaded_chunks=0,
        status=UploadSessionStatus.UPLOADING,
        dataset_id=None,
        error_message=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )


@pytest.fixture
def sample_data_source():
    """Create a sample data source for testing"""
    return DataSource(
        id=1,
        project_id=1,
        name="Test Dataset",
        type=DataSourceType.CSV,
        file_path="/tmp/test_file.csv",
        file_size=1024,
        rows_count=100,
        columns_count=5,
        status=DataSourceStatus.READY,
        metadata=None,
        file_hash="abc123",
        original_filename="test_file.csv",
        mime_type="text/csv",
        encoding="utf-8",
        delimiter=",",
        has_header=True,
        preview_data=None,
        error_details=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        processing_started_at=None,
        processing_completed_at=None
    )


@pytest.fixture
def sample_column_info():
    """Create sample column information for testing"""
    return [
        {
            "column_name": "id",
            "column_index": 0,
            "data_type": "number",
            "is_nullable": False,
            "unique_count": 100,
            "missing_count": 0,
            "min_value": "1",
            "max_value": "100",
            "avg_value": 50.5,
            "std_value": 28.87,
            "sample_values": ["1", "2", "3", "4", "5"]
        },
        {
            "column_name": "name",
            "column_index": 1,
            "data_type": "string",
            "is_nullable": False,
            "unique_count": 100,
            "missing_count": 0,
            "min_value": None,
            "max_value": None,
            "avg_value": None,
            "std_value": None,
            "sample_values": ["User 1", "User 2", "User 3", "User 4", "User 5"]
        }
    ]


@pytest.fixture
def file_upload_test_data():
    """Test data for file upload scenarios"""
    return {
        "valid_files": [
            {"filename": "data.csv", "content_type": "text/csv", "size": 1024},
            {"filename": "data.json", "content_type": "application/json", "size": 2048},
            {"filename": "data.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "size": 4096},
        ],
        "invalid_files": [
            {"filename": "data.txt", "content_type": "text/plain", "size": 1024, "error": "不支持的文件类型"},
            {"filename": "data.pdf", "content_type": "application/pdf", "size": 1024, "error": "不支持的文件类型"},
            {"filename": "", "content_type": "text/csv", "size": 1024, "error": "文件名不能为空"},
        ],
        "large_file": {"filename": "large.csv", "content_type": "text/csv", "size": 200 * 1024 * 1024},  # 200MB
    }


class MockUploadFile:
    """Mock UploadFile for testing"""

    def __init__(self, filename: str, content_type: str, content: bytes):
        self.filename = filename
        self.content_type = content_type
        self._content = content
        self.size = len(content)

    async def read(self) -> bytes:
        return self._content

    async def seek(self, position: int) -> None:
        pass

    async def close(self) -> None:
        pass


@pytest.fixture
def mock_upload_file_factory():
    """Factory to create mock upload files"""
    def create_mock_file(filename: str, content_type: str, content: str = "test content") -> MockUploadFile:
        return MockUploadFile(filename, content_type, content.encode())

    return create_mock_file


# Async fixtures for database testing
@pytest_asyncio.fixture
async def async_database_session():
    """Create an async database session for testing"""
    # This would typically set up a test database
    # For now, we'll mock it
    mock_session = AsyncMock()
    yield mock_session


@pytest_asyncio.fixture
async def async_redis_session():
    """Create an async Redis session for testing"""
    # This would typically set up a test Redis instance
    # For now, we'll mock it
    mock_session = AsyncMock()
    yield mock_session


# Test utilities
def create_test_data_source(**overrides) -> Dict[str, Any]:
    """Helper to create test data source data"""
    base_data = {
        "name": "Test Data Source",
        "type": DataSourceType.CSV,
        "project_id": 1,
        "file_path": "/tmp/test.csv",
        "file_size": 1024,
        "rows_count": 100,
        "columns_count": 5,
        "status": DataSourceStatus.READY,
        "original_filename": "test.csv",
        "mime_type": "text/csv",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    base_data.update(overrides)
    return base_data


def create_test_upload_session(**overrides) -> Dict[str, Any]:
    """Helper to create test upload session data"""
    base_data = {
        "id": "test-session",
        "user_id": 1,
        "project_id": 1,
        "filename": "test.csv",
        "file_size": 1024,
        "chunk_size": 512,
        "total_chunks": 2,
        "status": UploadSessionStatus.UPLOADING,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    base_data.update(overrides)
    return base_data