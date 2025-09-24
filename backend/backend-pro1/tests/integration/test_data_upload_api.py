"""
Integration tests for data upload API endpoints
Tests complete API workflows, database interactions, and error handling
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from shared.models.data_source import (
    UploadSessionStatus, DataSourceStatus, DataSourceType
)
from data_service.app.main import app
from data_service.app.routers.data_upload import (
    MAX_FILE_SIZE, ALLOWED_TYPES, UPLOAD_DIR
)


class TestUploadSessionEndpoints:
    """Test upload session management endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        """Mock authenticated user"""
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @pytest.fixture
    def valid_session_data(self):
        """Valid session creation data"""
        return {
            "filename": "test_data.csv",
            "file_size": 1024,
            "project_id": 1,
            "chunk_size": 512
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    def test_create_upload_session_success(
        self,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        valid_session_data
    ):
        """Test successful upload session creation"""
        # Mock authentication
        mock_get_user.return_value = mock_auth_user

        # Mock project validation
        mock_db_fetch_one.side_effect = [
            {"id": 1},  # Project exists
            {  # Created session
                "id": "session-123",
                "user_id": 1,
                "project_id": 1,
                "filename": "test_data.csv",
                "file_size": 1024,
                "uploaded_size": 0,
                "chunk_size": 512,
                "total_chunks": 2,
                "uploaded_chunks": 0,
                "status": "uploading",
                "dataset_id": None,
                "error_message": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
        ]

        response = client.post("/session", json=valid_session_data)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "session-123"
        assert data["filename"] == "test_data.csv"
        assert data["file_size"] == 1024
        assert data["total_chunks"] == 2
        assert data["status"] == "uploading"

    @patch('shared.auth.get_current_user')
    def test_create_upload_session_file_too_large(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test session creation fails for oversized files"""
        mock_get_user.return_value = mock_auth_user

        large_file_data = {
            "filename": "large_file.csv",
            "file_size": MAX_FILE_SIZE + 1,  # Exceed limit
            "project_id": 1
        }

        response = client.post("/session", json=large_file_data)

        assert response.status_code == 400
        assert "文件大小超出限制" in response.json()["detail"]

    @patch('shared.auth.get_current_user')
    def test_create_upload_session_invalid_filename(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test session creation fails for invalid filenames"""
        mock_get_user.return_value = mock_auth_user

        invalid_filenames = [
            "",
            "file.txt",  # Unsupported extension
            "file.pdf",  # Unsupported extension
        ]

        for filename in invalid_filenames:
            session_data = {
                "filename": filename,
                "file_size": 1024,
                "project_id": 1
            }

            response = client.post("/session", json=session_data)
            assert response.status_code == 422  # Validation error

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_create_upload_session_project_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        valid_session_data
    ):
        """Test session creation fails for non-existent project"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # Project not found

        response = client.post("/session", json=valid_session_data)

        assert response.status_code == 404
        assert "项目不存在或无权限" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_upload_progress(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test getting upload progress"""
        mock_get_user.return_value = mock_auth_user

        # Mock session data
        session_data = {
            "id": "session-123",
            "user_id": 1,
            "project_id": 1,
            "filename": "test.csv",
            "file_size": 1024,
            "uploaded_size": 512,
            "chunk_size": 256,
            "total_chunks": 4,
            "uploaded_chunks": 2,
            "status": "uploading",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        mock_db_fetch_one.return_value = session_data

        response = client.get("/progress/session-123")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == "session-123"
        assert data["uploaded_chunks"] == 2
        assert data["total_chunks"] == 4
        assert data["progress_percentage"] == 50.0

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_upload_progress_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test getting progress for non-existent session"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None

        response = client.get("/progress/nonexistent-session")

        assert response.status_code == 404
        assert "上传会话不存在" in response.json()["detail"]


class TestFileUploadEndpoints:
    """Test file upload endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    @patch('data_service.app.routers.data_upload.process_uploaded_file')
    def test_upload_file_success(
        self,
        mock_process_file,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_csv_file
    ):
        """Test successful file upload"""
        mock_get_user.return_value = mock_auth_user

        # Mock project validation
        mock_db_fetch_one.side_effect = [
            {"id": 1},  # Project exists
            {  # Created session
                "id": "session-123",
                "user_id": 1,
                "project_id": 1,
                "filename": "test.csv",
                "file_size": 1024,
                "chunk_size": 1024,
                "total_chunks": 1,
                "status": "uploading",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
        ]

        # Mock background task
        mock_process_file.return_value = None

        # Read test file
        with open(sample_csv_file, 'rb') as f:
            file_content = f.read()

        files = {"file": ("test.csv", BytesIO(file_content), "text/csv")}
        data = {"project_id": "1"}

        response = client.post("/file", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["session_id"] == "session-123"
        assert "文件上传成功" in result["message"]

    @patch('shared.auth.get_current_user')
    def test_upload_file_invalid_extension(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test file upload fails for invalid file extension"""
        mock_get_user.return_value = mock_auth_user

        # Create invalid file
        invalid_content = b"This is not a valid data file"
        files = {"file": ("invalid.txt", BytesIO(invalid_content), "text/plain")}
        data = {"project_id": "1"}

        response = client.post("/file", files=files, data=data)

        assert response.status_code == 400
        assert "不支持的文件类型" in response.json()["detail"]

    @patch('shared.auth.get_current_user')
    def test_upload_file_too_large(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test file upload fails for oversized files"""
        mock_get_user.return_value = mock_auth_user

        # Create oversized file content
        large_content = b"A" * (MAX_FILE_SIZE + 1)
        files = {"file": ("large.csv", BytesIO(large_content), "text/csv")}
        data = {"project_id": "1"}

        response = client.post("/file", files=files, data=data)

        assert response.status_code == 400
        assert "文件大小超出限制" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_upload_file_project_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test file upload fails for non-existent project"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # Project not found

        content = b"id,name\n1,test"
        files = {"file": ("test.csv", BytesIO(content), "text/csv")}
        data = {"project_id": "999"}

        response = client.post("/file", files=files, data=data)

        assert response.status_code == 404
        assert "项目不存在或无权限" in response.json()["detail"]


class TestChunkUploadEndpoints:
    """Test chunked file upload endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @pytest.fixture
    def sample_session(self):
        """Sample upload session for testing"""
        return {
            "id": "session-123",
            "user_id": 1,
            "project_id": 1,
            "filename": "test.csv",
            "file_size": 1024,
            "uploaded_size": 0,
            "chunk_size": 512,
            "total_chunks": 2,
            "uploaded_chunks": 0,
            "status": "uploading",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=MagicMock)
    def test_upload_chunk_success(
        self,
        mock_open,
        mock_mkdir,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_session
    ):
        """Test successful chunk upload"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = sample_session

        chunk_data = b"chunk content"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}
        data = {"chunk_index": "0"}

        response = client.post("/chunk/session-123", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["chunk_index"] == 0
        assert result["uploaded_chunks"] == 1
        assert result["total_chunks"] == 2
        assert result["progress_percentage"] == 50.0
        assert result["is_complete"] is False

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_upload_chunk_session_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test chunk upload fails for non-existent session"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None

        chunk_data = b"chunk content"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}
        data = {"chunk_index": "0"}

        response = client.post("/chunk/nonexistent", files=files, data=data)

        assert response.status_code == 404
        assert "上传会话不存在" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_upload_chunk_invalid_status(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_session
    ):
        """Test chunk upload fails for invalid session status"""
        mock_get_user.return_value = mock_auth_user

        # Session with invalid status
        invalid_session = sample_session.copy()
        invalid_session["status"] = "completed"
        mock_db_fetch_one.return_value = invalid_session

        chunk_data = b"chunk content"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}
        data = {"chunk_index": "0"}

        response = client.post("/chunk/session-123", files=files, data=data)

        assert response.status_code == 400
        assert "上传会话状态无效" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_upload_chunk_expired_session(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_session
    ):
        """Test chunk upload fails for expired session"""
        mock_get_user.return_value = mock_auth_user

        # Expired session
        expired_session = sample_session.copy()
        expired_session["expires_at"] = datetime.utcnow() - timedelta(hours=1)
        mock_db_fetch_one.return_value = expired_session

        chunk_data = b"chunk content"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}
        data = {"chunk_index": "0"}

        response = client.post("/chunk/session-123", files=files, data=data)

        assert response.status_code == 400
        assert "上传会话已过期" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_upload_chunk_invalid_index(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_session
    ):
        """Test chunk upload fails for invalid chunk index"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = sample_session

        chunk_data = b"chunk content"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}

        # Test negative index
        data = {"chunk_index": "-1"}
        response = client.post("/chunk/session-123", files=files, data=data)
        assert response.status_code == 400
        assert "无效的分块索引" in response.json()["detail"]

        # Test index beyond total chunks
        data = {"chunk_index": "10"}  # Session has only 2 chunks
        response = client.post("/chunk/session-123", files=files, data=data)
        assert response.status_code == 400
        assert "无效的分块索引" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    @patch('data_service.app.routers.data_upload.merge_chunks')
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=MagicMock)
    def test_upload_final_chunk_triggers_merge(
        self,
        mock_open,
        mock_mkdir,
        mock_merge_chunks,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_session
    ):
        """Test that uploading final chunk triggers file merge"""
        mock_get_user.return_value = mock_auth_user

        # Session with almost all chunks uploaded
        final_session = sample_session.copy()
        final_session["uploaded_chunks"] = 1  # Only 1 chunk left
        mock_db_fetch_one.return_value = final_session

        mock_merge_chunks.return_value = None

        chunk_data = b"final chunk"
        files = {"chunk": ("chunk", BytesIO(chunk_data), "application/octet-stream")}
        data = {"chunk_index": "1"}  # Final chunk

        response = client.post("/chunk/session-123", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert result["is_complete"] is True
        assert result["progress_percentage"] == 100.0
        assert "文件上传完成" in result["message"]

        # Verify merge was called
        mock_merge_chunks.assert_called_once()


class TestUploadCancellation:
    """Test upload cancellation functionality"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_cancel_upload_success(
        self,
        mock_unlink,
        mock_exists,
        mock_rmtree,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test successful upload cancellation"""
        mock_get_user.return_value = mock_auth_user

        session_data = {
            "id": "session-123",
            "user_id": 1,
            "filename": "test.csv",
            "status": "uploading"
        }
        mock_db_fetch_one.return_value = session_data

        # Mock file system operations
        mock_exists.return_value = True

        response = client.delete("/session/session-123")

        assert response.status_code == 200
        result = response.json()
        assert "上传已取消" in result["message"]

        # Verify database update was called
        mock_db_execute.assert_called()

        # Verify cleanup was attempted
        mock_rmtree.assert_called()
        mock_unlink.assert_called()

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_cancel_upload_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test cancellation fails for non-existent session"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None

        response = client.delete("/session/nonexistent")

        assert response.status_code == 404
        assert "上传会话不存在" in response.json()["detail"]


class TestUploadSessionListing:
    """Test upload session listing endpoint"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_upload_sessions_success(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user
    ):
        """Test successful session listing"""
        mock_get_user.return_value = mock_auth_user

        # Mock total count
        mock_db_fetch_val.return_value = 2

        # Mock session data
        sessions_data = [
            {
                "id": "session-1",
                "user_id": 1,
                "project_id": 1,
                "filename": "file1.csv",
                "file_size": 1024,
                "chunk_size": 512,
                "total_chunks": 2,
                "status": "completed",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            },
            {
                "id": "session-2",
                "user_id": 1,
                "project_id": 1,
                "filename": "file2.json",
                "file_size": 2048,
                "chunk_size": 1024,
                "total_chunks": 2,
                "status": "uploading",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
        ]
        mock_db_fetch_all.return_value = sessions_data

        response = client.get("/sessions")

        assert response.status_code == 200
        result = response.json()

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["limit"] == 20
        assert result["offset"] == 0

        # Check session data
        assert result["items"][0]["id"] == "session-1"
        assert result["items"][1]["id"] == "session-2"

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_upload_sessions_with_filters(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user
    ):
        """Test session listing with status filter"""
        mock_get_user.return_value = mock_auth_user

        mock_db_fetch_val.return_value = 1
        mock_db_fetch_all.return_value = [
            {
                "id": "session-1",
                "user_id": 1,
                "project_id": 1,
                "filename": "file1.csv",
                "file_size": 1024,
                "chunk_size": 512,
                "total_chunks": 2,
                "status": "completed",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)
            }
        ]

        response = client.get("/sessions?status=completed&limit=10&offset=5")

        assert response.status_code == 200
        result = response.json()

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["limit"] == 10
        assert result["offset"] == 5
        assert result["items"][0]["status"] == "completed"

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_upload_sessions_pagination(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user
    ):
        """Test session listing pagination"""
        mock_get_user.return_value = mock_auth_user

        mock_db_fetch_val.return_value = 100  # Total count
        mock_db_fetch_all.return_value = []  # Empty page

        response = client.get("/sessions?limit=5&offset=10")

        assert response.status_code == 200
        result = response.json()

        assert result["total"] == 100
        assert result["limit"] == 5
        assert result["offset"] == 10
        assert len(result["items"]) == 0

    @patch('shared.auth.get_current_user')
    def test_list_upload_sessions_invalid_params(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test session listing with invalid parameters"""
        mock_get_user.return_value = mock_auth_user

        # Test invalid limit (too high)
        response = client.get("/sessions?limit=200")
        assert response.status_code == 422

        # Test invalid limit (negative)
        response = client.get("/sessions?limit=-1")
        assert response.status_code == 422

        # Test invalid offset (negative)
        response = client.get("/sessions?offset=-1")
        assert response.status_code == 422


class TestFileProcessingIntegration:
    """Test file processing integration"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('data_service.app.routers.data_upload.calculate_file_hash')
    @patch('data_service.app.routers.data_upload.get_file_type_from_filename')
    async def test_process_uploaded_file_success(
        self,
        mock_get_file_type,
        mock_calculate_hash,
        mock_db_execute,
        mock_db_fetch_one,
        temp_upload_dir,
        sample_upload_session
    ):
        """Test successful file processing"""
        from data_service.app.routers.data_upload import process_uploaded_file

        # Create test file
        test_file = temp_upload_dir / "test.csv"
        test_file.write_text("id,name\n1,test\n2,test2")

        # Mock dependencies
        mock_get_file_type.return_value = "csv"
        mock_calculate_hash.return_value = "abc123"

        # Mock database calls
        mock_db_fetch_one.side_effect = [
            None,  # No existing file with same hash
            {"id": 1}  # Created dataset
        ]

        result = await process_uploaded_file(
            test_file,
            sample_upload_session,
            user_id=1
        )

        assert result == 1  # Dataset ID
        mock_calculate_hash.assert_called_once()
        mock_get_file_type.assert_called_once()

    @patch('shared.database.Database.fetch_one')
    @patch('data_service.app.routers.data_upload.calculate_file_hash')
    async def test_process_uploaded_file_duplicate(
        self,
        mock_calculate_hash,
        mock_db_fetch_one,
        temp_upload_dir,
        sample_upload_session
    ):
        """Test file processing fails for duplicate files"""
        from data_service.app.routers.data_upload import process_uploaded_file

        # Create test file
        test_file = temp_upload_dir / "test.csv"
        test_file.write_text("id,name\n1,test")

        # Mock hash calculation
        mock_calculate_hash.return_value = "abc123"

        # Mock existing file
        mock_db_fetch_one.return_value = {"id": 1}  # Duplicate file exists

        with pytest.raises(Exception, match="文件已存在"):
            await process_uploaded_file(
                test_file,
                sample_upload_session,
                user_id=1
            )


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_auth_user(self):
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser"
        }

    @patch('shared.auth.get_current_user')
    def test_unauthenticated_requests(self, mock_get_user, client):
        """Test that unauthenticated requests are rejected"""
        mock_get_user.side_effect = Exception("Unauthorized")

        endpoints_to_test = [
            ("POST", "/session", {"filename": "test.csv", "file_size": 1024, "project_id": 1}),
            ("GET", "/progress/session-123", None),
            ("DELETE", "/session/session-123", None),
            ("GET", "/sessions", None),
        ]

        for method, endpoint, data in endpoints_to_test:
            if method == "POST" and data:
                if "session" in endpoint and "chunk" not in endpoint:
                    response = client.post(endpoint, json=data)
                else:
                    response = client.post(endpoint, data=data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Should fail due to authentication error
            assert response.status_code in [401, 403, 500]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_database_error_handling(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test handling of database errors"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.side_effect = Exception("Database connection failed")

        session_data = {
            "filename": "test.csv",
            "file_size": 1024,
            "project_id": 1
        }

        response = client.post("/session", json=session_data)

        # Should handle database error gracefully
        assert response.status_code == 500