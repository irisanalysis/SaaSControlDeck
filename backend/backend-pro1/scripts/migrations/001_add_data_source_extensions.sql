-- 数据源扩展迁移脚本
-- 扩展现有datasets表以支持数据源连接功能

-- 添加新字段到datasets表
ALTER TABLE datasets
ADD COLUMN IF NOT EXISTS type VARCHAR(50) NOT NULL DEFAULT 'csv' CHECK (type IN ('csv', 'json', 'excel', 'parquet')),
ADD COLUMN IF NOT EXISTS rows_count INTEGER,
ADD COLUMN IF NOT EXISTS columns_count INTEGER,
ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'uploading'
    CHECK (status IN ('uploading', 'processing', 'ready', 'error')),
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64), -- SHA256 hash for duplicate detection
ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255),
ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS encoding VARCHAR(50) DEFAULT 'utf-8',
ADD COLUMN IF NOT EXISTS delimiter VARCHAR(10), -- for CSV files
ADD COLUMN IF NOT EXISTS has_header BOOLEAN DEFAULT true, -- for CSV files
ADD COLUMN IF NOT EXISTS preview_data JSONB, -- cached preview data
ADD COLUMN IF NOT EXISTS error_details TEXT, -- error messages during processing
ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITH TIME ZONE;

-- 更新现有记录的默认值
UPDATE datasets SET type = 'csv' WHERE type IS NULL;
UPDATE datasets SET status = 'ready' WHERE upload_status = 'completed' AND status = 'uploading';
UPDATE datasets SET status = 'error' WHERE upload_status = 'failed' AND status = 'uploading';

-- 创建新的索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_datasets_type ON datasets(type);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_file_hash ON datasets(file_hash);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at);
CREATE INDEX IF NOT EXISTS idx_datasets_processing_started_at ON datasets(processing_started_at);

-- 创建数据源列信息表
CREATE TABLE IF NOT EXISTS dataset_columns (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    column_index INTEGER NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- string, number, date, boolean, null
    is_nullable BOOLEAN DEFAULT true,
    unique_count INTEGER DEFAULT 0,
    missing_count INTEGER DEFAULT 0,
    min_value TEXT,
    max_value TEXT,
    avg_value NUMERIC,
    std_value NUMERIC,
    sample_values TEXT[], -- array of sample values
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建数据源列信息索引
CREATE INDEX IF NOT EXISTS idx_dataset_columns_dataset_id ON dataset_columns(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_columns_name ON dataset_columns(column_name);
CREATE INDEX IF NOT EXISTS idx_dataset_columns_type ON dataset_columns(data_type);

-- 创建数据源文件上传会话表（用于跟踪上传进度）
CREATE TABLE IF NOT EXISTS upload_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    project_id BIGINT REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_size BIGINT DEFAULT 0,
    chunk_size INTEGER DEFAULT 1048576, -- 1MB chunks
    total_chunks INTEGER NOT NULL,
    uploaded_chunks INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'uploading'
        CHECK (status IN ('uploading', 'processing', 'completed', 'failed', 'cancelled')),
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE SET NULL,
    temp_file_path TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '24 hours'
);

-- 创建上传会话索引
CREATE INDEX IF NOT EXISTS idx_upload_sessions_user_id ON upload_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_status ON upload_sessions(status);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_created_at ON upload_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_upload_sessions_expires_at ON upload_sessions(expires_at);

-- 为upload_sessions表添加更新时间触发器
CREATE TRIGGER update_upload_sessions_updated_at
    BEFORE UPDATE ON upload_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 创建数据质量检查结果表
CREATE TABLE IF NOT EXISTS data_quality_checks (
    id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES datasets(id) ON DELETE CASCADE,
    check_type VARCHAR(100) NOT NULL, -- missing_values, duplicates, outliers, data_types
    column_name VARCHAR(255), -- null for dataset-level checks
    severity VARCHAR(20) NOT NULL DEFAULT 'info'
        CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    affected_rows INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建数据质量检查索引
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_dataset_id ON data_quality_checks(dataset_id);
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_type ON data_quality_checks(check_type);
CREATE INDEX IF NOT EXISTS idx_data_quality_checks_severity ON data_quality_checks(severity);

-- 添加一些示例数据源类型配置
INSERT INTO datasets (project_id, name, type, status, file_size, rows_count, columns_count, metadata)
SELECT
    1, -- 假设存在project_id=1
    'Sample CSV Dataset',
    'csv',
    'ready',
    1024000,
    1000,
    10,
    '{
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": true,
        "data_types": {
            "id": "number",
            "name": "string",
            "email": "string",
            "age": "number",
            "created_at": "date"
        }
    }'::jsonb
WHERE EXISTS (SELECT 1 FROM projects WHERE id = 1)
ON CONFLICT DO NOTHING;

-- 创建清理过期上传会话的函数
CREATE OR REPLACE FUNCTION cleanup_expired_upload_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM upload_sessions
    WHERE expires_at < NOW() AND status NOT IN ('completed');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 注释：在生产环境中，建议设置定时任务定期清理过期的上传会话
-- 例如：SELECT cron.schedule('cleanup-uploads', '0 2 * * *', 'SELECT cleanup_expired_upload_sessions();');