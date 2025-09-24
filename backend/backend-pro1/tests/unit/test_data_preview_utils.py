"""
Unit tests for data preview and analysis utilities
Tests data type detection, column statistics, and quality analysis
RELEVANT FILES: data_preview.py, data_source.py, conftest.py, test_data_source_models.py
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from data_service.app.routers.data_preview import (
    detect_data_type, get_column_statistics, load_dataframe_from_file,
    analyze_data_quality, PREVIEW_ROWS, MAX_SAMPLE_VALUES
)
from shared.models.data_source import DataQualitySeverity


class TestDataTypeDetection:
    """Test data type detection functionality"""

    def test_detect_number_type(self):
        """Test numeric data type detection"""
        # Integer series
        int_series = pd.Series([1, 2, 3, 4, 5])
        assert detect_data_type(int_series) == "number"

        # Float series
        float_series = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5])
        assert detect_data_type(float_series) == "number"

        # Mixed numeric
        mixed_numeric = pd.Series([1, 2.5, 3, 4.0, 5])
        assert detect_data_type(mixed_numeric) == "number"

        # Numeric strings (80%+ parseable as numbers)
        numeric_strings = pd.Series(['1', '2', '3', '4', '5', '6.5', '7.8', '8', '9', 'not_a_number'])
        assert detect_data_type(numeric_strings) == "number"

    def test_detect_string_type(self):
        """Test string data type detection"""
        # Regular strings
        string_series = pd.Series(['apple', 'banana', 'cherry', 'date'])
        assert detect_data_type(string_series) == "string"

        # Mixed strings and numbers (but <80% numeric)
        mixed_series = pd.Series(['apple', 'banana', '1', '2', 'cherry'])
        assert detect_data_type(mixed_series) == "string"

        # Empty strings
        empty_series = pd.Series(['', '  ', 'text', ''])
        assert detect_data_type(empty_series) == "string"

    def test_detect_boolean_type(self):
        """Test boolean data type detection"""
        bool_series = pd.Series([True, False, True, False])
        assert detect_data_type(bool_series) == "boolean"

        # Boolean with some nulls
        bool_with_nulls = pd.Series([True, False, None, True])
        assert detect_data_type(bool_with_nulls) == "boolean"

    def test_detect_date_type(self):
        """Test date/datetime data type detection"""
        # Datetime series
        date_series = pd.Series([datetime.now(), datetime.now() + timedelta(days=1)])
        assert detect_data_type(date_series) == "date"

        # Date strings (80%+ parseable as dates)
        date_strings = pd.Series([
            '2023-01-01', '2023-02-15', '2023-03-20', '2023-04-10',
            '2023-05-05', '2023-06-12', '2023-07-01', '2023-08-15',
            '2023-09-30', 'not_a_date'
        ])
        assert detect_data_type(date_strings) == "date"

        # ISO format dates
        iso_dates = pd.Series(['2023-01-01T10:30:00', '2023-02-15T14:45:30'])
        assert detect_data_type(iso_dates) == "date"

    def test_detect_null_type(self):
        """Test null data type detection"""
        null_series = pd.Series([None, None, None, None])
        assert detect_data_type(null_series) == "null"

        # All NaN
        nan_series = pd.Series([np.nan, np.nan, np.nan])
        assert detect_data_type(nan_series) == "null"

    def test_detect_type_with_nulls(self):
        """Test data type detection with null values"""
        # Numbers with nulls
        numeric_with_nulls = pd.Series([1, 2, None, 4, 5])
        assert detect_data_type(numeric_with_nulls) == "number"

        # Strings with nulls
        string_with_nulls = pd.Series(['apple', None, 'cherry', None])
        assert detect_data_type(string_with_nulls) == "string"

        # Dates with nulls
        date_with_nulls = pd.Series(['2023-01-01', None, '2023-03-01'])
        assert detect_data_type(date_with_nulls) == "date"

    def test_detect_type_edge_cases(self):
        """Test edge cases in data type detection"""
        # Empty series
        empty_series = pd.Series([])
        result = detect_data_type(empty_series)
        assert result in ["string", "null"]  # Could be either

        # Single value
        single_value = pd.Series([42])
        assert detect_data_type(single_value) == "number"

        # Mixed types with low confidence
        mixed_low_confidence = pd.Series(['text', '1', 'more_text', '2', 'even_more_text'])
        assert detect_data_type(mixed_low_confidence) == "string"


class TestColumnStatistics:
    """Test column statistics calculation"""

    def test_numeric_column_statistics(self):
        """Test statistics for numeric columns"""
        numeric_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        stats = get_column_statistics(numeric_data, "test_column", 0)

        assert stats.column_name == "test_column"
        assert stats.column_index == 0
        assert stats.data_type == "number"
        assert stats.is_nullable is False
        assert stats.unique_count == 10
        assert stats.missing_count == 0
        assert stats.min_value == "1"
        assert stats.max_value == "10"
        assert stats.avg_value == 5.5
        assert stats.std_value == pytest.approx(3.02765, rel=1e-4)
        assert len(stats.sample_values) <= MAX_SAMPLE_VALUES

    def test_string_column_statistics(self):
        """Test statistics for string columns"""
        string_data = pd.Series(['apple', 'banana', 'cherry', 'date', 'elderberry'])
        stats = get_column_statistics(string_data, "fruit_column", 1)

        assert stats.column_name == "fruit_column"
        assert stats.column_index == 1
        assert stats.data_type == "string"
        assert stats.is_nullable is False
        assert stats.unique_count == 5
        assert stats.missing_count == 0
        # For strings, min/max refer to length
        assert stats.min_value == "4"  # 'date' length
        assert stats.max_value == "10"  # 'elderberry' length
        assert stats.avg_value == pytest.approx(6.0, rel=1e-2)

    def test_date_column_statistics(self):
        """Test statistics for date columns"""
        dates = ['2023-01-01', '2023-02-15', '2023-03-30', '2023-04-10']
        date_data = pd.Series(dates)
        stats = get_column_statistics(date_data, "date_column", 2)

        assert stats.column_name == "date_column"
        assert stats.column_index == 2
        assert stats.data_type == "date"
        assert stats.min_value is not None
        assert stats.max_value is not None
        # avg_value and std_value should be None for dates
        assert stats.avg_value is None
        assert stats.std_value is None

    def test_boolean_column_statistics(self):
        """Test statistics for boolean columns"""
        bool_data = pd.Series([True, False, True, True, False])
        stats = get_column_statistics(bool_data, "bool_column", 3)

        assert stats.column_name == "bool_column"
        assert stats.column_index == 3
        assert stats.data_type == "boolean"
        assert stats.unique_count == 2
        assert stats.missing_count == 0

    def test_column_with_nulls(self):
        """Test statistics for columns with null values"""
        data_with_nulls = pd.Series([1, 2, None, 4, None, 6])
        stats = get_column_statistics(data_with_nulls, "nullable_column", 4)

        assert stats.is_nullable is True
        assert stats.missing_count == 2
        assert stats.unique_count == 4  # 1, 2, 4, 6 (excluding nulls)

    def test_empty_column(self):
        """Test statistics for empty columns"""
        empty_data = pd.Series([])
        stats = get_column_statistics(empty_data, "empty_column", 5)

        assert stats.missing_count == 0
        assert stats.unique_count == 0
        assert stats.sample_values == []

    def test_all_null_column(self):
        """Test statistics for columns with all null values"""
        all_null_data = pd.Series([None, None, None])
        stats = get_column_statistics(all_null_data, "null_column", 6)

        assert stats.data_type == "null"
        assert stats.is_nullable is True
        assert stats.missing_count == 3
        assert stats.unique_count == 0

    def test_sample_values_limit(self):
        """Test that sample values are limited correctly"""
        large_series = pd.Series(range(1000))  # 1000 unique values
        stats = get_column_statistics(large_series, "large_column", 7)

        assert len(stats.sample_values) <= MAX_SAMPLE_VALUES
        # All sample values should be valid
        for value in stats.sample_values:
            assert value.isdigit()


class TestDataFrameLoading:
    """Test DataFrame loading from different file formats"""

    def test_load_csv_file(self, sample_csv_file):
        """Test loading CSV files"""
        df = load_dataframe_from_file(str(sample_csv_file), 'csv')

        assert not df.empty
        assert len(df.columns) > 0
        assert 'id' in df.columns
        assert 'name' in df.columns
        assert len(df) <= PREVIEW_ROWS * 10

    def test_load_json_file(self, sample_json_file):
        """Test loading JSON files"""
        df = load_dataframe_from_file(str(sample_json_file), 'json')

        assert not df.empty
        assert len(df.columns) > 0
        assert 'id' in df.columns

    def test_load_excel_file(self, sample_excel_file):
        """Test loading Excel files"""
        df = load_dataframe_from_file(str(sample_excel_file), 'excel')

        assert not df.empty
        assert len(df.columns) > 0
        assert 'Product' in df.columns

    def test_load_unsupported_file_type(self, temp_upload_dir):
        """Test loading unsupported file types raises error"""
        invalid_file = temp_upload_dir / "test.txt"
        invalid_file.write_text("This is not supported")

        with pytest.raises(Exception):
            load_dataframe_from_file(str(invalid_file), 'txt')

    def test_load_corrupted_file(self, temp_upload_dir):
        """Test loading corrupted files raises error"""
        corrupted_csv = temp_upload_dir / "corrupted.csv"
        corrupted_csv.write_bytes(b'\x00\x01\x02\x03')  # Binary garbage

        with pytest.raises(Exception):
            load_dataframe_from_file(str(corrupted_csv), 'csv')

    def test_load_empty_file(self, empty_file):
        """Test loading empty files"""
        with pytest.raises(Exception):
            load_dataframe_from_file(str(empty_file), 'csv')

    @patch('pandas.read_csv')
    def test_csv_encoding_fallback(self, mock_read_csv, temp_upload_dir):
        """Test CSV encoding fallback mechanism"""
        test_file = temp_upload_dir / "encoding_test.csv"
        test_file.write_text("id,name\n1,test")

        # Simulate encoding errors for first attempts
        mock_read_csv.side_effect = [
            UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte'),  # utf-8 fails
            UnicodeDecodeError('gbk', b'', 0, 1, 'invalid start byte'),    # gbk fails
            pd.DataFrame({'id': [1], 'name': ['test']})  # gb2312 succeeds
        ]

        df = load_dataframe_from_file(str(test_file), 'csv')
        assert not df.empty
        assert mock_read_csv.call_count >= 3


class TestDataQualityAnalysis:
    """Test data quality analysis functionality"""

    @pytest.mark.asyncio
    async def test_missing_values_analysis(self):
        """Test missing values quality check"""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['a', 'b', 'c', None, None],
            'col3': [1.0, 2.0, 3.0, 4.0, 5.0]  # No missing values
        })

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should have checks for col1 and col2 (missing values)
        missing_checks = [check for check in quality_checks if check['check_type'] == 'missing_values']
        assert len(missing_checks) == 2

        # Check col1 (20% missing - WARNING)
        col1_check = next(check for check in missing_checks if check['column_name'] == 'col1')
        assert col1_check['severity'] == DataQualitySeverity.WARNING.value
        assert col1_check['affected_rows'] == 1
        assert col1_check['details']['percentage'] == 20.0

        # Check col2 (40% missing - ERROR)
        col2_check = next(check for check in missing_checks if check['column_name'] == 'col2')
        assert col2_check['severity'] == DataQualitySeverity.ERROR.value
        assert col2_check['affected_rows'] == 2
        assert col2_check['details']['percentage'] == 40.0

    @pytest.mark.asyncio
    async def test_duplicate_rows_analysis(self):
        """Test duplicate rows quality check"""
        df = pd.DataFrame({
            'col1': [1, 2, 1, 3, 2],  # Duplicates: rows 0&2, rows 1&4
            'col2': ['a', 'b', 'a', 'c', 'b']
        })

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should have duplicate check
        duplicate_checks = [check for check in quality_checks if check['check_type'] == 'duplicates']
        assert len(duplicate_checks) == 1

        duplicate_check = duplicate_checks[0]
        assert duplicate_check['affected_rows'] == 2  # 2 duplicate rows
        assert duplicate_check['details']['duplicate_count'] == 2
        assert duplicate_check['details']['percentage'] == 40.0  # 2/5 = 40%

    @pytest.mark.asyncio
    async def test_outliers_analysis(self):
        """Test outliers detection for numeric columns"""
        # Create data with clear outliers
        normal_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        outliers = [100, -100]  # Clear outliers
        df = pd.DataFrame({'numeric_col': normal_data + outliers})

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should have outlier check
        outlier_checks = [check for check in quality_checks if check['check_type'] == 'outliers']
        assert len(outlier_checks) == 1

        outlier_check = outlier_checks[0]
        assert outlier_check['column_name'] == 'numeric_col'
        assert outlier_check['affected_rows'] == 2  # Two outliers
        assert 'lower_bound' in outlier_check['details']
        assert 'upper_bound' in outlier_check['details']

    @pytest.mark.asyncio
    async def test_no_quality_issues(self):
        """Test analysis when no quality issues are found"""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should have no quality issues (or very minor ones)
        assert len(quality_checks) == 0

    @pytest.mark.asyncio
    async def test_quality_analysis_with_empty_dataframe(self):
        """Test quality analysis with empty DataFrame"""
        df = pd.DataFrame()

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        assert quality_checks == []

    @pytest.mark.asyncio
    async def test_severity_levels(self):
        """Test different severity levels based on missing value percentages"""
        test_cases = [
            (5, DataQualitySeverity.INFO),     # 5% missing
            (15, DataQualitySeverity.WARNING), # 15% missing
            (30, DataQualitySeverity.ERROR),   # 30% missing
            (70, DataQualitySeverity.CRITICAL) # 70% missing
        ]

        for missing_percentage, expected_severity in test_cases:
            total_rows = 100
            missing_count = missing_percentage

            # Create data with specific missing percentage
            data = [1] * (total_rows - missing_count) + [None] * missing_count
            df = pd.DataFrame({'test_col': data})

            quality_checks = await analyze_data_quality(df, dataset_id=1)

            missing_check = next(
                check for check in quality_checks
                if check['check_type'] == 'missing_values'
            )
            assert missing_check['severity'] == expected_severity.value

    @pytest.mark.asyncio
    async def test_quality_analysis_performance(self):
        """Test quality analysis performance with large dataset"""
        # Create a moderately large dataset
        size = 10000
        df = pd.DataFrame({
            'col1': range(size),
            'col2': ['text'] * size,
            'col3': [i % 100 for i in range(size)]  # Some repeated values
        })

        # Add some missing values
        df.loc[df.index % 100 == 0, 'col1'] = None  # 1% missing
        df.loc[df.index % 50 == 0, 'col2'] = None   # 2% missing

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should complete quickly and find appropriate issues
        assert len(quality_checks) >= 2  # At least missing value checks
        missing_checks = [check for check in quality_checks if check['check_type'] == 'missing_values']
        assert len(missing_checks) == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters"""
        unicode_data = pd.Series(['café', '北京', 'naïve', '🎉', ''])
        stats = get_column_statistics(unicode_data, "unicode_column", 0)

        assert stats.data_type == "string"
        assert stats.unique_count == 5
        assert len(stats.sample_values) <= MAX_SAMPLE_VALUES

    def test_very_long_strings(self):
        """Test handling of very long strings"""
        long_strings = pd.Series(['x' * 1000, 'y' * 2000, 'z' * 500])
        stats = get_column_statistics(long_strings, "long_string_column", 0)

        assert stats.data_type == "string"
        assert stats.min_value == "500"
        assert stats.max_value == "2000"

    def test_extreme_numeric_values(self):
        """Test handling of extreme numeric values"""
        extreme_values = pd.Series([
            -float('inf'), float('inf'), 0, 1e-10, 1e10,
            float('nan'), -1e-100, 1e100
        ])
        stats = get_column_statistics(extreme_values, "extreme_column", 0)

        # Should handle without crashing
        assert stats.column_name == "extreme_column"
        # Data type might be number or string depending on how pandas handles inf/nan

    def test_mixed_data_types_in_series(self):
        """Test handling of mixed data types in a single series"""
        mixed_data = pd.Series([1, '2', 3.0, '4.5', True, None, 'text'])
        stats = get_column_statistics(mixed_data, "mixed_column", 0)

        assert stats.column_name == "mixed_column"
        assert stats.missing_count == 1  # None value
        # Data type detection should handle this gracefully

    @pytest.mark.asyncio
    async def test_quality_analysis_with_all_null_columns(self):
        """Test quality analysis when some columns are all nulls"""
        df = pd.DataFrame({
            'good_col': [1, 2, 3, 4, 5],
            'all_null_col': [None, None, None, None, None],
            'another_good_col': ['a', 'b', 'c', 'd', 'e']
        })

        quality_checks = await analyze_data_quality(df, dataset_id=1)

        # Should find the all-null column
        missing_checks = [check for check in quality_checks if check['check_type'] == 'missing_values']
        all_null_check = next(
            check for check in missing_checks
            if check['column_name'] == 'all_null_col'
        )
        assert all_null_check['severity'] == DataQualitySeverity.CRITICAL.value
        assert all_null_check['details']['percentage'] == 100.0


class TestStatisticsAccuracy:
    """Test accuracy of statistical calculations"""

    def test_numeric_statistics_accuracy(self):
        """Test accuracy of numeric statistical calculations"""
        # Known dataset with predictable statistics
        data = pd.Series([10, 20, 30, 40, 50])
        stats = get_column_statistics(data, "test", 0)

        assert float(stats.min_value) == 10.0
        assert float(stats.max_value) == 50.0
        assert stats.avg_value == 30.0
        assert stats.std_value == pytest.approx(15.811, rel=1e-3)

    def test_string_length_statistics(self):
        """Test accuracy of string length statistics"""
        data = pd.Series(['a', 'ab', 'abc', 'abcd'])  # lengths: 1,2,3,4
        stats = get_column_statistics(data, "test", 0)

        assert float(stats.min_value) == 1.0
        assert float(stats.max_value) == 4.0
        assert stats.avg_value == 2.5
        assert stats.std_value == pytest.approx(1.291, rel=1e-3)

    def test_unique_count_accuracy(self):
        """Test accuracy of unique value counting"""
        # Data with known unique counts
        data = pd.Series([1, 1, 2, 2, 3, 3, 3, 4])
        stats = get_column_statistics(data, "test", 0)

        assert stats.unique_count == 4  # 1, 2, 3, 4
        assert stats.missing_count == 0

    def test_missing_count_accuracy(self):
        """Test accuracy of missing value counting"""
        data = pd.Series([1, None, 2, None, None, 3])
        stats = get_column_statistics(data, "test", 0)

        assert stats.missing_count == 3
        assert stats.unique_count == 3  # 1, 2, 3 (excluding nulls)