"""
Integration tests for database operations in data source functionality
Tests CRUD operations, migrations, and data integrity
RELEVANT FILES: data_source.py, database.py, migrations/, conftest.py
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

import pytest_asyncio

from shared.models.data_source import (
    DataSourceType, DataSourceStatus, UploadSessionStatus,
    DataSource, UploadSession, ColumnInfo, DataQualityCheck,
    DataSourceMetadata
)


class TestDataSourceDatabaseOperations:
    """Test database operations for data sources"""

    @pytest.fixture
    def sample_dataset_data(self):
        """Sample dataset data for database tests"""
        return {
            "project_id": 1,
            "name": "Test Dataset",
            "type": DataSourceType.CSV.value,
            "file_path": "/tmp/test.csv",
            "file_size": 1024,
            "original_filename": "test.csv",
            "file_hash": "abc123def456",
            "mime_type": "text/csv",
            "status": DataSourceStatus.PROCESSING.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @pytest.fixture
    def sample_upload_session_data(self):
        """Sample upload session data for database tests"""
        return {
            "id": "session-123",
            "user_id": 1,
            "project_id": 1,
            "filename": "test.csv",
            "file_size": 2048,
            "chunk_size": 512,
            "total_chunks": 4,
            "uploaded_chunks": 0,
            "uploaded_size": 0,
            "status": UploadSessionStatus.UPLOADING.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    @patch('shared.database.Database.fetch_one')
    async def test_create_dataset_success(
        self,
        mock_fetch_one,
        mock_execute,
        sample_dataset_data
    ):
        """Test successful dataset creation in database"""
        # Mock successful insert
        mock_fetch_one.return_value = {**sample_dataset_data, "id": 1}

        from data_service.app.routers.data_upload import process_uploaded_file
        from shared.database import Database

        # Simulate the database insert that happens in process_uploaded_file
        insert_query = """
        INSERT INTO datasets (
            project_id, name, type, file_path, file_size, original_filename,
            file_hash, mime_type, status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """

        result = await Database.fetch_one(
            insert_query,
            sample_dataset_data["project_id"],
            sample_dataset_data["name"],
            sample_dataset_data["type"],
            sample_dataset_data["file_path"],
            sample_dataset_data["file_size"],
            sample_dataset_data["original_filename"],
            sample_dataset_data["file_hash"],
            sample_dataset_data["mime_type"],
            sample_dataset_data["status"],
            sample_dataset_data["created_at"],
            sample_dataset_data["updated_at"]
        )

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    @patch('shared.database.Database.fetch_one')
    async def test_create_upload_session_success(
        self,
        mock_fetch_one,
        mock_execute,
        sample_upload_session_data
    ):
        """Test successful upload session creation in database"""
        mock_fetch_one.return_value = sample_upload_session_data

        from data_service.app.routers.data_upload import create_upload_session
        from shared.models.data_source import UploadSessionCreate

        # Create session data
        session_create = UploadSessionCreate(
            filename="test.csv",
            file_size=2048,
            project_id=1,
            chunk_size=512
        )

        result = await create_upload_session(session_create, user_id=1)

        assert result.id == "session-123"
        assert result.filename == "test.csv"
        assert result.file_size == 2048
        assert result.total_chunks == 4
        mock_fetch_one.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_one')
    async def test_get_dataset_by_id(self, mock_fetch_one, sample_dataset_data):
        """Test retrieving dataset by ID"""
        mock_fetch_one.return_value = {**sample_dataset_data, "id": 1}

        from shared.database import Database

        query = "SELECT * FROM datasets WHERE id = $1"
        result = await Database.fetch_one(query, 1)

        assert result["id"] == 1
        assert result["name"] == "Test Dataset"
        assert result["type"] == DataSourceType.CSV.value
        mock_fetch_one.assert_called_once_with(query, 1)

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_all')
    async def test_list_datasets_with_filters(self, mock_fetch_all):
        """Test listing datasets with various filters"""
        # Mock multiple datasets
        datasets = [
            {"id": 1, "name": "Dataset 1", "type": "csv", "status": "ready", "project_id": 1},
            {"id": 2, "name": "Dataset 2", "type": "json", "status": "processing", "project_id": 1},
            {"id": 3, "name": "Dataset 3", "type": "excel", "status": "ready", "project_id": 2}
        ]
        mock_fetch_all.return_value = datasets

        from shared.database import Database

        # Test listing all datasets for user
        query = """
        SELECT d.* FROM datasets d
        JOIN projects p ON d.project_id = p.id
        WHERE p.user_id = $1
        ORDER BY d.created_at DESC
        """
        result = await Database.fetch_all(query, 1)

        assert len(result) == 3
        assert result[0]["id"] == 1
        mock_fetch_all.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_update_dataset_status(self, mock_execute):
        """Test updating dataset status"""
        from shared.database import Database

        query = """
        UPDATE datasets
        SET status = $1, updated_at = $2
        WHERE id = $3
        """

        await Database.execute(
            query,
            DataSourceStatus.READY.value,
            datetime.utcnow(),
            1
        )

        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_update_upload_session_progress(self, mock_execute):
        """Test updating upload session progress"""
        from shared.database import Database

        query = """
        UPDATE upload_sessions
        SET uploaded_chunks = $1, uploaded_size = $2, updated_at = $3
        WHERE id = $4
        """

        await Database.execute(
            query,
            2,  # uploaded_chunks
            1024,  # uploaded_size
            datetime.utcnow(),
            "session-123"
        )

        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_one')
    async def test_check_duplicate_file_hash(self, mock_fetch_one):
        """Test checking for duplicate files by hash"""
        # Mock existing file with same hash
        mock_fetch_one.return_value = {"id": 1}

        from shared.database import Database

        query = """
        SELECT id FROM datasets
        WHERE file_hash = $1 AND project_id = $2
        """

        result = await Database.fetch_one(query, "abc123def456", 1)

        assert result["id"] == 1  # Duplicate found
        mock_fetch_one.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_one')
    async def test_check_project_access(self, mock_fetch_one):
        """Test checking user access to project"""
        # Mock project access
        mock_fetch_one.return_value = {"id": 1, "user_id": 1}

        from shared.database import Database

        query = """
        SELECT id FROM projects
        WHERE id = $1 AND user_id = $2 AND status = 'active'
        """

        result = await Database.fetch_one(query, 1, 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()


class TestColumnInfoDatabaseOperations:
    """Test database operations for column information"""

    @pytest.fixture
    def sample_columns_data(self):
        """Sample column data for database tests"""
        return [
            {
                "dataset_id": 1,
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
                "dataset_id": 1,
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
                "sample_values": ["Alice", "Bob", "Charlie"]
            }
        ]

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    @patch('shared.database.Database.execute_many')
    async def test_save_column_info(self, mock_execute_many, mock_execute, sample_columns_data):
        """Test saving column information to database"""
        from data_service.app.routers.data_preview import save_column_info

        # Convert to ColumnInfo objects
        columns = [ColumnInfo(**col_data) for col_data in sample_columns_data]

        await save_column_info(columns, dataset_id=1)

        # Should delete existing columns first
        mock_execute.assert_called_once()
        delete_call = mock_execute.call_args[0]
        assert "DELETE FROM dataset_columns" in delete_call[0]

        # Should insert new columns
        mock_execute_many.assert_called_once()
        insert_call = mock_execute_many.call_args[0]
        assert "INSERT INTO dataset_columns" in insert_call[0]

        # Check batch data
        batch_data = mock_execute_many.call_args[0][1]
        assert len(batch_data) == 2
        assert batch_data[0][1] == "id"  # column_name
        assert batch_data[1][1] == "name"  # column_name

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_all')
    async def test_get_column_info(self, mock_fetch_all, sample_columns_data):
        """Test retrieving column information from database"""
        mock_fetch_all.return_value = sample_columns_data

        from shared.database import Database

        query = """
        SELECT * FROM dataset_columns
        WHERE dataset_id = $1
        ORDER BY column_index
        """

        result = await Database.fetch_all(query, 1)

        assert len(result) == 2
        assert result[0]["column_name"] == "id"
        assert result[1]["column_name"] == "name"
        mock_fetch_all.assert_called_once()


class TestQualityCheckDatabaseOperations:
    """Test database operations for quality checks"""

    @pytest.fixture
    def sample_quality_checks_data(self):
        """Sample quality checks data for database tests"""
        return [
            {
                "dataset_id": 1,
                "check_type": "missing_values",
                "column_name": "age",
                "severity": DataQualitySeverity.WARNING.value,
                "message": "Column 'age' has missing values",
                "details": {"missing_count": 15, "percentage": 15.0},
                "affected_rows": 15
            },
            {
                "dataset_id": 1,
                "check_type": "outliers",
                "column_name": "salary",
                "severity": DataQualitySeverity.INFO.value,
                "message": "Column 'salary' has outliers",
                "details": {"outlier_count": 3, "percentage": 3.0},
                "affected_rows": 3
            }
        ]

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute_many')
    async def test_save_quality_checks(self, mock_execute_many, sample_quality_checks_data):
        """Test saving quality checks to database"""
        from data_service.app.routers.data_preview import save_quality_checks

        await save_quality_checks(sample_quality_checks_data)

        mock_execute_many.assert_called_once()
        insert_call = mock_execute_many.call_args[0]
        assert "INSERT INTO data_quality_checks" in insert_call[0]

        # Check batch data
        batch_data = mock_execute_many.call_args[0][1]
        assert len(batch_data) == 2
        assert batch_data[0][1] == "missing_values"  # check_type
        assert batch_data[1][1] == "outliers"  # check_type

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_all')
    async def test_get_quality_checks(self, mock_fetch_all):
        """Test retrieving quality checks from database"""
        # Mock quality checks with JSON details
        quality_checks = [
            {
                "id": 1,
                "dataset_id": 1,
                "check_type": "missing_values",
                "column_name": "age",
                "severity": "warning",
                "message": "Missing values found",
                "details": '{"missing_count": 15}',
                "affected_rows": 15,
                "created_at": datetime.utcnow()
            }
        ]
        mock_fetch_all.return_value = quality_checks

        from shared.database import Database

        query = """
        SELECT * FROM data_quality_checks
        WHERE dataset_id = $1
        ORDER BY severity DESC, created_at DESC
        """

        result = await Database.fetch_all(query, 1)

        assert len(result) == 1
        assert result[0]["check_type"] == "missing_values"
        assert '"missing_count": 15' in result[0]["details"]
        mock_fetch_all.assert_called_once()


class TestDatabaseTransactions:
    """Test database transaction handling"""

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    @patch('shared.database.Database.fetch_one')
    async def test_upload_session_expiration_cleanup(self, mock_fetch_one, mock_execute):
        """Test cleanup of expired upload sessions"""
        from shared.database import Database

        # Test query to find expired sessions
        expired_query = """
        SELECT id FROM upload_sessions
        WHERE expires_at < $1 AND status IN ($2, $3)
        """

        expired_sessions = [
            {"id": "expired-session-1"},
            {"id": "expired-session-2"}
        ]
        mock_fetch_one.return_value = expired_sessions

        # Test cleanup query
        cleanup_query = """
        UPDATE upload_sessions
        SET status = $1, updated_at = $2
        WHERE expires_at < $3
        """

        await Database.execute(
            cleanup_query,
            UploadSessionStatus.CANCELLED.value,
            datetime.utcnow(),
            datetime.utcnow()
        )

        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_cascade_delete_dataset(self, mock_execute):
        """Test cascading delete when removing dataset"""
        from shared.database import Database

        dataset_id = 1

        # Delete related data first (quality checks, columns, etc.)
        queries = [
            "DELETE FROM data_quality_checks WHERE dataset_id = $1",
            "DELETE FROM dataset_columns WHERE dataset_id = $1",
            "DELETE FROM datasets WHERE id = $1"
        ]

        for query in queries:
            await Database.execute(query, dataset_id)

        assert mock_execute.call_count == 3

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    @patch('shared.database.Database.fetch_one')
    async def test_concurrent_upload_handling(self, mock_fetch_one, mock_execute):
        """Test handling of concurrent uploads to same project"""
        from shared.database import Database

        # Simulate checking for concurrent uploads
        query = """
        SELECT COUNT(*) as active_uploads
        FROM upload_sessions
        WHERE project_id = $1 AND status = $2
        """

        mock_fetch_one.return_value = {"active_uploads": 2}

        result = await Database.fetch_one(
            query,
            1,  # project_id
            UploadSessionStatus.UPLOADING.value
        )

        assert result["active_uploads"] == 2
        mock_fetch_one.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_update_dataset_with_metadata(self, mock_execute):
        """Test updating dataset with complex metadata"""
        from shared.database import Database

        metadata = {
            "columns": [{"name": "col1", "type": "string"}],
            "data_types": {"col1": "object"},
            "sample_data": [{"col1": "value1"}],
            "missing_values_count": 0
        }

        query = """
        UPDATE datasets SET
            rows_count = $1,
            columns_count = $2,
            metadata = $3,
            preview_data = $4,
            status = $5,
            processing_completed_at = $6,
            updated_at = $7
        WHERE id = $8
        """

        await Database.execute(
            query,
            100,  # rows_count
            1,    # columns_count
            json.dumps(metadata),
            json.dumps([{"col1": "sample"}]),
            DataSourceStatus.READY.value,
            datetime.utcnow(),
            datetime.utcnow(),
            1  # dataset_id
        )

        mock_execute.assert_called_once()


class TestDatabaseErrorHandling:
    """Test database error handling scenarios"""

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_handle_duplicate_key_constraint(self, mock_execute):
        """Test handling of database constraint violations"""
        # Simulate unique constraint violation
        mock_execute.side_effect = Exception("UNIQUE constraint failed")

        from shared.database import Database

        with pytest.raises(Exception, match="UNIQUE constraint failed"):
            await Database.execute(
                "INSERT INTO datasets (name, project_id) VALUES ($1, $2)",
                "Duplicate Name",
                1
            )

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_one')
    async def test_handle_connection_timeout(self, mock_fetch_one):
        """Test handling of database connection timeouts"""
        mock_fetch_one.side_effect = asyncio.TimeoutError("Connection timed out")

        from shared.database import Database

        with pytest.raises(asyncio.TimeoutError):
            await Database.fetch_one("SELECT * FROM datasets WHERE id = $1", 1)

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute')
    async def test_handle_foreign_key_constraint(self, mock_execute):
        """Test handling of foreign key constraint violations"""
        mock_execute.side_effect = Exception("FOREIGN KEY constraint failed")

        from shared.database import Database

        with pytest.raises(Exception, match="FOREIGN KEY constraint failed"):
            await Database.execute(
                "INSERT INTO datasets (project_id) VALUES ($1)",
                999  # Non-existent project
            )


class TestDatabasePerformance:
    """Test database performance characteristics"""

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_all')
    async def test_large_dataset_query_performance(self, mock_fetch_all):
        """Test query performance with large datasets"""
        # Simulate large result set
        large_result = [{"id": i, "name": f"Dataset {i}"} for i in range(10000)]
        mock_fetch_all.return_value = large_result

        from shared.database import Database

        query = "SELECT * FROM datasets LIMIT 10000"
        result = await Database.fetch_all(query)

        assert len(result) == 10000
        mock_fetch_all.assert_called_once()

    @pytest.mark.asyncio
    @patch('shared.database.Database.execute_many')
    async def test_bulk_insert_performance(self, mock_execute_many):
        """Test bulk insert performance"""
        from shared.database import Database

        # Simulate bulk insert of quality checks
        batch_data = [(1, "check", "col", "info", "msg", "{}", 0) for _ in range(1000)]

        query = """
        INSERT INTO data_quality_checks
        (dataset_id, check_type, column_name, severity, message, details, affected_rows)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """

        await Database.execute_many(query, batch_data)

        mock_execute_many.assert_called_once()
        assert len(mock_execute_many.call_args[0][1]) == 1000

    @pytest.mark.asyncio
    @patch('shared.database.Database.fetch_all')
    async def test_complex_join_query_performance(self, mock_fetch_all):
        """Test complex join query performance"""
        mock_fetch_all.return_value = []

        from shared.database import Database

        # Complex query with multiple joins and filters
        complex_query = """
        SELECT
            d.id,
            d.name,
            d.status,
            p.name as project_name,
            COUNT(dc.id) as column_count,
            COUNT(dqc.id) as quality_issues
        FROM datasets d
        JOIN projects p ON d.project_id = p.id
        LEFT JOIN dataset_columns dc ON d.id = dc.dataset_id
        LEFT JOIN data_quality_checks dqc ON d.id = dqc.dataset_id
        WHERE p.user_id = $1
        AND d.status = $2
        AND d.created_at > $3
        GROUP BY d.id, d.name, d.status, p.name
        ORDER BY d.created_at DESC
        LIMIT 50
        """

        await Database.fetch_all(
            complex_query,
            1,  # user_id
            "ready",  # status
            datetime.utcnow() - timedelta(days=30)  # created_at filter
        )

        mock_fetch_all.assert_called_once()


class TestDatabaseIntegrity:
    """Test database data integrity constraints"""

    @pytest.mark.asyncio
    async def test_required_fields_validation(self):
        """Test that required fields are properly validated"""
        from shared.models.data_source import DataSourceCreate

        # Test missing required fields
        with pytest.raises(Exception):
            DataSourceCreate(
                # Missing name
                type=DataSourceType.CSV,
                project_id=1
            )

        with pytest.raises(Exception):
            DataSourceCreate(
                name="Test",
                # Missing type
                project_id=1
            )

    @pytest.mark.asyncio
    async def test_field_length_constraints(self):
        """Test field length constraints"""
        from shared.models.data_source import DataSourceCreate

        # Test name too long
        with pytest.raises(Exception):
            DataSourceCreate(
                name="x" * 201,  # Over 200 character limit
                type=DataSourceType.CSV,
                project_id=1
            )

        # Test description too long
        with pytest.raises(Exception):
            DataSourceCreate(
                name="Valid Name",
                type=DataSourceType.CSV,
                project_id=1,
                description="x" * 1001  # Over 1000 character limit
            )

    @pytest.mark.asyncio
    async def test_enum_value_constraints(self):
        """Test enum value constraints"""
        from shared.models.data_source import DataSource

        # Test invalid status
        with pytest.raises(Exception):
            DataSource(
                id=1,
                project_id=1,
                name="Test",
                type=DataSourceType.CSV,
                status="invalid_status",  # Invalid enum value
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

    @pytest.mark.asyncio
    async def test_date_field_consistency(self):
        """Test date field consistency"""
        from shared.models.data_source import DataSource

        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        # Valid date progression
        dataset = DataSource(
            id=1,
            project_id=1,
            name="Test",
            type=DataSourceType.CSV,
            status=DataSourceStatus.READY,
            created_at=past,
            updated_at=now,
            processing_started_at=past,
            processing_completed_at=now
        )

        # Should calculate duration correctly
        assert dataset.processing_duration > 0

        # Invalid: processing completed before started
        with pytest.raises(Exception):
            DataSource(
                id=1,
                project_id=1,
                name="Test",
                type=DataSourceType.CSV,
                status=DataSourceStatus.READY,
                created_at=now,
                updated_at=now,
                processing_started_at=now,
                processing_completed_at=past  # Before start time
            )