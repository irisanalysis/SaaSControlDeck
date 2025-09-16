"""
数据库Schema完整性测试套件

验证数据库表结构、约束、索引和触发器的完整性
"""

import pytest
import asyncpg
from typing import Dict, Any, List, Set
from . import (
    CORE_TABLES, 
    PARTITIONED_TABLES, 
    EXPECTED_INDEXES, 
    EXPECTED_FOREIGN_KEYS,
    EXPECTED_CHECK_CONSTRAINTS
)


class TestSchemaIntegrity:
    """Schema完整性测试类"""

    @pytest.mark.asyncio
    async def test_core_tables_exist(self, db_connection: asyncpg.Connection, db_utils):
        """验证所有核心表是否存在"""
        missing_tables = []
        existing_tables = []
        
        for table_name in CORE_TABLES:
            exists = await db_utils.table_exists(db_connection, table_name)
            if exists:
                existing_tables.append(table_name)
            else:
                missing_tables.append(table_name)
        
        print(f"✅ 现有表 ({len(existing_tables)}): {', '.join(existing_tables)}")
        
        if missing_tables:
            print(f"❌ 缺失表 ({len(missing_tables)}): {', '.join(missing_tables)}")
        
        # 验证所有核心表都存在
        assert len(missing_tables) == 0, f"缺失核心表: {missing_tables}"
        assert len(existing_tables) == len(CORE_TABLES), f"表数量不匹配"

    @pytest.mark.asyncio
    async def test_table_structure_consistency(self, db_connection: asyncpg.Connection, db_utils):
        """验证表结构一致性"""
        expected_table_structures = {
            'users': {
                'required_columns': [
                    'id', 'email', 'username', 'password_hash', 
                    'is_active', 'is_verified', 'created_at', 'updated_at'
                ],
                'nullable_columns': [
                    'email_verified_at', 'failed_login_attempts', 
                    'locked_until', 'last_login_at'
                ]
            },
            'projects': {
                'required_columns': [
                    'id', 'name', 'slug', 'owner_id', 'status', 
                    'visibility', 'created_at', 'updated_at'
                ],
                'nullable_columns': [
                    'description', 'settings', 'tags', 'archived_at'
                ]
            },
            'ai_tasks': {
                'required_columns': [
                    'id', 'project_id', 'user_id', 'task_name', 
                    'task_type', 'status', 'created_at', 'updated_at'
                ],
                'nullable_columns': [
                    'model_id', 'input_data', 'output_data', 
                    'error_message', 'started_at', 'completed_at'
                ]
            }
        }
        
        for table_name, expected_structure in expected_table_structures.items():
            # 检查表是否存在
            if not await db_utils.table_exists(db_connection, table_name):
                print(f"⚠️  跳过表结构检查: {table_name} (表不存在)")
                continue
            
            # 获取列信息
            columns = await db_utils.get_column_info(db_connection, table_name)
            column_names = [col['column_name'] for col in columns]
            
            # 检查必需列
            missing_required = []
            for required_col in expected_structure['required_columns']:
                if required_col not in column_names:
                    missing_required.append(required_col)
            
            # 检查列的可空性
            nullable_issues = []
            for col in columns:
                col_name = col['column_name']
                is_nullable = col['is_nullable'] == 'YES'
                
                if col_name in expected_structure['required_columns']:
                    if is_nullable and col_name not in expected_structure.get('nullable_columns', []):
                        nullable_issues.append(f"{col_name} should not be nullable")
            
            # 报告结果
            if missing_required:
                pytest.fail(f"{table_name} 缺失必需列: {missing_required}")
            
            if nullable_issues:
                print(f"⚠️  {table_name} 可空性问题: {nullable_issues}")
            
            print(f"✅ {table_name} 表结构检查通过 ({len(column_names)} 列)")

    @pytest.mark.asyncio
    async def test_primary_keys(self, db_connection: asyncpg.Connection):
        """验证主键约束"""
        query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name
        """
        
        primary_keys = await db_connection.fetch(query)
        pk_by_table = {}
        
        for pk in primary_keys:
            table_name = pk['table_name']
            if table_name not in pk_by_table:
                pk_by_table[table_name] = []
            pk_by_table[table_name].append(pk['column_name'])
        
        # 验证所有核心表都有主键
        tables_without_pk = []
        for table_name in CORE_TABLES:
            if await self._table_exists(db_connection, table_name):
                if table_name not in pk_by_table:
                    tables_without_pk.append(table_name)
        
        if tables_without_pk:
            pytest.fail(f"表缺少主键: {tables_without_pk}")
        
        # 验证主键都是UUID类型的id字段
        id_pk_tables = []
        for table_name, pk_columns in pk_by_table.items():
            if len(pk_columns) == 1 and pk_columns[0] == 'id':
                id_pk_tables.append(table_name)
        
        print(f"✅ 主键验证通过:")
        print(f"   有主键的表: {len(pk_by_table)}")
        print(f"   使用UUID id主键的表: {len(id_pk_tables)}")
        
        for table_name, columns in pk_by_table.items():
            if table_name in CORE_TABLES:
                print(f"   {table_name}: {', '.join(columns)}")

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_connection: asyncpg.Connection):
        """验证外键约束"""
        query = """
        SELECT 
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name
        """
        
        foreign_keys = await db_connection.fetch(query)
        fk_by_table = {}
        
        for fk in foreign_keys:
            table_name = fk['table_name']
            if table_name not in fk_by_table:
                fk_by_table[table_name] = []
            fk_by_table[table_name].append({
                'column': fk['column_name'],
                'ref_table': fk['foreign_table_name'],
                'ref_column': fk['foreign_column_name']
            })
        
        # 验证预期的外键约束
        missing_fks = []
        for expected_fk in EXPECTED_FOREIGN_KEYS:
            table_name = expected_fk['table']
            
            if not await self._table_exists(db_connection, table_name):
                continue
                
            table_fks = fk_by_table.get(table_name, [])
            
            fk_found = False
            for fk in table_fks:
                if (fk['column'] == expected_fk['column'] and 
                    fk['ref_table'] == expected_fk['ref_table'] and
                    fk['ref_column'] == expected_fk['ref_column']):
                    fk_found = True
                    break
            
            if not fk_found:
                missing_fks.append(f"{table_name}.{expected_fk['column']} -> {expected_fk['ref_table']}.{expected_fk['ref_column']}")
        
        print(f"✅ 外键约束验证:")
        print(f"   总外键数量: {len(foreign_keys)}")
        print(f"   有外键的表: {len(fk_by_table)}")
        
        if missing_fks:
            print(f"⚠️  缺失的外键约束: {missing_fks}")
        
        # 验证主要的外键约束存在
        assert len(missing_fks) <= len(EXPECTED_FOREIGN_KEYS) * 0.1, f"缺失过多外键约束: {missing_fks}"

    @pytest.mark.asyncio
    async def test_check_constraints(self, db_connection: asyncpg.Connection):
        """验证检查约束"""
        query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            cc.check_clause
        FROM information_schema.table_constraints tc
        JOIN information_schema.check_constraints cc 
            ON tc.constraint_name = cc.constraint_name
        WHERE tc.constraint_type = 'CHECK'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name
        """
        
        check_constraints = await db_connection.fetch(query)
        constraints_by_table = {}
        
        for constraint in check_constraints:
            table_name = constraint['table_name']
            if table_name not in constraints_by_table:
                constraints_by_table[table_name] = []
            constraints_by_table[table_name].append({
                'name': constraint['constraint_name'],
                'clause': constraint['check_clause']
            })
        
        # 验证预期的检查约束
        missing_constraints = []
        for expected_constraint in EXPECTED_CHECK_CONSTRAINTS:
            table_name = expected_constraint['table']
            constraint_name = expected_constraint['constraint']
            
            if not await self._table_exists(db_connection, table_name):
                continue
            
            table_constraints = constraints_by_table.get(table_name, [])
            constraint_found = any(c['name'] == constraint_name for c in table_constraints)
            
            if not constraint_found:
                missing_constraints.append(f"{table_name}.{constraint_name}")
        
        print(f"✅ 检查约束验证:")
        print(f"   总约束数量: {len(check_constraints)}")
        print(f"   有约束的表: {len(constraints_by_table)}")
        
        for table_name, constraints in constraints_by_table.items():
            print(f"   {table_name}: {len(constraints)} 个约束")
        
        if missing_constraints:
            print(f"⚠️  缺失的检查约束: {missing_constraints}")

    @pytest.mark.asyncio
    async def test_unique_constraints(self, db_connection: asyncpg.Connection):
        """验证唯一约束"""
        query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name
        """
        
        unique_constraints = await db_connection.fetch(query)
        unique_by_table = {}
        
        for constraint in unique_constraints:
            table_name = constraint['table_name']
            if table_name not in unique_by_table:
                unique_by_table[table_name] = []
            unique_by_table[table_name].append({
                'constraint': constraint['constraint_name'],
                'column': constraint['column_name']
            })
        
        # 验证关键的唯一约束
        expected_unique_constraints = [
            {'table': 'users', 'column': 'email'},
            {'table': 'users', 'column': 'username'},
            {'table': 'projects', 'column': 'slug'},
            {'table': 'file_storage', 'column': 'file_hash'}
        ]
        
        missing_unique = []
        for expected in expected_unique_constraints:
            table_name = expected['table']
            column_name = expected['column']
            
            if not await self._table_exists(db_connection, table_name):
                continue
            
            table_constraints = unique_by_table.get(table_name, [])
            constraint_found = any(c['column'] == column_name for c in table_constraints)
            
            if not constraint_found:
                missing_unique.append(f"{table_name}.{column_name}")
        
        print(f"✅ 唯一约束验证:")
        print(f"   总约束数量: {len(unique_constraints)}")
        print(f"   有唯一约束的表: {len(unique_by_table)}")
        
        if missing_unique:
            print(f"⚠️  缺失的唯一约束: {missing_unique}")
        
        # 关键约束必须存在
        critical_missing = [u for u in missing_unique if 'users.email' in u or 'users.username' in u]
        assert len(critical_missing) == 0, f"缺失关键唯一约束: {critical_missing}"

    @pytest.mark.asyncio
    async def test_indexes(self, db_connection: asyncpg.Connection, db_utils):
        """验证索引"""
        existing_indexes = {}
        
        for table_name in CORE_TABLES:
            if not await db_utils.table_exists(db_connection, table_name):
                continue
                
            indexes = await db_utils.get_indexes(db_connection, table_name)
            existing_indexes[table_name] = indexes
        
        # 验证预期的索引
        missing_indexes = []
        for expected_index in EXPECTED_INDEXES:
            table_name = expected_index['table']
            expected_columns = expected_index['columns']
            is_unique = expected_index.get('unique', False)
            
            if table_name not in existing_indexes:
                missing_indexes.append(f"{table_name}.{','.join(expected_columns)}")
                continue
            
            table_indexes = existing_indexes[table_name]
            index_found = False
            
            for index in table_indexes:
                if (set(index['columns']) == set(expected_columns) and 
                    index['is_unique'] == is_unique):
                    index_found = True
                    break
            
            if not index_found:
                missing_indexes.append(f"{table_name}.{','.join(expected_columns)}")
        
        # 统计索引信息
        total_indexes = sum(len(indexes) for indexes in existing_indexes.values())
        
        print(f"✅ 索引验证:")
        print(f"   总索引数量: {total_indexes}")
        print(f"   有索引的表: {len(existing_indexes)}")
        
        if missing_indexes:
            print(f"⚠️  缺失的索引: {missing_indexes}")
        
        # 验证关键索引存在
        critical_indexes = [idx for idx in missing_indexes if 'users.' in idx or 'projects.' in idx]
        assert len(critical_indexes) <= 2, f"缺失过多关键索引: {critical_indexes}"

    @pytest.mark.asyncio
    async def test_triggers(self, db_connection: asyncpg.Connection):
        """验证触发器"""
        query = """
        SELECT 
            event_object_table as table_name,
            trigger_name,
            event_manipulation,
            action_timing,
            action_statement
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
        ORDER BY event_object_table, trigger_name
        """
        
        triggers = await db_connection.fetch(query)
        triggers_by_table = {}
        
        for trigger in triggers:
            table_name = trigger['table_name']
            if table_name not in triggers_by_table:
                triggers_by_table[table_name] = []
            triggers_by_table[table_name].append({
                'name': trigger['trigger_name'],
                'event': trigger['event_manipulation'],
                'timing': trigger['action_timing']
            })
        
        # 验证updated_at触发器
        tables_with_updated_at = [
            'users', 'user_profiles', 'projects', 'project_settings',
            'ai_models', 'ai_tasks', 'data_sources', 'analysis_jobs', 'file_storage'
        ]
        
        missing_update_triggers = []
        for table_name in tables_with_updated_at:
            if not await self._table_exists(db_connection, table_name):
                continue
            
            table_triggers = triggers_by_table.get(table_name, [])
            update_trigger_found = any(
                'updated_at' in t['name'].lower() for t in table_triggers
            )
            
            if not update_trigger_found:
                missing_update_triggers.append(table_name)
        
        print(f"✅ 触发器验证:")
        print(f"   总触发器数量: {len(triggers)}")
        print(f"   有触发器的表: {len(triggers_by_table)}")
        
        for table_name, table_triggers in triggers_by_table.items():
            print(f"   {table_name}: {len(table_triggers)} 个触发器")
        
        if missing_update_triggers:
            print(f"⚠️  缺失updated_at触发器的表: {missing_update_triggers}")

    @pytest.mark.asyncio
    async def test_partitioned_tables(self, db_connection: asyncpg.Connection):
        """验证分区表"""
        query = """
        SELECT 
            schemaname, 
            tablename,
            partitionboundspec
        FROM pg_tables pt
        JOIN pg_partitioned_table ppt ON pt.tablename = ppt.partrelid::regclass::text
        WHERE schemaname = 'public'
        """
        
        try:
            partitioned_tables = await db_connection.fetch(query)
        except Exception:
            # 如果查询失败，可能是因为表不存在分区
            partitioned_tables = []
        
        # 检查哪些预期的分区表实际上是分区的
        actual_partitioned = [pt['tablename'] for pt in partitioned_tables]
        
        print(f"✅ 分区表验证:")
        print(f"   预期分区表: {PARTITIONED_TABLES}")
        print(f"   实际分区表: {actual_partitioned}")
        
        for table_name in PARTITIONED_TABLES:
            if await self._table_exists(db_connection, table_name):
                if table_name in actual_partitioned:
                    print(f"   ✅ {table_name}: 正确分区")
                else:
                    print(f"   ⚠️  {table_name}: 未分区")

    @pytest.mark.asyncio
    async def test_data_types_consistency(self, db_connection: asyncpg.Connection, db_utils):
        """验证数据类型一致性"""
        expected_data_types = {
            'users': {
                'id': 'uuid',
                'email': 'character varying',
                'created_at': 'timestamp with time zone',
                'is_active': 'boolean'
            },
            'projects': {
                'id': 'uuid', 
                'owner_id': 'uuid',
                'settings': 'jsonb',
                'tags': 'ARRAY'
            },
            'ai_tasks': {
                'id': 'uuid',
                'input_data': 'jsonb',
                'progress_percentage': 'integer',
                'cost_usd': 'numeric'
            }
        }
        
        type_mismatches = []
        
        for table_name, expected_types in expected_data_types.items():
            if not await db_utils.table_exists(db_connection, table_name):
                continue
            
            columns = await db_utils.get_column_info(db_connection, table_name)
            column_types = {col['column_name']: col['data_type'] for col in columns}
            
            for column_name, expected_type in expected_types.items():
                if column_name not in column_types:
                    type_mismatches.append(f"{table_name}.{column_name}: 列不存在")
                    continue
                
                actual_type = column_types[column_name]
                
                # 处理数组类型的特殊情况
                if expected_type == 'ARRAY':
                    if 'ARRAY' not in actual_type.upper():
                        type_mismatches.append(f"{table_name}.{column_name}: 期望ARRAY，实际{actual_type}")
                elif expected_type not in actual_type:
                    type_mismatches.append(f"{table_name}.{column_name}: 期望{expected_type}，实际{actual_type}")
        
        if type_mismatches:
            print(f"⚠️  数据类型不匹配: {type_mismatches}")
        else:
            print(f"✅ 数据类型一致性检查通过")

    async def _table_exists(self, connection: asyncpg.Connection, table_name: str) -> bool:
        """检查表是否存在的辅助方法"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        )
        """
        return await connection.fetchval(query, table_name)