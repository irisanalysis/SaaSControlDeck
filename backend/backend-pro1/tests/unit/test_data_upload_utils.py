"""
Unit tests for data upload utility functions
Tests file validation, processing, and helper functions
"""

import pytest
import hashlib
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, mock_open, AsyncMock
from fastapi import HTTPException, UploadFile

from data_service.app.routers.data_upload import (
    get_file_type_from_filename,
    validate_file_upload,
    calculate_file_hash,
    MAX_FILE_SIZE,
    ALLOWED_TYPES,
    ALLOWED_MIME_TYPES
)


class TestFileTypeDetection:
    """Test file type detection from filename"""

    def test_get_file_type_csv(self):
        """Test CSV file type detection"""
        assert get_file_type_from_filename("data.csv") == "csv"
        assert get_file_type_from_filename("DATA.CSV") == "csv"
        assert get_file_type_from_filename("path/to/file.csv") == "csv"

    def test_get_file_type_json(self):
        """Test JSON file type detection"""
        assert get_file_type_from_filename("data.json") == "json"
        assert get_file_type_from_filename("DATA.JSON") == "json"
        assert get_file_type_from_filename("path/to/file.json") == "json"

    def test_get_file_type_excel(self):
        """Test Excel file type detection"""
        assert get_file_type_from_filename("data.xlsx") == "excel"
        assert get_file_type_from_filename("data.xls") == "excel"
        assert get_file_type_from_filename("DATA.XLSX") == "excel"
        assert get_file_type_from_filename("DATA.XLS") == "excel"

    def test_get_file_type_parquet(self):
        """Test Parquet file type detection"""
        assert get_file_type_from_filename("data.parquet") == "parquet"
        assert get_file_type_from_filename("DATA.PARQUET") == "parquet"

    def test_get_file_type_unsupported(self):
        """Test unsupported file types raise ValueError"""
        unsupported_files = [
            "data.txt",
            "data.pdf",
            "data.doc",
            "data.docx",
            "data.xml",
            "data.html",
            "file_without_extension"
        ]

        for filename in unsupported_files:
            with pytest.raises(ValueError, match="不支持的文件类型"):
                get_file_type_from_filename(filename)

    def test_get_file_type_edge_cases(self):
        """Test edge cases for file type detection"""
        # File with multiple dots
        assert get_file_type_from_filename("data.backup.csv") == "csv"

        # File with no extension should raise error
        with pytest.raises(ValueError):
            get_file_type_from_filename("filename_no_ext")

        # Empty filename should raise error
        with pytest.raises(ValueError):
            get_file_type_from_filename("")


class TestFileValidation:
    """Test file upload validation"""

    class MockUploadFile:
        """Mock UploadFile for testing"""
        def __init__(self, filename: str = None, content_type: str = None):
            self.filename = filename
            self.content_type = content_type

    def test_validate_file_upload_valid_files(self):
        """Test validation of valid files"""
        valid_files = [
            ("data.csv", "text/csv"),
            ("data.json", "application/json"),
            ("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("data.xls", "application/vnd.ms-excel"),
            ("data.parquet", "application/octet-stream"),
        ]

        for filename, content_type in valid_files:
            file = self.MockUploadFile(filename=filename, content_type=content_type)
            # Should not raise exception
            validate_file_upload(file)

    def test_validate_file_upload_empty_filename(self):
        """Test validation fails for empty filename"""
        file = self.MockUploadFile(filename=None)

        with pytest.raises(HTTPException) as exc_info:
            validate_file_upload(file)

        assert exc_info.value.status_code == 400
        assert "文件名不能为空" in str(exc_info.value.detail)

        # Test empty string filename
        file = self.MockUploadFile(filename="")

        with pytest.raises(HTTPException) as exc_info:
            validate_file_upload(file)

        assert exc_info.value.status_code == 400

    def test_validate_file_upload_unsupported_extension(self):
        """Test validation fails for unsupported file extensions"""
        unsupported_files = [
            "data.txt",
            "data.pdf",
            "data.doc",
            "data.docx",
            "data.xml",
            "data.html"
        ]

        for filename in unsupported_files:
            file = self.MockUploadFile(filename=filename, content_type="text/plain")

            with pytest.raises(HTTPException) as exc_info:
                validate_file_upload(file)

            assert exc_info.value.status_code == 400
            assert "不支持的文件类型" in str(exc_info.value.detail)

    def test_validate_file_upload_case_insensitive(self):
        """Test validation is case insensitive"""
        case_variants = [
            "DATA.CSV",
            "data.CSV",
            "Data.Csv",
            "DATA.XLSX",
            "data.JSON"
        ]

        for filename in case_variants:
            file = self.MockUploadFile(filename=filename, content_type="text/csv")
            # Should not raise exception
            validate_file_upload(file)

    def test_validate_file_upload_mime_type_warning(self):
        """Test that invalid MIME types log warnings but don't fail validation"""
        file = self.MockUploadFile(
            filename="data.csv",
            content_type="invalid/mime-type"
        )

        # Should not raise exception, but would log a warning
        # We can't easily test logging in unit tests without additional setup
        validate_file_upload(file)

    def test_validate_file_upload_none_mime_type(self):
        """Test validation with None MIME type"""
        file = self.MockUploadFile(
            filename="data.csv",
            content_type=None
        )

        # Should not raise exception
        validate_file_upload(file)


class TestFileHashCalculation:
    """Test file hash calculation"""

    @pytest.mark.asyncio
    async def test_calculate_file_hash_simple(self, temp_upload_dir):
        """Test hash calculation for a simple file"""
        # Create a test file
        test_content = b"Hello, World!"
        test_file = temp_upload_dir / "test.txt"

        with open(test_file, "wb") as f:
            f.write(test_content)

        # Calculate hash
        calculated_hash = await calculate_file_hash(test_file)

        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert calculated_hash == expected_hash

    @pytest.mark.asyncio
    async def test_calculate_file_hash_empty_file(self, temp_upload_dir):
        """Test hash calculation for empty file"""
        test_file = temp_upload_dir / "empty.txt"
        test_file.touch()  # Create empty file

        calculated_hash = await calculate_file_hash(test_file)
        expected_hash = hashlib.sha256(b"").hexdigest()

        assert calculated_hash == expected_hash

    @pytest.mark.asyncio
    async def test_calculate_file_hash_large_file(self, temp_upload_dir):
        """Test hash calculation for larger file (chunked reading)"""
        # Create a larger test file
        test_content = b"A" * 10000  # 10KB of 'A' characters
        test_file = temp_upload_dir / "large.txt"

        with open(test_file, "wb") as f:
            f.write(test_content)

        calculated_hash = await calculate_file_hash(test_file)
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert calculated_hash == expected_hash

    @pytest.mark.asyncio
    async def test_calculate_file_hash_nonexistent_file(self, temp_upload_dir):
        """Test hash calculation for non-existent file"""
        nonexistent_file = temp_upload_dir / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            await calculate_file_hash(nonexistent_file)

    @pytest.mark.asyncio
    async def test_calculate_file_hash_binary_content(self, temp_upload_dir):
        """Test hash calculation for binary content"""
        # Create binary content (simulating a CSV file)
        binary_content = bytes([i % 256 for i in range(1000)])
        test_file = temp_upload_dir / "binary.dat"

        with open(test_file, "wb") as f:
            f.write(binary_content)

        calculated_hash = await calculate_file_hash(test_file)
        expected_hash = hashlib.sha256(binary_content).hexdigest()

        assert calculated_hash == expected_hash


class TestConstants:
    """Test configuration constants"""

    def test_max_file_size(self):
        """Test MAX_FILE_SIZE constant"""
        assert MAX_FILE_SIZE == 100 * 1024 * 1024  # 100MB
        assert isinstance(MAX_FILE_SIZE, int)

    def test_allowed_types(self):
        """Test ALLOWED_TYPES constant"""
        expected_types = {'csv', 'json', 'xlsx', 'xls', 'parquet'}
        assert ALLOWED_TYPES == expected_types
        assert isinstance(ALLOWED_TYPES, set)

    def test_allowed_mime_types(self):
        """Test ALLOWED_MIME_TYPES constant"""
        expected_mime_types = {
            'text/csv',
            'application/json',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/octet-stream'
        }
        assert ALLOWED_MIME_TYPES == expected_mime_types
        assert isinstance(ALLOWED_MIME_TYPES, set)


class TestUploadDirectoryHandling:
    """Test upload directory creation and handling"""

    def test_upload_dir_creation(self):
        """Test that UPLOAD_DIR is created"""
        # This is implicitly tested by the import, but we can verify the pattern
        from data_service.app.routers.data_upload import UPLOAD_DIR

        # UPLOAD_DIR should be a Path object
        assert isinstance(UPLOAD_DIR, Path)
        assert UPLOAD_DIR.name == "data_uploads"

    @patch('tempfile.gettempdir')
    def test_upload_dir_uses_temp_directory(self, mock_gettempdir):
        """Test that upload directory uses system temp directory"""
        mock_gettempdir.return_value = "/custom/temp"

        # Re-import to trigger path creation with mocked temp dir
        import importlib
        from data_service.app.routers import data_upload
        importlib.reload(data_upload)

        expected_path = Path("/custom/temp") / "data_uploads"
        assert str(data_upload.UPLOAD_DIR) == str(expected_path)


class TestFileValidationEdgeCases:
    """Test edge cases for file validation"""

    class MockUploadFile:
        def __init__(self, filename=None, content_type=None):
            self.filename = filename
            self.content_type = content_type

    def test_filename_with_spaces(self):
        """Test filename with spaces is handled correctly"""
        file = self.MockUploadFile(
            filename="my data file.csv",
            content_type="text/csv"
        )
        # Should not raise exception
        validate_file_upload(file)

    def test_filename_with_special_characters(self):
        """Test filename with special characters"""
        special_filenames = [
            "data-file.csv",
            "data_file.csv",
            "data.file.csv",
            "data(1).csv",
            "数据文件.csv",  # Chinese characters
        ]

        for filename in special_filenames:
            file = self.MockUploadFile(
                filename=filename,
                content_type="text/csv"
            )
            # Should not raise exception
            validate_file_upload(file)

    def test_very_long_filename(self):
        """Test very long filename is handled"""
        long_filename = "a" * 200 + ".csv"  # Very long filename
        file = self.MockUploadFile(
            filename=long_filename,
            content_type="text/csv"
        )
        # Should not raise exception for valid extension
        validate_file_upload(file)

    def test_filename_with_path_traversal_attempt(self):
        """Test filename with path traversal attempts"""
        # These should still validate based on extension, not path
        traversal_filenames = [
            "../data.csv",
            "../../data.csv",
            "/absolute/path/data.csv",
            "path\\to\\data.csv",  # Windows-style path
        ]

        for filename in traversal_filenames:
            file = self.MockUploadFile(
                filename=filename,
                content_type="text/csv"
            )
            # Should not raise exception - validation only checks extension
            validate_file_upload(file)


class TestFileProcessingHelpers:
    """Test file processing helper functions"""

    def test_file_extension_extraction(self):
        """Test various file extension extraction scenarios"""
        test_cases = [
            ("file.csv", ".csv"),
            ("FILE.CSV", ".csv"),  # Case conversion
            ("path/to/file.json", ".json"),
            ("file.name.xlsx", ".xlsx"),  # Multiple dots
            ("file.", "."),  # Edge case: dot at end
        ]

        for filename, expected_ext in test_cases:
            ext = Path(filename).suffix.lower()
            assert ext == expected_ext

    def test_mime_type_checking(self):
        """Test MIME type validation logic"""
        # Test that all expected MIME types are in the allowed set
        valid_mime_types = [
            "text/csv",
            "application/json",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream"
        ]

        for mime_type in valid_mime_types:
            assert mime_type in ALLOWED_MIME_TYPES

        # Test invalid MIME types
        invalid_mime_types = [
            "text/plain",
            "application/pdf",
            "image/jpeg",
            "video/mp4"
        ]

        for mime_type in invalid_mime_types:
            assert mime_type not in ALLOWED_MIME_TYPES