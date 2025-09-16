"""
文件存储模块CRUD操作测试套件

测试文件存储相关表的完整CRUD操作
"""

import pytest
import asyncpg
import json
import hashlib
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta


class TestFileStorageCRUD:
    """文件存储CRUD操作测试类"""

    @pytest.mark.asyncio
    async def test_file_storage_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试file_storage表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not table_exists:
            pytest.skip("file_storage表不存在")

        # CREATE - 上传文件
        file_content = "This is a test CSV file with sample data for analysis.\nname,age,city\nJohn,30,New York\nJane,25,Los Angeles"
        file_hash = hashlib.sha256(file_content.encode()).hexdigest()
        
        file_data = {
            'project_id': sample_project_in_db['id'],
            'user_id': sample_user_in_db['id'],
            'file_name': 'test_data_20240101.csv',
            'original_name': 'sample_data.csv',
            'file_path': '/storage/projects/test_data_20240101.csv',
            'file_hash': file_hash,
            'file_size': len(file_content),
            'mime_type': 'text/csv',
            'storage_type': 'local',
            'storage_config': {
                'bucket': 'saas-control-files',
                'region': 'us-west-2',
                'encryption': 'AES256',
                'backup_enabled': True
            },
            'upload_status': 'completed',
            'download_count': 0,
            'is_public': False
        }
        
        file_id = await db_transaction.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash, 
             file_size, mime_type, storage_type, storage_config, upload_status, 
             download_count, is_public)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
            """,
            file_data['project_id'], file_data['user_id'], file_data['file_name'],
            file_data['original_name'], file_data['file_path'], file_data['file_hash'],
            file_data['file_size'], file_data['mime_type'], file_data['storage_type'],
            json.dumps(file_data['storage_config']), file_data['upload_status'],
            file_data['download_count'], file_data['is_public']
        )
        
        assert file_id is not None
        print(f"✅ 创建文件记录成功: {file_id}")

        # READ - 查询文件信息
        created_file = await db_transaction.fetchrow(
            "SELECT * FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert created_file is not None
        assert created_file['file_name'] == file_data['file_name']
        assert created_file['file_hash'] == file_data['file_hash']
        assert created_file['file_size'] == file_data['file_size']
        assert created_file['mime_type'] == file_data['mime_type']
        assert created_file['upload_status'] == file_data['upload_status']
        print("✅ 查询文件信息成功")

        # UPDATE - 更新下载计数
        new_download_count = 5
        await db_transaction.execute(
            "UPDATE file_storage SET download_count = $1 WHERE id = $2",
            new_download_count, file_id
        )
        
        # 验证下载计数更新
        updated_file = await db_transaction.fetchrow(
            "SELECT download_count FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert updated_file['download_count'] == new_download_count
        print("✅ 更新下载计数成功")

        # UPDATE - 设置文件过期时间
        expiry_time = datetime.now(timezone.utc) + timedelta(days=30)
        await db_transaction.execute(
            "UPDATE file_storage SET expires_at = $1 WHERE id = $2",
            expiry_time, file_id
        )
        
        # 验证过期时间设置
        file_with_expiry = await db_transaction.fetchrow(
            "SELECT expires_at FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert file_with_expiry['expires_at'] is not None
        print("✅ 设置文件过期时间成功")

        # UPDATE - 改变文件可见性
        await db_transaction.execute(
            "UPDATE file_storage SET is_public = true WHERE id = $1",
            file_id
        )
        
        # 验证可见性更改
        public_file = await db_transaction.fetchrow(
            "SELECT is_public FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert public_file['is_public'] == True
        print("✅ 更改文件可见性成功")

        # UPDATE - 模拟文件删除（软删除）
        await db_transaction.execute(
            "UPDATE file_storage SET upload_status = 'deleted' WHERE id = $1",
            file_id
        )
        
        # 验证软删除
        deleted_file = await db_transaction.fetchrow(
            "SELECT upload_status FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert deleted_file['upload_status'] == 'deleted'
        print("✅ 文件软删除成功")

        # DELETE - 物理删除文件记录
        await db_transaction.execute(
            "DELETE FROM file_storage WHERE id = $1",
            file_id
        )
        
        # 验证物理删除
        physical_deleted = await db_transaction.fetchrow(
            "SELECT * FROM file_storage WHERE id = $1",
            file_id
        )
        
        assert physical_deleted is None
        print("✅ 文件物理删除成功")

    @pytest.mark.asyncio
    async def test_file_metadata_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试file_metadata表的CRUD操作"""
        # 检查表是否存在
        metadata_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_metadata')"
        )
        storage_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not (metadata_exists and storage_exists):
            pytest.skip("file_metadata或file_storage表不存在")

        # 首先创建一个文件记录
        file_id = await db_transaction.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash, 
             file_size, mime_type, upload_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'], 'metadata_test.json',
            'metadata_test.json', '/storage/metadata_test.json', 'hash123',
            1024, 'application/json', 'completed'
        )

        # CREATE - 添加文件元数据
        metadata_entries = [
            {
                'file_id': file_id,
                'metadata_category': 'file_info',
                'metadata_key': 'dimensions',
                'metadata_value': {
                    'width': 1920,
                    'height': 1080,
                    'format': 'JSON',
                    'version': '1.0'
                },
                'extracted_by': 'file_analyzer_v2.1'
            },
            {
                'file_id': file_id,
                'metadata_category': 'content',
                'metadata_key': 'schema',
                'metadata_value': {
                    'fields': [
                        {'name': 'id', 'type': 'integer', 'nullable': False},
                        {'name': 'name', 'type': 'string', 'nullable': False},
                        {'name': 'email', 'type': 'string', 'nullable': True}
                    ],
                    'record_count': 1500,
                    'estimated_size': 125000
                },
                'extracted_by': 'schema_detector_v1.3'
            },
            {
                'file_id': file_id,
                'metadata_category': 'quality',
                'metadata_key': 'data_quality',
                'metadata_value': {
                    'completeness': 0.95,
                    'accuracy': 0.92,
                    'consistency': 0.88,
                    'validity': 0.94,
                    'duplicate_rate': 0.02
                },
                'extracted_by': 'quality_assessor_v3.0'
            },
            {
                'file_id': file_id,
                'metadata_category': 'security',
                'metadata_key': 'scan_results',
                'metadata_value': {
                    'virus_scan': 'clean',
                    'malware_scan': 'clean',
                    'pii_detected': True,
                    'sensitive_fields': ['email', 'phone'],
                    'scan_timestamp': datetime.now(timezone.utc).isoformat()
                },
                'extracted_by': 'security_scanner_v2.5'
            }
        ]
        
        metadata_ids = []
        for metadata in metadata_entries:
            metadata_id = await db_transaction.fetchval(
                """
                INSERT INTO file_metadata 
                (file_id, metadata_category, metadata_key, metadata_value, extracted_by)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                metadata['file_id'], metadata['metadata_category'], 
                metadata['metadata_key'], json.dumps(metadata['metadata_value']),
                metadata['extracted_by']
            )
            metadata_ids.append(metadata_id)
        
        print(f"✅ 创建文件元数据成功: {len(metadata_ids)} 条记录")

        # READ - 查询特定类别的元数据
        content_metadata = await db_transaction.fetch(
            """
            SELECT * FROM file_metadata 
            WHERE file_id = $1 AND metadata_category = $2
            """,
            file_id, 'content'
        )
        
        assert len(content_metadata) > 0
        print(f"✅ 查询内容元数据: {len(content_metadata)} 条记录")

        # READ - 查询所有元数据
        all_metadata = await db_transaction.fetch(
            "SELECT * FROM file_metadata WHERE file_id = $1 ORDER BY metadata_category, metadata_key",
            file_id
        )
        
        assert len(all_metadata) == 4
        print(f"✅ 查询所有元数据: {len(all_metadata)} 条记录")

        # UPDATE - 更新数据质量元数据
        updated_quality_data = {
            'completeness': 0.97,
            'accuracy': 0.94,
            'consistency': 0.90,
            'validity': 0.96,
            'duplicate_rate': 0.01,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        await db_transaction.execute(
            """
            UPDATE file_metadata 
            SET metadata_value = $1
            WHERE file_id = $2 AND metadata_category = $3 AND metadata_key = $4
            """,
            json.dumps(updated_quality_data), file_id, 'quality', 'data_quality'
        )
        
        # 验证更新
        updated_metadata = await db_transaction.fetchrow(
            """
            SELECT * FROM file_metadata 
            WHERE file_id = $1 AND metadata_category = $2 AND metadata_key = $3
            """,
            file_id, 'quality', 'data_quality'
        )
        
        updated_value = json.loads(updated_metadata['metadata_value'])
        assert updated_value['completeness'] == 0.97
        assert updated_value['accuracy'] == 0.94
        print("✅ 更新元数据成功")

        # READ - 元数据统计查询
        metadata_stats = await db_transaction.fetch(
            """
            SELECT 
                metadata_category,
                COUNT(*) as count,
                COUNT(DISTINCT metadata_key) as unique_keys
            FROM file_metadata 
            WHERE file_id = $1
            GROUP BY metadata_category
            ORDER BY metadata_category
            """,
            file_id
        )
        
        print("✅ 元数据统计:")
        for stat in metadata_stats:
            print(f"   {stat['metadata_category']}: {stat['count']} 条记录, {stat['unique_keys']} 个不同的键")

        # DELETE - 删除特定类别的元数据
        await db_transaction.execute(
            "DELETE FROM file_metadata WHERE file_id = $1 AND metadata_category = $2",
            file_id, 'security'
        )
        
        # 验证删除
        remaining_metadata = await db_transaction.fetch(
            "SELECT * FROM file_metadata WHERE file_id = $1",
            file_id
        )
        
        assert len(remaining_metadata) == 3  # 应该剩余3条记录
        print("✅ 删除特定类别元数据成功")

        # DELETE - 删除所有元数据
        await db_transaction.execute(
            "DELETE FROM file_metadata WHERE file_id = $1",
            file_id
        )
        
        # 验证删除
        deleted_metadata = await db_transaction.fetch(
            "SELECT * FROM file_metadata WHERE file_id = $1",
            file_id
        )
        
        assert len(deleted_metadata) == 0
        print("✅ 删除所有元数据成功")

    @pytest.mark.asyncio
    async def test_file_storage_relationships(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试文件存储表之间的关系完整性"""
        # 检查所有相关表是否存在
        required_tables = ['file_storage', 'file_metadata']
        existing_tables = []
        
        for table in required_tables:
            exists = await db_transaction.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table
            )
            if exists:
                existing_tables.append(table)
        
        if len(existing_tables) < len(required_tables):
            pytest.skip(f"缺少必要的表: {set(required_tables) - set(existing_tables)}")

        # 创建测试文件
        file_id = await db_transaction.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash, 
             file_size, mime_type, upload_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'], 'relationship_test.csv',
            'relationship_test.csv', '/storage/relationship_test.csv', 'hash456',
            2048, 'text/csv', 'completed'
        )

        # 创建关联的元数据
        metadata_ids = []
        for i in range(3):
            metadata_id = await db_transaction.fetchval(
                """
                INSERT INTO file_metadata 
                (file_id, metadata_category, metadata_key, metadata_value)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                file_id, f'category_{i}', f'key_{i}', 
                json.dumps({'value': f'test_value_{i}'})
            )
            metadata_ids.append(metadata_id)

        # 验证关系存在
        metadata_count = await db_transaction.fetchval(
            "SELECT COUNT(*) FROM file_metadata WHERE file_id = $1",
            file_id
        )
        
        assert metadata_count == 3
        print("✅ 文件-元数据关系建立成功")

        # 测试级联删除
        await db_transaction.execute(
            "DELETE FROM file_storage WHERE id = $1",
            file_id
        )

        # 验证级联删除
        metadata_after_delete = await db_transaction.fetchval(
            "SELECT COUNT(*) FROM file_metadata WHERE file_id = $1",
            file_id
        )
        
        assert metadata_after_delete == 0
        print("✅ 级联删除验证成功")

        # 测试文件与项目的关系
        project_files = await db_transaction.fetch(
            """
            SELECT fs.*, p.name as project_name, u.username as uploader
            FROM file_storage fs
            JOIN projects p ON fs.project_id = p.id
            JOIN users u ON fs.user_id = u.id
            WHERE fs.project_id = $1
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 项目文件关系查询: 找到 {len(project_files)} 个文件")

    @pytest.mark.asyncio
    async def test_file_deduplication(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试文件去重功能"""
        # 检查file_storage表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not table_exists:
            pytest.skip("file_storage表不存在")

        # 创建相同hash的文件，测试唯一性约束
        duplicate_hash = 'duplicate_file_hash_12345'
        
        # 创建第一个文件
        first_file_id = await db_transaction.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash, 
             file_size, mime_type, upload_status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'], 'original_file.txt',
            'original_file.txt', '/storage/original_file.txt', duplicate_hash,
            1024, 'text/plain', 'completed'
        )
        
        assert first_file_id is not None
        print("✅ 创建原始文件成功")

        # 尝试创建具有相同hash的文件
        duplicate_rejected = False
        try:
            await db_transaction.execute(
                """
                INSERT INTO file_storage 
                (project_id, user_id, file_name, original_name, file_path, file_hash, 
                 file_size, mime_type, upload_status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                sample_project_in_db['id'], sample_user_in_db['id'], 'duplicate_file.txt',
                'duplicate_file.txt', '/storage/duplicate_file.txt', duplicate_hash,
                1024, 'text/plain', 'completed'
            )
            print("❌ 重复文件未被阻止")
        except Exception:
            duplicate_rejected = True
            print("✅ 重复文件被正确拒绝")

        # 验证去重功能
        assert duplicate_rejected, "文件去重功能未生效"

        # 查询具有该hash的文件数量
        file_count = await db_transaction.fetchval(
            "SELECT COUNT(*) FROM file_storage WHERE file_hash = $1",
            duplicate_hash
        )
        
        assert file_count == 1, f"期望1个文件，实际找到{file_count}个"

    @pytest.mark.asyncio
    async def test_file_search_and_filtering(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试文件搜索和过滤功能"""
        # 检查file_storage表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not table_exists:
            pytest.skip("file_storage表不存在")

        # 创建多种类型的测试文件
        test_files = [
            {
                'file_name': 'sales_report_2024.csv',
                'mime_type': 'text/csv',
                'file_size': 15000,
                'storage_type': 'local',
                'is_public': False
            },
            {
                'file_name': 'user_data_export.json',
                'mime_type': 'application/json',
                'file_size': 8500,
                'storage_type': 's3',
                'is_public': True
            },
            {
                'file_name': 'project_documentation.pdf',
                'mime_type': 'application/pdf',
                'file_size': 250000,
                'storage_type': 'minio',
                'is_public': False
            },
            {
                'file_name': 'data_visualization.png',
                'mime_type': 'image/png',
                'file_size': 120000,
                'storage_type': 'local',
                'is_public': True
            },
            {
                'file_name': 'backup_database.sql',
                'mime_type': 'application/sql',
                'file_size': 5000000,
                'storage_type': 's3',
                'is_public': False
            }
        ]
        
        created_file_ids = []
        for i, file_data in enumerate(test_files):
            file_id = await db_transaction.fetchval(
                """
                INSERT INTO file_storage 
                (project_id, user_id, file_name, original_name, file_path, file_hash, 
                 file_size, mime_type, storage_type, upload_status, is_public)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
                """,
                sample_project_in_db['id'], sample_user_in_db['id'], 
                file_data['file_name'], file_data['file_name'], 
                f"/storage/{file_data['file_name']}", f"hash_{i}",
                file_data['file_size'], file_data['mime_type'], 
                file_data['storage_type'], 'completed', file_data['is_public']
            )
            created_file_ids.append(file_id)

        # 1. 按文件名搜索
        name_search = await db_transaction.fetch(
            "SELECT id, file_name FROM file_storage WHERE file_name ILIKE $1",
            "%data%"
        )
        
        print(f"✅ 文件名搜索 ('%data%'): 找到 {len(name_search)} 个文件")

        # 2. 按MIME类型过滤
        image_files = await db_transaction.fetch(
            "SELECT id, file_name, mime_type FROM file_storage WHERE mime_type LIKE $1",
            "image/%"
        )
        
        csv_files = await db_transaction.fetch(
            "SELECT id, file_name, mime_type FROM file_storage WHERE mime_type = $1",
            "text/csv"
        )
        
        print(f"✅ MIME类型过滤:")
        print(f"   图片文件: {len(image_files)}")
        print(f"   CSV文件: {len(csv_files)}")

        # 3. 按文件大小过滤
        large_files = await db_transaction.fetch(
            "SELECT id, file_name, file_size FROM file_storage WHERE file_size > $1",
            100000  # 大于100KB
        )
        
        small_files = await db_transaction.fetch(
            "SELECT id, file_name, file_size FROM file_storage WHERE file_size < $1",
            50000   # 小于50KB
        )
        
        print(f"✅ 文件大小过滤:")
        print(f"   大文件 (>100KB): {len(large_files)}")
        print(f"   小文件 (<50KB): {len(small_files)}")

        # 4. 按存储类型过滤
        storage_types = await db_transaction.fetch(
            """
            SELECT 
                storage_type, 
                COUNT(*) as file_count,
                SUM(file_size) as total_size
            FROM file_storage 
            WHERE project_id = $1
            GROUP BY storage_type
            ORDER BY file_count DESC
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 按存储类型统计:")
        for storage_stat in storage_types:
            print(f"   {storage_stat['storage_type']}: {storage_stat['file_count']} 文件, {storage_stat['total_size']} 字节")

        # 5. 按可见性过滤
        public_files = await db_transaction.fetch(
            "SELECT id, file_name FROM file_storage WHERE is_public = true"
        )
        
        private_files = await db_transaction.fetch(
            "SELECT id, file_name FROM file_storage WHERE is_public = false AND project_id = $1",
            sample_project_in_db['id']
        )
        
        print(f"✅ 按可见性过滤:")
        print(f"   公开文件: {len(public_files)}")
        print(f"   私有文件: {len(private_files)}")

        # 6. 复合搜索
        complex_search = await db_transaction.fetch(
            """
            SELECT id, file_name, file_size, mime_type, storage_type
            FROM file_storage 
            WHERE project_id = $1
            AND upload_status = 'completed'
            AND file_size BETWEEN 10000 AND 300000
            AND storage_type IN ('local', 's3')
            ORDER BY file_size DESC
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 复合搜索: 符合条件的文件 {len(complex_search)} 个")

        # 7. 文件统计摘要
        file_summary = await db_transaction.fetchrow(
            """
            SELECT 
                COUNT(*) as total_files,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                MAX(file_size) as max_size,
                MIN(file_size) as min_size,
                COUNT(DISTINCT mime_type) as mime_type_count,
                COUNT(CASE WHEN is_public THEN 1 END) as public_files
            FROM file_storage 
            WHERE project_id = $1
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 文件统计摘要:")
        print(f"   总文件数: {file_summary['total_files']}")
        print(f"   总大小: {file_summary['total_size']:,} 字节")
        print(f"   平均大小: {file_summary['avg_size']:,.0f} 字节")
        print(f"   最大文件: {file_summary['max_size']:,} 字节")
        print(f"   最小文件: {file_summary['min_size']:,} 字节")
        print(f"   MIME类型数: {file_summary['mime_type_count']}")
        print(f"   公开文件数: {file_summary['public_files']}")

    @pytest.mark.asyncio
    async def test_file_lifecycle_management(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试文件生命周期管理"""
        # 检查file_storage表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'file_storage')"
        )
        
        if not table_exists:
            pytest.skip("file_storage表不存在")

        # 1. 创建文件（上传中状态）
        file_id = await db_transaction.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash, 
             file_size, mime_type, upload_status, is_public)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'], 
            'lifecycle_test.dat', 'lifecycle_test.dat', 
            '/storage/lifecycle_test.dat', 'lifecycle_hash',
            10240, 'application/octet-stream', 'uploading', False
        )

        # 2. 完成上传
        await db_transaction.execute(
            "UPDATE file_storage SET upload_status = 'completed' WHERE id = $1",
            file_id
        )
        
        file_status = await db_transaction.fetchval(
            "SELECT upload_status FROM file_storage WHERE id = $1",
            file_id
        )
        assert file_status == 'completed'
        print("✅ 文件上传完成")

        # 3. 模拟文件访问（增加下载次数）
        for i in range(5):
            await db_transaction.execute(
                "UPDATE file_storage SET download_count = download_count + 1 WHERE id = $1",
                file_id
            )

        download_count = await db_transaction.fetchval(
            "SELECT download_count FROM file_storage WHERE id = $1",
            file_id
        )
        assert download_count == 5
        print(f"✅ 文件访问记录: {download_count} 次下载")

        # 4. 设置文件过期
        expiry_time = datetime.now(timezone.utc) + timedelta(days=7)
        await db_transaction.execute(
            "UPDATE file_storage SET expires_at = $1 WHERE id = $2",
            expiry_time, file_id
        )
        
        print("✅ 设置文件过期时间")

        # 5. 查找即将过期的文件
        expiring_files = await db_transaction.fetch(
            """
            SELECT id, file_name, expires_at 
            FROM file_storage 
            WHERE expires_at IS NOT NULL 
            AND expires_at < $1
            AND upload_status = 'completed'
            """,
            datetime.now(timezone.utc) + timedelta(days=10)  # 10天内过期
        )
        
        print(f"✅ 即将过期文件: {len(expiring_files)} 个")

        # 6. 模拟文件归档
        await db_transaction.execute(
            """
            UPDATE file_storage 
            SET storage_type = 'archive', 
                storage_config = $1
            WHERE id = $2
            """,
            json.dumps({'archive_tier': 'glacier', 'archived_at': datetime.now(timezone.utc).isoformat()}),
            file_id
        )
        
        print("✅ 文件归档完成")

        # 7. 标记文件删除
        await db_transaction.execute(
            "UPDATE file_storage SET upload_status = 'deleted' WHERE id = $1",
            file_id
        )
        
        deleted_status = await db_transaction.fetchval(
            "SELECT upload_status FROM file_storage WHERE id = $1",
            file_id
        )
        assert deleted_status == 'deleted'
        print("✅ 文件标记删除")

        # 8. 查询文件状态分布
        status_distribution = await db_transaction.fetch(
            """
            SELECT 
                upload_status,
                COUNT(*) as count,
                SUM(file_size) as total_size
            FROM file_storage 
            WHERE project_id = $1
            GROUP BY upload_status
            ORDER BY count DESC
            """,
            sample_project_in_db['id']
        )
        
        print("✅ 文件状态分布:")
        for status_stat in status_distribution:
            print(f"   {status_stat['upload_status']}: {status_stat['count']} 文件, {status_stat['total_size']} 字节")

        # 9. 清理已删除文件（物理删除）
        cleanup_count = await db_transaction.fetchval(
            """
            DELETE FROM file_storage 
            WHERE upload_status = 'deleted' 
            AND updated_at < $1
            """,
            datetime.now(timezone.utc) - timedelta(days=1)  # 删除1天前标记删除的文件
        )
        
        print(f"✅ 清理已删除文件: {cleanup_count} 个文件被物理删除")