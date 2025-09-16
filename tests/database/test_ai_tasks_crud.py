"""
AI任务模块CRUD操作测试套件

测试AI任务管理相关表的完整CRUD操作
"""

import pytest
import asyncpg
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal


class TestAITasksCRUD:
    """AI任务CRUD操作测试类"""

    @pytest.mark.asyncio
    async def test_ai_models_crud(self, db_transaction: asyncpg.Connection):
        """测试ai_models表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_models')"
        )
        
        if not table_exists:
            pytest.skip("ai_models表不存在")

        # CREATE - 创建AI模型
        model_data = {
            'name': 'GPT-4 Turbo',
            'version': '2024-01',
            'model_type': 'language_model',
            'provider': 'openai',
            'configuration': {
                'max_tokens': 128000,
                'temperature_range': [0.0, 2.0],
                'supports_streaming': True,
                'supports_function_calling': True,
                'context_window': 128000
            },
            'capabilities': {
                'text_generation': True,
                'text_analysis': True,
                'code_generation': True,
                'image_analysis': False,
                'fine_tuning': True
            },
            'pricing_info': {
                'input_price_per_1k_tokens': 0.01,
                'output_price_per_1k_tokens': 0.03,
                'currency': 'USD',
                'billing_unit': 'tokens'
            },
            'performance_metrics': {
                'average_response_time_ms': 2000,
                'tokens_per_second': 50,
                'accuracy_score': 0.95,
                'reliability_score': 0.99
            },
            'is_active': True,
            'is_deprecated': False
        }
        
        model_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_models 
            (name, version, model_type, provider, configuration, capabilities, 
             pricing_info, performance_metrics, is_active, is_deprecated)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            model_data['name'], model_data['version'], model_data['model_type'],
            model_data['provider'], json.dumps(model_data['configuration']),
            json.dumps(model_data['capabilities']), json.dumps(model_data['pricing_info']),
            json.dumps(model_data['performance_metrics']), model_data['is_active'],
            model_data['is_deprecated']
        )
        
        assert model_id is not None
        print(f"✅ 创建AI模型成功: {model_id}")

        # READ - 查询AI模型
        created_model = await db_transaction.fetchrow(
            "SELECT * FROM ai_models WHERE id = $1",
            model_id
        )
        
        assert created_model is not None
        assert created_model['name'] == model_data['name']
        assert created_model['version'] == model_data['version']
        assert created_model['provider'] == model_data['provider']
        assert created_model['is_active'] == model_data['is_active']
        print("✅ 查询AI模型成功")

        # UPDATE - 更新模型性能指标
        updated_metrics = {
            'average_response_time_ms': 1800,
            'tokens_per_second': 55,
            'accuracy_score': 0.96,
            'reliability_score': 0.995,
            'last_benchmark_date': datetime.now(timezone.utc).isoformat()
        }
        
        await db_transaction.execute(
            """
            UPDATE ai_models 
            SET performance_metrics = $1
            WHERE id = $2
            """,
            json.dumps(updated_metrics), model_id
        )
        
        # 验证更新
        updated_model = await db_transaction.fetchrow(
            "SELECT * FROM ai_models WHERE id = $1",
            model_id
        )
        
        updated_performance = json.loads(updated_model['performance_metrics'])
        assert updated_performance['tokens_per_second'] == 55
        assert updated_performance['accuracy_score'] == 0.96
        print("✅ 更新AI模型成功")

        # UPDATE - 标记模型为已弃用
        deprecated_time = datetime.now(timezone.utc)
        await db_transaction.execute(
            """
            UPDATE ai_models 
            SET is_deprecated = true, is_active = false, deprecated_at = $1
            WHERE id = $2
            """,
            deprecated_time, model_id
        )
        
        # 验证弃用状态
        deprecated_model = await db_transaction.fetchrow(
            "SELECT * FROM ai_models WHERE id = $1",
            model_id
        )
        
        assert deprecated_model['is_deprecated'] == True
        assert deprecated_model['is_active'] == False
        assert deprecated_model['deprecated_at'] is not None
        print("✅ 标记模型弃用成功")

        # DELETE - 删除AI模型
        await db_transaction.execute(
            "DELETE FROM ai_models WHERE id = $1",
            model_id
        )
        
        # 验证删除
        deleted_model = await db_transaction.fetchrow(
            "SELECT * FROM ai_models WHERE id = $1",
            model_id
        )
        
        assert deleted_model is None
        print("✅ 删除AI模型成功")

    @pytest.mark.asyncio
    async def test_ai_tasks_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试ai_tasks表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_tasks')"
        )
        
        if not table_exists:
            pytest.skip("ai_tasks表不存在")

        # 首先创建一个AI模型（如果ai_models表存在）
        model_id = None
        ai_models_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_models')"
        )
        
        if ai_models_exists:
            model_id = await db_transaction.fetchval(
                """
                INSERT INTO ai_models (name, version, model_type, provider)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                'Test GPT Model', 'v1.0', 'language_model', 'openai'
            )

        # CREATE - 创建AI任务
        task_data = {
            'project_id': sample_project_in_db['id'],
            'user_id': sample_user_in_db['id'],
            'model_id': model_id,
            'task_name': 'Document Analysis Task',
            'task_type': 'text_analysis',
            'priority': 'high',
            'status': 'pending',
            'input_data': {
                'text': 'This is a comprehensive analysis of the quarterly business report...',
                'analysis_type': 'sentiment_and_entities',
                'language': 'en',
                'options': {
                    'include_sentiment': True,
                    'extract_entities': True,
                    'summarize': True,
                    'max_summary_length': 200
                }
            },
            'progress_percentage': 0,
            'retry_count': 0,
            'max_retries': 3,
            'estimated_duration_seconds': 120
        }
        
        task_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_tasks 
            (project_id, user_id, model_id, task_name, task_type, priority, status, 
             input_data, progress_percentage, retry_count, max_retries, estimated_duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
            """,
            task_data['project_id'], task_data['user_id'], task_data['model_id'],
            task_data['task_name'], task_data['task_type'], task_data['priority'],
            task_data['status'], json.dumps(task_data['input_data']),
            task_data['progress_percentage'], task_data['retry_count'],
            task_data['max_retries'], task_data['estimated_duration_seconds']
        )
        
        assert task_id is not None
        print(f"✅ 创建AI任务成功: {task_id}")

        # READ - 查询AI任务
        created_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            task_id
        )
        
        assert created_task is not None
        assert created_task['project_id'] == task_data['project_id']
        assert created_task['task_name'] == task_data['task_name']
        assert created_task['task_type'] == task_data['task_type']
        assert created_task['priority'] == task_data['priority']
        assert created_task['status'] == task_data['status']
        print("✅ 查询AI任务成功")

        # UPDATE - 开始执行任务
        start_time = datetime.now(timezone.utc)
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'running', started_at = $1, progress_percentage = 10
            WHERE id = $2
            """,
            start_time, task_id
        )
        
        # 模拟任务进度更新
        progress_updates = [25, 50, 75, 90]
        for progress in progress_updates:
            await db_transaction.execute(
                """
                UPDATE ai_tasks 
                SET progress_percentage = $1
                WHERE id = $2
                """,
                progress, task_id
            )
        
        print("✅ 任务进度更新成功")

        # UPDATE - 完成任务
        completion_time = datetime.now(timezone.utc)
        output_data = {
            'sentiment': {
                'overall_sentiment': 'positive',
                'confidence': 0.85,
                'sentiment_scores': {
                    'positive': 0.75,
                    'neutral': 0.20,
                    'negative': 0.05
                }
            },
            'entities': [
                {'text': 'Q4 2024', 'type': 'DATE', 'confidence': 0.99},
                {'text': 'revenue', 'type': 'METRIC', 'confidence': 0.92},
                {'text': 'growth', 'type': 'CONCEPT', 'confidence': 0.88}
            ],
            'summary': 'The quarterly report shows positive growth trends with strong revenue performance.',
            'processing_info': {
                'tokens_used': 1250,
                'processing_time_seconds': 85,
                'model_version': 'gpt-4-turbo-2024-01'
            }
        }
        
        actual_duration = 85
        tokens_consumed = 1250
        cost_usd = Decimal('0.0375')  # $0.0375
        
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'completed', completed_at = $1, progress_percentage = 100,
                output_data = $2, actual_duration_seconds = $3, 
                tokens_consumed = $4, cost_usd = $5
            WHERE id = $6
            """,
            completion_time, json.dumps(output_data), actual_duration,
            tokens_consumed, cost_usd, task_id
        )
        
        # 验证任务完成
        completed_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            task_id
        )
        
        assert completed_task['status'] == 'completed'
        assert completed_task['progress_percentage'] == 100
        assert completed_task['completed_at'] is not None
        assert completed_task['tokens_consumed'] == tokens_consumed
        assert completed_task['cost_usd'] == cost_usd
        print("✅ 完成AI任务成功")

        # READ - 查询任务详细信息
        task_with_output = await db_transaction.fetchrow(
            """
            SELECT t.*, 
                   u.username as user_name,
                   p.name as project_name
            FROM ai_tasks t
            JOIN users u ON t.user_id = u.id
            JOIN projects p ON t.project_id = p.id
            WHERE t.id = $1
            """,
            task_id
        )
        
        assert task_with_output is not None
        print("✅ 查询任务详细信息成功")

        # DELETE - 删除AI任务
        await db_transaction.execute(
            "DELETE FROM ai_tasks WHERE id = $1",
            task_id
        )
        
        # 验证删除
        deleted_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            task_id
        )
        
        assert deleted_task is None
        print("✅ 删除AI任务成功")

    @pytest.mark.asyncio
    async def test_ai_results_crud(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试ai_results表的完整CRUD操作"""
        # 检查表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_results')"
        )
        
        if not table_exists:
            pytest.skip("ai_results表不存在")

        # 首先创建一个AI任务
        ai_tasks_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_tasks')"
        )
        
        if not ai_tasks_exists:
            pytest.skip("ai_tasks表不存在，无法创建结果")

        # 创建测试任务
        task_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_tasks (project_id, user_id, task_name, task_type, status)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'],
            'Results Test Task', 'text_analysis', 'completed'
        )

        # CREATE - 创建AI结果
        results_data = [
            {
                'task_id': task_id,
                'result_type': 'sentiment_analysis',
                'result_data': {
                    'overall_sentiment': 'positive',
                    'sentiment_score': 0.85,
                    'confidence': 0.92,
                    'details': {
                        'positive_phrases': ['excellent performance', 'strong growth', 'successful quarter'],
                        'negative_phrases': ['minor challenges', 'room for improvement'],
                        'neutral_phrases': ['according to the data', 'in comparison to']
                    }
                },
                'confidence_score': Decimal('0.9200'),
                'quality_metrics': {
                    'accuracy': 0.95,
                    'precision': 0.89,
                    'recall': 0.91,
                    'f1_score': 0.90
                },
                'processing_time_ms': 1200,
                'model_version': 'sentiment-v2.1'
            },
            {
                'task_id': task_id,
                'result_type': 'entity_extraction',
                'result_data': {
                    'entities': [
                        {'text': 'Q4 2024', 'type': 'DATE', 'start': 15, 'end': 22, 'confidence': 0.99},
                        {'text': 'Apple Inc.', 'type': 'ORGANIZATION', 'start': 45, 'end': 55, 'confidence': 0.97},
                        {'text': '$50 billion', 'type': 'MONEY', 'start': 78, 'end': 89, 'confidence': 0.94}
                    ],
                    'entity_count': 3,
                    'coverage_ratio': 0.12
                },
                'confidence_score': Decimal('0.9500'),
                'quality_metrics': {
                    'entity_accuracy': 0.97,
                    'boundary_accuracy': 0.95,
                    'type_accuracy': 0.98
                },
                'processing_time_ms': 800,
                'model_version': 'ner-v3.0'
            },
            {
                'task_id': task_id,
                'result_type': 'text_summary',
                'result_data': {
                    'summary': 'The Q4 2024 report shows strong performance with significant revenue growth...',
                    'key_points': [
                        'Revenue increased by 15%',
                        'Customer satisfaction improved',
                        'Market expansion successful'
                    ],
                    'word_count': 45,
                    'compression_ratio': 0.08
                },
                'confidence_score': Decimal('0.8800'),
                'quality_metrics': {
                    'coherence_score': 0.92,
                    'relevance_score': 0.89,
                    'conciseness_score': 0.85
                },
                'processing_time_ms': 2100,
                'model_version': 'summarizer-v1.5'
            }
        ]
        
        result_ids = []
        for result_data in results_data:
            result_id = await db_transaction.fetchval(
                """
                INSERT INTO ai_results 
                (task_id, result_type, result_data, confidence_score, quality_metrics, 
                 processing_time_ms, model_version)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                result_data['task_id'], result_data['result_type'], 
                json.dumps(result_data['result_data']), result_data['confidence_score'],
                json.dumps(result_data['quality_metrics']), result_data['processing_time_ms'],
                result_data['model_version']
            )
            result_ids.append(result_id)
        
        print(f"✅ 创建AI结果成功: {len(result_ids)} 个结果")

        # READ - 查询单个结果
        sentiment_result = await db_transaction.fetchrow(
            "SELECT * FROM ai_results WHERE result_type = $1 AND task_id = $2",
            'sentiment_analysis', task_id
        )
        
        assert sentiment_result is not None
        assert sentiment_result['result_type'] == 'sentiment_analysis'
        assert sentiment_result['confidence_score'] == Decimal('0.9200')
        print("✅ 查询单个AI结果成功")

        # READ - 查询任务的所有结果
        all_results = await db_transaction.fetch(
            "SELECT * FROM ai_results WHERE task_id = $1 ORDER BY created_at",
            task_id
        )
        
        assert len(all_results) == 3
        print(f"✅ 查询任务所有结果: {len(all_results)} 个")

        # UPDATE - 更新结果质量指标
        updated_quality_metrics = {
            'accuracy': 0.96,
            'precision': 0.91,
            'recall': 0.93,
            'f1_score': 0.92,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db_transaction.execute(
            """
            UPDATE ai_results 
            SET quality_metrics = $1
            WHERE id = $2
            """,
            json.dumps(updated_quality_metrics), result_ids[0]
        )
        
        # 验证更新
        updated_result = await db_transaction.fetchrow(
            "SELECT * FROM ai_results WHERE id = $1",
            result_ids[0]
        )
        
        updated_metrics = json.loads(updated_result['quality_metrics'])
        assert updated_metrics['accuracy'] == 0.96
        print("✅ 更新AI结果成功")

        # READ - 性能统计查询
        performance_stats = await db_transaction.fetchrow(
            """
            SELECT 
                COUNT(*) as total_results,
                AVG(confidence_score) as avg_confidence,
                AVG(processing_time_ms) as avg_processing_time,
                MAX(confidence_score) as max_confidence,
                MIN(confidence_score) as min_confidence
            FROM ai_results 
            WHERE task_id = $1
            """,
            task_id
        )
        
        assert performance_stats['total_results'] == 3
        assert performance_stats['avg_confidence'] > 0
        print(f"✅ 性能统计查询: 平均置信度 {performance_stats['avg_confidence']:.4f}")

        # READ - 按结果类型分组查询
        results_by_type = await db_transaction.fetch(
            """
            SELECT 
                result_type,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence,
                AVG(processing_time_ms) as avg_time
            FROM ai_results 
            WHERE task_id = $1
            GROUP BY result_type
            ORDER BY result_type
            """,
            task_id
        )
        
        print(f"✅ 按类型分组查询: {len(results_by_type)} 种结果类型")
        for result_type_stats in results_by_type:
            print(f"   {result_type_stats['result_type']}: {result_type_stats['count']} 个结果")

        # DELETE - 删除特定类型的结果
        await db_transaction.execute(
            "DELETE FROM ai_results WHERE task_id = $1 AND result_type = $2",
            task_id, 'text_summary'
        )
        
        # 验证删除
        remaining_results = await db_transaction.fetch(
            "SELECT * FROM ai_results WHERE task_id = $1",
            task_id
        )
        
        assert len(remaining_results) == 2
        print("✅ 删除特定类型结果成功")

        # DELETE - 删除所有结果
        await db_transaction.execute(
            "DELETE FROM ai_results WHERE task_id = $1",
            task_id
        )
        
        # 验证删除
        deleted_results = await db_transaction.fetch(
            "SELECT * FROM ai_results WHERE task_id = $1",
            task_id
        )
        
        assert len(deleted_results) == 0
        print("✅ 删除所有AI结果成功")

    @pytest.mark.asyncio
    async def test_ai_task_workflow(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试完整的AI任务工作流程"""
        # 检查所有相关表是否存在
        required_tables = ['ai_tasks', 'ai_results']
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

        # 1. 创建任务
        task_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_tasks 
            (project_id, user_id, task_name, task_type, priority, status, 
             input_data, estimated_duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'],
            'Workflow Test Task', 'comprehensive_analysis', 'normal', 'pending',
            json.dumps({'text': 'Test document for comprehensive analysis...'}), 180
        )
        
        # 2. 开始执行任务
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'running', started_at = $1, progress_percentage = 0
            WHERE id = $2
            """,
            datetime.now(timezone.utc), task_id
        )
        
        # 3. 模拟处理进度和中间结果
        processing_stages = [
            {'progress': 20, 'stage': 'preprocessing'},
            {'progress': 40, 'stage': 'analysis'},
            {'progress': 60, 'stage': 'entity_extraction'},
            {'progress': 80, 'stage': 'sentiment_analysis'},
            {'progress': 100, 'stage': 'completed'}
        ]
        
        for stage in processing_stages:
            await db_transaction.execute(
                """
                UPDATE ai_tasks 
                SET progress_percentage = $1
                WHERE id = $2
                """,
                stage['progress'], task_id
            )
            
            # 在特定阶段添加中间结果
            if stage['progress'] == 60:
                # 添加实体提取结果
                await db_transaction.execute(
                    """
                    INSERT INTO ai_results (task_id, result_type, result_data, confidence_score)
                    VALUES ($1, $2, $3, $4)
                    """,
                    task_id, 'entity_extraction',
                    json.dumps({'entities': [{'text': 'test entity', 'type': 'TEST'}]}),
                    Decimal('0.90')
                )
            
            elif stage['progress'] == 80:
                # 添加情感分析结果
                await db_transaction.execute(
                    """
                    INSERT INTO ai_results (task_id, result_type, result_data, confidence_score)
                    VALUES ($1, $2, $3, $4)
                    """,
                    task_id, 'sentiment_analysis',
                    json.dumps({'sentiment': 'neutral', 'score': 0.5}),
                    Decimal('0.85')
                )
        
        # 4. 完成任务
        completion_time = datetime.now(timezone.utc)
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'completed', completed_at = $1, actual_duration_seconds = 175,
                tokens_consumed = 2500, cost_usd = 0.05
            WHERE id = $2
            """,
            completion_time, task_id
        )
        
        # 5. 添加最终结果
        await db_transaction.execute(
            """
            INSERT INTO ai_results (task_id, result_type, result_data, confidence_score)
            VALUES ($1, $2, $3, $4)
            """,
            task_id, 'final_summary',
            json.dumps({'summary': 'Comprehensive analysis completed successfully'}),
            Decimal('0.95')
        )
        
        # 验证工作流程结果
        final_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            task_id
        )
        
        assert final_task['status'] == 'completed'
        assert final_task['progress_percentage'] == 100
        assert final_task['completed_at'] is not None
        assert final_task['actual_duration_seconds'] == 175
        
        # 验证结果数量
        result_count = await db_transaction.fetchval(
            "SELECT COUNT(*) FROM ai_results WHERE task_id = $1",
            task_id
        )
        
        assert result_count == 3  # entity_extraction, sentiment_analysis, final_summary
        
        print(f"✅ AI任务工作流程测试完成:")
        print(f"   任务ID: {task_id}")
        print(f"   执行时间: {final_task['actual_duration_seconds']} 秒")
        print(f"   生成结果: {result_count} 个")
        print(f"   消耗token: {final_task['tokens_consumed']}")
        print(f"   成本: ${final_task['cost_usd']}")

    @pytest.mark.asyncio
    async def test_ai_task_error_handling(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试AI任务错误处理和重试机制"""
        # 检查ai_tasks表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_tasks')"
        )
        
        if not table_exists:
            pytest.skip("ai_tasks表不存在")

        # 创建会失败的任务
        failed_task_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_tasks 
            (project_id, user_id, task_name, task_type, status, max_retries)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'],
            'Error Handling Test Task', 'error_prone_analysis', 'pending', 3
        )
        
        # 模拟第一次失败
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'failed', retry_count = 1,
                error_message = 'API rate limit exceeded', 
                error_code = 'RATE_LIMIT_ERROR'
            WHERE id = $1
            """,
            failed_task_id
        )
        
        # 模拟第二次失败
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'failed', retry_count = 2,
                error_message = 'Model temporarily unavailable',
                error_code = 'MODEL_UNAVAILABLE'
            WHERE id = $1
            """,
            failed_task_id
        )
        
        # 模拟第三次成功
        await db_transaction.execute(
            """
            UPDATE ai_tasks 
            SET status = 'completed', retry_count = 3,
                error_message = NULL, error_code = NULL,
                completed_at = $1, actual_duration_seconds = 95
            WHERE id = $2
            """,
            datetime.now(timezone.utc), failed_task_id
        )
        
        # 验证重试处理
        retry_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            failed_task_id
        )
        
        assert retry_task['status'] == 'completed'
        assert retry_task['retry_count'] == 3
        assert retry_task['error_message'] is None
        
        # 创建超过最大重试次数的任务
        max_retry_task_id = await db_transaction.fetchval(
            """
            INSERT INTO ai_tasks 
            (project_id, user_id, task_name, task_type, status, max_retries)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            sample_project_in_db['id'], sample_user_in_db['id'],
            'Max Retry Test Task', 'unstable_analysis', 'pending', 2
        )
        
        # 模拟达到最大重试次数
        for retry_num in range(1, 4):  # 重试3次，超过max_retries=2
            status = 'failed' if retry_num <= 2 else 'failed'  # 最后一次仍然失败
            await db_transaction.execute(
                """
                UPDATE ai_tasks 
                SET status = $1, retry_count = $2,
                    error_message = $3, error_code = 'PERSISTENT_ERROR'
                WHERE id = $4
                """,
                status, retry_num, f'Retry {retry_num} failed', max_retry_task_id
            )
        
        # 验证最大重试处理
        max_retry_task = await db_transaction.fetchrow(
            "SELECT * FROM ai_tasks WHERE id = $1",
            max_retry_task_id
        )
        
        assert max_retry_task['status'] == 'failed'
        assert max_retry_task['retry_count'] == 3
        assert max_retry_task['error_message'] is not None
        
        print(f"✅ AI任务错误处理测试:")
        print(f"   重试成功任务: retry_count = {retry_task['retry_count']}")
        print(f"   最大重试任务: retry_count = {max_retry_task['retry_count']}, status = {max_retry_task['status']}")

    @pytest.mark.asyncio
    async def test_ai_task_performance_metrics(self, db_transaction: asyncpg.Connection, sample_user_in_db, sample_project_in_db):
        """测试AI任务性能指标统计"""
        # 检查ai_tasks表是否存在
        table_exists = await db_transaction.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_tasks')"
        )
        
        if not table_exists:
            pytest.skip("ai_tasks表不存在")

        # 创建多个不同状态和类型的任务进行统计
        task_types = ['text_analysis', 'image_analysis', 'data_processing']
        priorities = ['low', 'normal', 'high']
        statuses = ['completed', 'completed', 'completed', 'failed', 'pending']
        
        created_tasks = []
        for i in range(15):  # 创建15个任务
            task_type = task_types[i % len(task_types)]
            priority = priorities[i % len(priorities)]
            status = statuses[i % len(statuses)]
            
            # 基于状态设置不同的数值
            if status == 'completed':
                duration = 60 + (i * 10)  # 60-200秒
                tokens = 1000 + (i * 100)  # 1000-2400 tokens
                cost = round(0.01 + (i * 0.005), 4)  # $0.01-$0.08
                completed_at = datetime.now(timezone.utc)
            else:
                duration = None
                tokens = None
                cost = None
                completed_at = None
            
            task_id = await db_transaction.fetchval(
                """
                INSERT INTO ai_tasks 
                (project_id, user_id, task_name, task_type, priority, status,
                 actual_duration_seconds, tokens_consumed, cost_usd, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
                """,
                sample_project_in_db['id'], sample_user_in_db['id'],
                f'Metrics Test Task {i}', task_type, priority, status,
                duration, tokens, cost, completed_at
            )
            created_tasks.append(task_id)
        
        # 1. 总体统计
        overall_stats = await db_transaction.fetchrow(
            """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
                AVG(CASE WHEN actual_duration_seconds IS NOT NULL THEN actual_duration_seconds END) as avg_duration,
                SUM(CASE WHEN tokens_consumed IS NOT NULL THEN tokens_consumed END) as total_tokens,
                SUM(CASE WHEN cost_usd IS NOT NULL THEN cost_usd END) as total_cost
            FROM ai_tasks 
            WHERE project_id = $1
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 总体统计:")
        print(f"   总任务数: {overall_stats['total_tasks']}")
        print(f"   完成任务: {overall_stats['completed_tasks']}")
        print(f"   失败任务: {overall_stats['failed_tasks']}")
        print(f"   等待任务: {overall_stats['pending_tasks']}")
        print(f"   平均执行时间: {overall_stats['avg_duration']:.1f}秒")
        print(f"   总token消耗: {overall_stats['total_tokens']}")
        print(f"   总成本: ${overall_stats['total_cost']:.4f}")

        # 2. 按任务类型统计
        type_stats = await db_transaction.fetch(
            """
            SELECT 
                task_type,
                COUNT(*) as task_count,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                AVG(CASE WHEN actual_duration_seconds IS NOT NULL THEN actual_duration_seconds END) as avg_duration,
                AVG(CASE WHEN tokens_consumed IS NOT NULL THEN tokens_consumed END) as avg_tokens,
                SUM(CASE WHEN cost_usd IS NOT NULL THEN cost_usd END) as total_cost
            FROM ai_tasks 
            WHERE project_id = $1
            GROUP BY task_type
            ORDER BY task_count DESC
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 按类型统计:")
        for stat in type_stats:
            print(f"   {stat['task_type']}: {stat['task_count']}个任务, 完成{stat['completed_count']}个")

        # 3. 按优先级统计
        priority_stats = await db_transaction.fetch(
            """
            SELECT 
                priority,
                COUNT(*) as task_count,
                AVG(CASE WHEN actual_duration_seconds IS NOT NULL THEN actual_duration_seconds END) as avg_duration
            FROM ai_tasks 
            WHERE project_id = $1
            GROUP BY priority
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'normal' THEN 2 
                    WHEN 'low' THEN 3 
                END
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 按优先级统计:")
        for stat in priority_stats:
            avg_dur = stat['avg_duration'] if stat['avg_duration'] else 0
            print(f"   {stat['priority']}: {stat['task_count']}个任务, 平均耗时{avg_dur:.1f}秒")

        # 4. 成功率统计
        success_rate = await db_transaction.fetchrow(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                ROUND(
                    COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / 
                    NULLIF(COUNT(*), 0) * 100, 2
                ) as success_rate_percent
            FROM ai_tasks 
            WHERE project_id = $1 AND status IN ('completed', 'failed')
            """,
            sample_project_in_db['id']
        )
        
        print(f"✅ 成功率统计:")
        print(f"   总处理任务: {success_rate['total']}")
        print(f"   成功任务: {success_rate['completed']}")
        print(f"   成功率: {success_rate['success_rate_percent']}%")

        # 验证统计数据的合理性
        assert overall_stats['total_tasks'] >= 15
        assert overall_stats['completed_tasks'] > 0
        assert overall_stats['avg_duration'] > 0
        assert len(type_stats) == 3  # 三种任务类型
        assert len(priority_stats) == 3  # 三种优先级