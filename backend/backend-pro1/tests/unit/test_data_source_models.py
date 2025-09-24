"""
Unit tests for data source Pydantic models
Tests validation, serialization, and business logic
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from pydantic import ValidationError

from shared.models.data_source import (
    DataSourceType, DataSourceStatus, UploadSessionStatus, DataQualitySeverity,
    ColumnInfo, DataSourceMetadata, DataSourceBase, DataSourceCreate,
    DataSourceUpdate, UploadSessionCreate, UploadSession, DataSource,
    DataSourcePreview, DataQualityCheck, FileUploadResponse,
    ChunkUploadResponse, DataSourceAnalytics
)


class TestDataSourceEnums:
    """Test enum classes for data sources"""

    def test_data_source_type_enum(self):
        """Test DataSourceType enum values"""
        assert DataSourceType.CSV == "csv"
        assert DataSourceType.JSON == "json"
        assert DataSourceType.EXCEL == "excel"
        assert DataSourceType.PARQUET == "parquet"

    def test_data_source_status_enum(self):
        """Test DataSourceStatus enum values"""
        assert DataSourceStatus.UPLOADING == "uploading"
        assert DataSourceStatus.PROCESSING == "processing"
        assert DataSourceStatus.READY == "ready"
        assert DataSourceStatus.ERROR == "error"

    def test_upload_session_status_enum(self):
        """Test UploadSessionStatus enum values"""
        assert UploadSessionStatus.UPLOADING == "uploading"
        assert UploadSessionStatus.PROCESSING == "processing"
        assert UploadSessionStatus.COMPLETED == "completed"
        assert UploadSessionStatus.FAILED == "failed"
        assert UploadSessionStatus.CANCELLED == "cancelled"

    def test_data_quality_severity_enum(self):
        """Test DataQualitySeverity enum values"""
        assert DataQualitySeverity.INFO == "info"
        assert DataQualitySeverity.WARNING == "warning"
        assert DataQualitySeverity.ERROR == "error"
        assert DataQualitySeverity.CRITICAL == "critical"


class TestColumnInfo:
    """Test ColumnInfo model"""

    def test_column_info_creation_minimal(self):
        """Test creating ColumnInfo with minimal required fields"""
        column = ColumnInfo(
            column_name="test_column",
            column_index=0,
            data_type="string"
        )

        assert column.column_name == "test_column"
        assert column.column_index == 0
        assert column.data_type == "string"
        assert column.is_nullable is True  # Default value
        assert column.unique_count == 0    # Default value
        assert column.missing_count == 0   # Default value
        assert column.sample_values == []  # Default value

    def test_column_info_creation_complete(self):
        """Test creating ColumnInfo with all fields"""
        column = ColumnInfo(
            column_name="age",
            column_index=2,
            data_type="number",
            is_nullable=False,
            unique_count=50,
            missing_count=5,
            min_value="18",
            max_value="65",
            avg_value=35.5,
            std_value=12.3,
            sample_values=["25", "30", "35", "40", "45"]
        )

        assert column.column_name == "age"
        assert column.data_type == "number"
        assert column.is_nullable is False
        assert column.unique_count == 50
        assert column.missing_count == 5
        assert column.avg_value == 35.5
        assert len(column.sample_values) == 5

    def test_column_info_validation_required_fields(self):
        """Test validation of required fields"""
        with pytest.raises(ValidationError) as exc_info:
            ColumnInfo(column_index=0, data_type="string")  # Missing column_name

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("column_name",) for error in errors)

    def test_column_info_data_types(self):
        """Test different data types"""
        valid_types = ["string", "number", "date", "boolean", "null"]

        for data_type in valid_types:
            column = ColumnInfo(
                column_name=f"test_{data_type}",
                column_index=0,
                data_type=data_type
            )
            assert column.data_type == data_type


class TestDataSourceMetadata:
    """Test DataSourceMetadata model"""

    def test_metadata_defaults(self):
        """Test default values for metadata"""
        metadata = DataSourceMetadata()

        assert metadata.encoding == "utf-8"
        assert metadata.delimiter is None
        assert metadata.has_header is True
        assert metadata.columns == []
        assert metadata.data_types == {}
        assert metadata.sample_data == []
        assert metadata.missing_values_count == 0

    def test_metadata_with_columns(self):
        """Test metadata with column information"""
        columns = [
            ColumnInfo(column_name="id", column_index=0, data_type="number"),
            ColumnInfo(column_name="name", column_index=1, data_type="string")
        ]

        metadata = DataSourceMetadata(
            encoding="utf-8",
            delimiter=",",
            has_header=True,
            columns=columns,
            data_types={"id": "int64", "name": "object"},
            missing_values_count=10
        )

        assert metadata.encoding == "utf-8"
        assert metadata.delimiter == ","
        assert len(metadata.columns) == 2
        assert metadata.data_types["id"] == "int64"
        assert metadata.missing_values_count == 10


class TestDataSourceCreate:
    """Test DataSourceCreate model"""

    def test_data_source_create_valid(self):
        """Test valid data source creation"""
        data_source = DataSourceCreate(
            name="Test Dataset",
            type=DataSourceType.CSV,
            project_id=1,
            description="A test dataset"
        )

        assert data_source.name == "Test Dataset"
        assert data_source.type == DataSourceType.CSV
        assert data_source.project_id == 1
        assert data_source.description == "A test dataset"

    def test_data_source_create_name_validation(self):
        """Test name validation"""
        # Valid name
        data_source = DataSourceCreate(
            name="Valid Name",
            type=DataSourceType.CSV,
            project_id=1
        )
        assert data_source.name == "Valid Name"

        # Empty name should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DataSourceCreate(
                name="",
                type=DataSourceType.CSV,
                project_id=1
            )

        errors = exc_info.value.errors()
        assert any("数据源名称不能为空" in str(error["msg"]) for error in errors)

        # Whitespace-only name should be trimmed and raise error
        with pytest.raises(ValidationError) as exc_info:
            DataSourceCreate(
                name="   ",
                type=DataSourceType.CSV,
                project_id=1
            )

    def test_data_source_create_name_trimming(self):
        """Test automatic name trimming"""
        data_source = DataSourceCreate(
            name="  Trimmed Name  ",
            type=DataSourceType.CSV,
            project_id=1
        )
        assert data_source.name == "Trimmed Name"

    def test_data_source_create_required_fields(self):
        """Test validation of required fields"""
        # Missing name
        with pytest.raises(ValidationError):
            DataSourceCreate(
                type=DataSourceType.CSV,
                project_id=1
            )

        # Missing type
        with pytest.raises(ValidationError):
            DataSourceCreate(
                name="Test",
                project_id=1
            )

        # Missing project_id
        with pytest.raises(ValidationError):
            DataSourceCreate(
                name="Test",
                type=DataSourceType.CSV
            )

    def test_data_source_create_field_lengths(self):
        """Test field length validation"""
        # Valid lengths
        data_source = DataSourceCreate(
            name="a" * 200,  # Max length
            type=DataSourceType.CSV,
            project_id=1,
            description="a" * 1000  # Max length
        )
        assert len(data_source.name) == 200
        assert len(data_source.description) == 1000

        # Name too long
        with pytest.raises(ValidationError):
            DataSourceCreate(
                name="a" * 201,  # Over max length
                type=DataSourceType.CSV,
                project_id=1
            )

        # Description too long
        with pytest.raises(ValidationError):
            DataSourceCreate(
                name="Test",
                type=DataSourceType.CSV,
                project_id=1,
                description="a" * 1001  # Over max length
            )


class TestUploadSessionCreate:
    """Test UploadSessionCreate model"""

    def test_upload_session_create_valid(self):
        """Test valid upload session creation"""
        session = UploadSessionCreate(
            filename="test.csv",
            file_size=1024,
            project_id=1,
            chunk_size=512
        )

        assert session.filename == "test.csv"
        assert session.file_size == 1024
        assert session.project_id == 1
        assert session.chunk_size == 512

    def test_upload_session_create_defaults(self):
        """Test default values"""
        session = UploadSessionCreate(
            filename="test.csv",
            file_size=1024,
            project_id=1
        )

        assert session.chunk_size == 1048576  # Default 1MB

    def test_filename_validation(self):
        """Test filename validation"""
        # Valid filenames
        valid_filenames = [
            "data.csv",
            "dataset.json",
            "report.xlsx",
            "analysis.xls",
            "bigdata.parquet"
        ]

        for filename in valid_filenames:
            session = UploadSessionCreate(
                filename=filename,
                file_size=1024,
                project_id=1
            )
            assert session.filename == filename

        # Invalid filenames
        invalid_filenames = [
            "",           # Empty
            "   ",        # Whitespace only
            "file.txt",   # Unsupported extension
            "file.pdf",   # Unsupported extension
            "file.doc",   # Unsupported extension
        ]

        for filename in invalid_filenames:
            with pytest.raises(ValidationError):
                UploadSessionCreate(
                    filename=filename,
                    file_size=1024,
                    project_id=1
                )

    def test_file_size_validation(self):
        """Test file size validation"""
        # Valid file size
        session = UploadSessionCreate(
            filename="test.csv",
            file_size=1024,
            project_id=1
        )
        assert session.file_size == 1024

        # Invalid file size (must be greater than 0)
        with pytest.raises(ValidationError):
            UploadSessionCreate(
                filename="test.csv",
                file_size=0,
                project_id=1
            )

        with pytest.raises(ValidationError):
            UploadSessionCreate(
                filename="test.csv",
                file_size=-100,
                project_id=1
            )

    def test_chunk_size_validation(self):
        """Test chunk size validation"""
        # Valid chunk size
        session = UploadSessionCreate(
            filename="test.csv",
            file_size=1024,
            project_id=1,
            chunk_size=512
        )
        assert session.chunk_size == 512

        # Invalid chunk size (must be greater than 0)
        with pytest.raises(ValidationError):
            UploadSessionCreate(
                filename="test.csv",
                file_size=1024,
                project_id=1,
                chunk_size=0
            )


class TestUploadSession:
    """Test UploadSession model"""

    def test_upload_session_creation(self):
        """Test upload session creation with all fields"""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)

        session = UploadSession(
            id="session-123",
            user_id=1,
            project_id=1,
            filename="test.csv",
            file_size=1024,
            uploaded_size=512,
            chunk_size=256,
            total_chunks=4,
            uploaded_chunks=2,
            status=UploadSessionStatus.UPLOADING,
            dataset_id=None,
            error_message=None,
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )

        assert session.id == "session-123"
        assert session.file_size == 1024
        assert session.uploaded_size == 512
        assert session.total_chunks == 4
        assert session.uploaded_chunks == 2

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation"""
        # No chunks uploaded
        session = UploadSession(
            id="session-123",
            user_id=1,
            project_id=1,
            filename="test.csv",
            file_size=1024,
            chunk_size=256,
            total_chunks=4,
            uploaded_chunks=0,
            status=UploadSessionStatus.UPLOADING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        assert session.progress_percentage == 0.0

        # Half uploaded
        session.uploaded_chunks = 2
        assert session.progress_percentage == 50.0

        # Fully uploaded
        session.uploaded_chunks = 4
        assert session.progress_percentage == 100.0

        # Edge case: no total chunks
        session.total_chunks = 0
        assert session.progress_percentage == 0.0


class TestDataSource:
    """Test DataSource model"""

    def test_data_source_creation(self):
        """Test complete data source creation"""
        now = datetime.utcnow()
        processing_start = now - timedelta(minutes=5)
        processing_end = now

        data_source = DataSource(
            id=1,
            project_id=1,
            name="Test Dataset",
            type=DataSourceType.CSV,
            file_path="/tmp/test.csv",
            file_size=1024,
            rows_count=100,
            columns_count=5,
            status=DataSourceStatus.READY,
            file_hash="abc123",
            original_filename="test.csv",
            mime_type="text/csv",
            encoding="utf-8",
            delimiter=",",
            has_header=True,
            created_at=now,
            updated_at=now,
            processing_started_at=processing_start,
            processing_completed_at=processing_end
        )

        assert data_source.id == 1
        assert data_source.name == "Test Dataset"
        assert data_source.type == DataSourceType.CSV
        assert data_source.status == DataSourceStatus.READY
        assert data_source.rows_count == 100
        assert data_source.columns_count == 5

    def test_processing_duration_calculation(self):
        """Test processing duration calculation"""
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=5)
        end_time = now

        # With both times set
        data_source = DataSource(
            id=1,
            project_id=1,
            name="Test",
            type=DataSourceType.CSV,
            status=DataSourceStatus.READY,
            created_at=now,
            updated_at=now,
            processing_started_at=start_time,
            processing_completed_at=end_time
        )

        duration = data_source.processing_duration
        assert duration is not None
        assert abs(duration - 300.0) < 1.0  # ~5 minutes (300 seconds)

        # With missing start time
        data_source.processing_started_at = None
        assert data_source.processing_duration is None

        # With missing end time
        data_source.processing_started_at = start_time
        data_source.processing_completed_at = None
        assert data_source.processing_duration is None


class TestResponseModels:
    """Test response models"""

    def test_file_upload_response(self):
        """Test FileUploadResponse model"""
        response = FileUploadResponse(
            success=True,
            session_id="session-123",
            dataset_id=1,
            message="Upload successful",
            upload_url="https://example.com/upload"
        )

        assert response.success is True
        assert response.session_id == "session-123"
        assert response.dataset_id == 1
        assert response.message == "Upload successful"

    def test_chunk_upload_response(self):
        """Test ChunkUploadResponse model"""
        response = ChunkUploadResponse(
            success=True,
            chunk_index=2,
            uploaded_chunks=3,
            total_chunks=5,
            progress_percentage=60.0,
            is_complete=False,
            message="Chunk uploaded"
        )

        assert response.success is True
        assert response.chunk_index == 2
        assert response.uploaded_chunks == 3
        assert response.total_chunks == 5
        assert response.progress_percentage == 60.0
        assert response.is_complete is False

    def test_data_source_analytics(self):
        """Test DataSourceAnalytics model"""
        analytics = DataSourceAnalytics(
            total_datasets=100,
            datasets_by_type={"csv": 60, "json": 30, "excel": 10},
            datasets_by_status={"ready": 90, "processing": 5, "error": 5},
            total_size=1024000,
            total_rows=50000,
            recent_uploads=[],
            quality_issues=15
        )

        assert analytics.total_datasets == 100
        assert analytics.datasets_by_type["csv"] == 60
        assert analytics.datasets_by_status["ready"] == 90
        assert analytics.total_size == 1024000
        assert analytics.quality_issues == 15


class TestDataQualityCheck:
    """Test DataQualityCheck model"""

    def test_data_quality_check_creation(self):
        """Test data quality check creation"""
        check = DataQualityCheck(
            id=1,
            dataset_id=1,
            check_type="missing_values",
            column_name="age",
            severity=DataQualitySeverity.WARNING,
            message="Column has missing values",
            details={"missing_count": 10, "missing_percentage": 10.0},
            affected_rows=10,
            created_at=datetime.utcnow()
        )

        assert check.id == 1
        assert check.dataset_id == 1
        assert check.check_type == "missing_values"
        assert check.column_name == "age"
        assert check.severity == DataQualitySeverity.WARNING
        assert check.affected_rows == 10
        assert check.details["missing_count"] == 10


class TestDataSourcePreview:
    """Test DataSourcePreview model"""

    def test_data_source_preview_creation(self):
        """Test data source preview creation"""
        columns = [
            ColumnInfo(column_name="id", column_index=0, data_type="number"),
            ColumnInfo(column_name="name", column_index=1, data_type="string")
        ]

        preview = DataSourcePreview(
            dataset_id=1,
            rows_count=1000,
            columns_count=2,
            columns=columns,
            sample_data=[{"id": 1, "name": "Test"}],
            data_types={"id": "int64", "name": "object"},
            missing_values_summary={"id": 0, "name": 5},
            memory_usage=1024
        )

        assert preview.dataset_id == 1
        assert preview.rows_count == 1000
        assert preview.columns_count == 2
        assert len(preview.columns) == 2
        assert len(preview.sample_data) == 1
        assert preview.data_types["id"] == "int64"
        assert preview.missing_values_summary["name"] == 5


class TestModelSerialization:
    """Test model serialization and deserialization"""

    def test_data_source_serialization(self):
        """Test DataSource model serialization"""
        now = datetime.utcnow()

        data_source = DataSource(
            id=1,
            project_id=1,
            name="Test Dataset",
            type=DataSourceType.CSV,
            status=DataSourceStatus.READY,
            created_at=now,
            updated_at=now
        )

        # Test dict conversion
        data_dict = data_source.model_dump()
        assert data_dict["id"] == 1
        assert data_dict["name"] == "Test Dataset"
        assert data_dict["type"] == "csv"
        assert data_dict["status"] == "ready"

        # Test JSON serialization
        json_str = data_source.model_dump_json()
        assert "Test Dataset" in json_str
        assert '"type":"csv"' in json_str

    def test_upload_session_serialization(self):
        """Test UploadSession model serialization"""
        now = datetime.utcnow()

        session = UploadSession(
            id="session-123",
            user_id=1,
            project_id=1,
            filename="test.csv",
            file_size=1024,
            chunk_size=512,
            total_chunks=2,
            status=UploadSessionStatus.UPLOADING,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=24)
        )

        data_dict = session.model_dump()
        assert data_dict["id"] == "session-123"
        assert data_dict["filename"] == "test.csv"
        assert data_dict["status"] == "uploading"
        assert data_dict["progress_percentage"] == 0.0  # Computed property