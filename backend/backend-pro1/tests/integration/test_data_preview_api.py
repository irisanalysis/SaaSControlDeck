"""
Integration tests for data preview API endpoints
Tests complete API workflows for data analysis and preview functionality
RELEVANT FILES: data_preview.py, data_upload_api.py, conftest.py, test_data_source_models.py
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pandas as pd

from shared.models.data_source import (
    DataSourceStatus, DataQualitySeverity
)
from data_service.app.main import app


class TestDataPreviewEndpoints:
    """Test data preview API endpoints"""

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
    def sample_dataset_data(self):
        """Sample dataset for testing"""
        return {
            "id": 1,
            "project_id": 1,
            "name": "Test Dataset",
            "type": "csv",
            "status": "ready",
            "rows_count": 100,
            "columns_count": 5,
            "metadata": {
                "columns": [
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
                        "sample_values": ["Alice", "Bob", "Charlie", "David", "Eve"]
                    }
                ]
            },
            "preview_data": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"}
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @pytest.fixture
    def sample_column_data(self):
        """Sample column data for testing"""
        return [
            {
                "id": 1,
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
                "id": 2,
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
                "sample_values": ["Alice", "Bob", "Charlie", "David", "Eve"]
            }
        ]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_get_data_preview_success(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_dataset_data,
        sample_column_data
    ):
        """Test successful data preview retrieval"""
        mock_get_user.return_value = mock_auth_user

        # Mock dataset fetch
        mock_db_fetch_one.return_value = sample_dataset_data

        # Mock columns fetch
        mock_db_fetch_all.return_value = sample_column_data

        response = client.get("/datasets/1/preview")

        assert response.status_code == 200
        data = response.json()

        assert data["dataset_id"] == 1
        assert data["rows_count"] == 100
        assert data["columns_count"] == 5
        assert len(data["columns"]) == 2
        assert len(data["sample_data"]) == 3

        # Check column data
        id_column = next(col for col in data["columns"] if col["column_name"] == "id")
        assert id_column["data_type"] == "number"
        assert id_column["unique_count"] == 100

        # Check data types mapping
        assert data["data_types"]["id"] == "number"
        assert data["data_types"]["name"] == "string"

        # Check missing values summary
        assert data["missing_values_summary"]["id"] == 0
        assert data["missing_values_summary"]["name"] == 0

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_data_preview_dataset_not_found(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test preview fails when dataset not found"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # Dataset not found

        response = client.get("/datasets/999/preview")

        assert response.status_code == 404
        assert "数据集不存在或无权限访问" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_data_preview_wrong_status(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_dataset_data
    ):
        """Test preview fails when dataset is not ready"""
        mock_get_user.return_value = mock_auth_user

        # Dataset in processing state
        processing_dataset = sample_dataset_data.copy()
        processing_dataset["status"] = "processing"
        mock_db_fetch_one.return_value = processing_dataset

        response = client.get("/datasets/1/preview")

        assert response.status_code == 400
        assert "数据集状态为 processing，无法预览" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_data_preview_no_permission(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test preview fails when user has no permission"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # No access to dataset

        response = client.get("/datasets/1/preview")

        assert response.status_code == 404
        assert "数据集不存在或无权限访问" in response.json()["detail"]


class TestDatasetListingEndpoints:
    """Test dataset listing API endpoints"""

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
    def sample_datasets(self):
        """Sample datasets for listing tests"""
        return [
            {
                "id": 1,
                "project_id": 1,
                "name": "Dataset 1",
                "type": "csv",
                "status": "ready",
                "rows_count": 100,
                "columns_count": 5,
                "file_size": 1024,
                "created_at": datetime.utcnow() - timedelta(days=1),
                "updated_at": datetime.utcnow() - timedelta(days=1)
            },
            {
                "id": 2,
                "project_id": 1,
                "name": "Dataset 2",
                "type": "json",
                "status": "processing",
                "rows_count": None,
                "columns_count": None,
                "file_size": 2048,
                "created_at": datetime.utcnow() - timedelta(hours=12),
                "updated_at": datetime.utcnow() - timedelta(hours=12)
            },
            {
                "id": 3,
                "project_id": 2,
                "name": "Dataset 3",
                "type": "excel",
                "status": "ready",
                "rows_count": 50,
                "columns_count": 3,
                "file_size": 4096,
                "created_at": datetime.utcnow() - timedelta(hours=6),
                "updated_at": datetime.utcnow() - timedelta(hours=6)
            }
        ]

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_datasets_success(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user,
        sample_datasets
    ):
        """Test successful dataset listing"""
        mock_get_user.return_value = mock_auth_user

        # Mock total count
        mock_db_fetch_val.return_value = 3

        # Mock dataset data
        mock_db_fetch_all.return_value = sample_datasets

        response = client.get("/datasets")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1

        # Check dataset data
        assert data["items"][0]["id"] == 1
        assert data["items"][0]["name"] == "Dataset 1"
        assert data["items"][0]["type"] == "csv"

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_datasets_with_filters(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user,
        sample_datasets
    ):
        """Test dataset listing with filters"""
        mock_get_user.return_value = mock_auth_user

        # Mock filtered results
        filtered_datasets = [d for d in sample_datasets if d["status"] == "ready"]
        mock_db_fetch_val.return_value = len(filtered_datasets)
        mock_db_fetch_all.return_value = filtered_datasets

        response = client.get("/datasets?status=ready&type=csv&project_id=1")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 2
        assert all(item["status"] == "ready" for item in data["items"])

    @patch('shared.database.Database.fetch_val')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_list_datasets_pagination(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user
    ):
        """Test dataset listing pagination"""
        mock_get_user.return_value = mock_auth_user

        # Mock pagination
        mock_db_fetch_val.return_value = 100  # Total count
        mock_db_fetch_all.return_value = []   # Empty page

        response = client.get("/datasets?page=3&size=10")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 100
        assert data["page"] == 3
        assert data["size"] == 10
        assert data["pages"] == 10
        assert len(data["items"]) == 0

    @patch('shared.auth.get_current_user')
    def test_list_datasets_invalid_pagination(
        self,
        mock_get_user,
        client,
        mock_auth_user
    ):
        """Test dataset listing with invalid pagination parameters"""
        mock_get_user.return_value = mock_auth_user

        # Test invalid page
        response = client.get("/datasets?page=0")
        assert response.status_code == 422

        # Test invalid size
        response = client.get("/datasets?size=200")  # Over limit
        assert response.status_code == 422

        response = client.get("/datasets?size=0")
        assert response.status_code == 422


class TestQualityCheckEndpoints:
    """Test data quality check API endpoints"""

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
    def sample_quality_checks(self):
        """Sample quality checks for testing"""
        return [
            {
                "id": 1,
                "dataset_id": 1,
                "check_type": "missing_values",
                "column_name": "age",
                "severity": "warning",
                "message": "Column 'age' has 15 missing values (15.0%)",
                "details": '{"missing_count": 15, "total_count": 100, "percentage": 15.0}',
                "affected_rows": 15,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "dataset_id": 1,
                "check_type": "outliers",
                "column_name": "salary",
                "severity": "info",
                "message": "Column 'salary' has 3 outliers (3.0%)",
                "details": '{"outlier_count": 3, "percentage": 3.0, "lower_bound": 20000, "upper_bound": 100000}',
                "affected_rows": 3,
                "created_at": datetime.utcnow()
            },
            {
                "id": 3,
                "dataset_id": 1,
                "check_type": "duplicates",
                "column_name": None,
                "severity": "warning",
                "message": "Found 5 duplicate rows (5.0%)",
                "details": '{"duplicate_count": 5, "total_count": 100, "percentage": 5.0}',
                "affected_rows": 5,
                "created_at": datetime.utcnow()
            }
        ]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_get_quality_checks_success(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_quality_checks
    ):
        """Test successful quality checks retrieval"""
        mock_get_user.return_value = mock_auth_user

        # Mock dataset access check
        mock_db_fetch_one.return_value = {"id": 1}

        # Mock quality checks
        mock_db_fetch_all.return_value = sample_quality_checks

        response = client.get("/datasets/1/quality")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 3

        # Check first quality check (missing values)
        missing_check = next(check for check in data if check["check_type"] == "missing_values")
        assert missing_check["column_name"] == "age"
        assert missing_check["severity"] == "warning"
        assert missing_check["affected_rows"] == 15
        assert missing_check["details"]["missing_count"] == 15

        # Check outliers check
        outlier_check = next(check for check in data if check["check_type"] == "outliers")
        assert outlier_check["column_name"] == "salary"
        assert outlier_check["details"]["outlier_count"] == 3

        # Check duplicates check
        duplicate_check = next(check for check in data if check["check_type"] == "duplicates")
        assert duplicate_check["column_name"] is None
        assert duplicate_check["details"]["duplicate_count"] == 5

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_get_quality_checks_no_access(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test quality checks fails when no access to dataset"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # No access

        response = client.get("/datasets/999/quality")

        assert response.status_code == 404
        assert "数据集不存在或无权限访问" in response.json()["detail"]

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_get_quality_checks_empty_result(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test quality checks with no issues found"""
        mock_get_user.return_value = mock_auth_user

        # Mock dataset access
        mock_db_fetch_one.return_value = {"id": 1}

        # Mock empty quality checks
        mock_db_fetch_all.return_value = []

        response = client.get("/datasets/1/quality")

        assert response.status_code == 200
        data = response.json()

        assert data == []

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_get_quality_checks_malformed_details(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test quality checks with malformed JSON details"""
        mock_get_user.return_value = mock_auth_user

        # Mock dataset access
        mock_db_fetch_one.return_value = {"id": 1}

        # Mock quality check with invalid JSON
        malformed_check = {
            "id": 1,
            "dataset_id": 1,
            "check_type": "missing_values",
            "column_name": "test",
            "severity": "info",
            "message": "Test message",
            "details": "invalid json {",  # Malformed JSON
            "affected_rows": 1,
            "created_at": datetime.utcnow()
        }
        mock_db_fetch_all.return_value = [malformed_check]

        response = client.get("/datasets/1/quality")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        assert data[0]["details"] == {}  # Should default to empty dict


class TestAnalysisTriggerEndpoints:
    """Test analysis trigger API endpoints"""

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
    def sample_dataset_ready(self):
        """Sample dataset ready for analysis"""
        return {
            "id": 1,
            "project_id": 1,
            "name": "Test Dataset",
            "type": "csv",
            "status": "ready",
            "file_path": "/tmp/test.csv"
        }

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.execute')
    @patch('shared.auth.get_current_user')
    @patch('fastapi.BackgroundTasks.add_task')
    def test_trigger_analysis_success(
        self,
        mock_add_task,
        mock_get_user,
        mock_db_execute,
        mock_db_fetch_one,
        client,
        mock_auth_user,
        sample_dataset_ready
    ):
        """Test successful analysis trigger"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = sample_dataset_ready

        response = client.post("/datasets/1/analyze")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "数据分析任务已启动"
        assert data["dataset_id"] == 1

        # Verify status was updated to processing
        mock_db_execute.assert_called_once()
        execute_args = mock_db_execute.call_args[0]
        assert "UPDATE datasets SET status = $1" in execute_args[0]
        assert execute_args[1] == "processing"

        # Verify background task was added
        mock_add_task.assert_called_once()

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_trigger_analysis_no_access(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test analysis trigger fails when no access to dataset"""
        mock_get_user.return_value = mock_auth_user
        mock_db_fetch_one.return_value = None  # No access

        response = client.post("/datasets/999/analyze")

        assert response.status_code == 404
        assert "数据集不存在或无权限访问" in response.json()["detail"]


class TestErrorHandling:
    """Test error handling in data preview endpoints"""

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
            ("GET", "/datasets/1/preview"),
            ("GET", "/datasets"),
            ("GET", "/datasets/1/quality"),
            ("POST", "/datasets/1/analyze"),
        ]

        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint)

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

        response = client.get("/datasets/1/preview")

        # Should handle database error gracefully
        assert response.status_code == 500

    @patch('shared.database.Database.fetch_one')
    @patch('shared.auth.get_current_user')
    def test_invalid_dataset_id(
        self,
        mock_get_user,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test handling of invalid dataset IDs"""
        mock_get_user.return_value = mock_auth_user

        # Test negative ID
        response = client.get("/datasets/-1/preview")
        assert response.status_code == 422

        # Test zero ID
        response = client.get("/datasets/0/preview")
        # Depends on validation rules - could be 404 or 422

        # Test very large ID
        mock_db_fetch_one.return_value = None
        response = client.get("/datasets/999999999/preview")
        assert response.status_code == 404


class TestPerformanceAndScaling:
    """Test performance characteristics of preview endpoints"""

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
    def test_large_dataset_listing(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_val,
        client,
        mock_auth_user
    ):
        """Test listing performance with large number of datasets"""
        mock_get_user.return_value = mock_auth_user

        # Simulate large dataset count
        mock_db_fetch_val.return_value = 10000

        # Mock empty result for specific page
        mock_db_fetch_all.return_value = []

        # Test pagination limits
        response = client.get("/datasets?page=1&size=100")  # Max allowed size
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 10000
        assert data["pages"] == 100

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_large_preview_data_handling(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test handling of large preview datasets"""
        mock_get_user.return_value = mock_auth_user

        # Create large dataset with many columns and preview rows
        large_columns = []
        for i in range(100):  # 100 columns
            large_columns.append({
                "id": i,
                "dataset_id": 1,
                "column_name": f"col_{i}",
                "column_index": i,
                "data_type": "string",
                "is_nullable": False,
                "unique_count": 1000,
                "missing_count": 0,
                "sample_values": [f"value_{j}" for j in range(10)]
            })

        large_preview_data = []
        for i in range(100):  # 100 preview rows
            row = {f"col_{j}": f"value_{i}_{j}" for j in range(100)}
            large_preview_data.append(row)

        large_dataset = {
            "id": 1,
            "project_id": 1,
            "status": "ready",
            "rows_count": 1000000,  # 1M rows
            "columns_count": 100,
            "preview_data": large_preview_data
        }

        mock_db_fetch_one.return_value = large_dataset
        mock_db_fetch_all.return_value = large_columns

        response = client.get("/datasets/1/preview")

        assert response.status_code == 200
        data = response.json()

        assert data["columns_count"] == 100
        assert data["rows_count"] == 1000000
        assert len(data["columns"]) == 100
        assert len(data["sample_data"]) == 100

    @patch('shared.database.Database.fetch_one')
    @patch('shared.database.Database.fetch_all')
    @patch('shared.auth.get_current_user')
    def test_many_quality_checks_handling(
        self,
        mock_get_user,
        mock_db_fetch_all,
        mock_db_fetch_one,
        client,
        mock_auth_user
    ):
        """Test handling of many quality check results"""
        mock_get_user.return_value = mock_auth_user

        # Mock dataset access
        mock_db_fetch_one.return_value = {"id": 1}

        # Create many quality checks
        many_checks = []
        for i in range(1000):  # 1000 quality issues
            check = {
                "id": i,
                "dataset_id": 1,
                "check_type": "missing_values",
                "column_name": f"col_{i}",
                "severity": "warning",
                "message": f"Column col_{i} has issues",
                "details": '{"count": 10}',
                "affected_rows": 10,
                "created_at": datetime.utcnow()
            }
            many_checks.append(check)

        mock_db_fetch_all.return_value = many_checks

        response = client.get("/datasets/1/quality")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1000
        # Response should be properly formatted despite large size