"""
数据库测试数据固件生成器

提供可重复的测试数据生成和管理功能
"""

import json
import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class UserFixture:
    """用户数据固件"""
    email: str
    username: str
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = 'UTC'
    language: str = 'en'


@dataclass
class ProjectFixture:
    """项目数据固件"""
    name: str
    slug: str
    description: Optional[str] = None
    status: str = 'active'
    visibility: str = 'private'
    settings: Optional[Dict] = None
    tags: Optional[List[str]] = None


@dataclass
class AITaskFixture:
    """AI任务数据固件"""
    task_name: str
    task_type: str
    priority: str = 'normal'
    status: str = 'pending'
    input_data: Optional[Dict] = None
    progress_percentage: int = 0
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class FileFixture:
    """文件数据固件"""
    file_name: str
    original_name: str
    file_path: str
    file_hash: str
    file_size: int
    mime_type: str
    storage_type: str = 'local'
    upload_status: str = 'completed'
    is_public: bool = False


class DatabaseFixtureGenerator:
    """数据库测试数据生成器"""
    
    def __init__(self, seed: int = 42):
        """初始化生成器
        
        Args:
            seed: 随机数种子，确保可重复性
        """
        random.seed(seed)
        self.seed = seed
    
    def generate_random_string(self, length: int = 10, charset: str = None) -> str:
        """生成随机字符串"""
        if charset is None:
            charset = string.ascii_lowercase + string.digits
        return ''.join(random.choices(charset, k=length))
    
    def generate_email(self, domain: str = 'saascontrol-test.com') -> str:
        """生成测试邮箱"""
        username = self.generate_random_string(8)
        return f"{username}@{domain}"
    
    def generate_phone(self) -> str:
        """生成测试电话号码"""
        area_code = random.randint(100, 999)
        number = random.randint(1000000, 9999999)
        return f"+1{area_code}{number}"
    
    def generate_password_hash(self) -> str:
        """生成密码哈希（模拟）"""
        return f"$2b$12${''.join(random.choices(string.ascii_letters + string.digits + './', k=53))}"
    
    def generate_file_hash(self) -> str:
        """生成文件哈希"""
        return ''.join(random.choices(string.hexdigits.lower(), k=64))
    
    def generate_slug(self, name: str) -> str:
        """从名称生成slug"""
        slug_base = name.lower().replace(' ', '-').replace('_', '-')
        # 移除非字母数字和连字符的字符
        slug = ''.join(c for c in slug_base if c.isalnum() or c == '-')
        # 添加随机后缀确保唯一性
        suffix = self.generate_random_string(4)
        return f"{slug}-{suffix}"
    
    def generate_uuid(self) -> str:
        """生成UUID"""
        return str(uuid.uuid4())
    
    def generate_user_fixture(self, 
                            email: Optional[str] = None,
                            username: Optional[str] = None,
                            **kwargs) -> UserFixture:
        """生成用户固件"""
        if email is None:
            email = self.generate_email()
        
        if username is None:
            username = f"user_{self.generate_random_string(6)}"
        
        # 生成姓名
        first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        display_name = f"{first_name} {last_name}"
        
        return UserFixture(
            email=email,
            username=username,
            password_hash=self.generate_password_hash(),
            is_active=kwargs.get('is_active', True),
            is_verified=kwargs.get('is_verified', random.choice([True, False])),
            first_name=kwargs.get('first_name', first_name),
            last_name=kwargs.get('last_name', last_name),
            display_name=kwargs.get('display_name', display_name),
            phone=kwargs.get('phone', self.generate_phone() if random.random() > 0.3 else None),
            timezone=kwargs.get('timezone', random.choice(['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'])),
            language=kwargs.get('language', random.choice(['en', 'es', 'fr', 'de', 'zh']))
        )
    
    def generate_project_fixture(self,
                               name: Optional[str] = None,
                               slug: Optional[str] = None,
                               **kwargs) -> ProjectFixture:
        """生成项目固件"""
        project_names = [
            'AI Data Analysis Platform',
            'Customer Insights Dashboard',
            'Marketing Analytics Tool',
            'Sales Performance Tracker',
            'User Behavior Analysis',
            'Financial Report Generator',
            'Inventory Management System',
            'Content Management Platform'
        ]
        
        if name is None:
            name = random.choice(project_names)
        
        if slug is None:
            slug = self.generate_slug(name)
        
        # 生成项目描述
        descriptions = [
            'A comprehensive platform for analyzing business data using advanced AI algorithms.',
            'Real-time dashboard providing insights into customer behavior and preferences.',
            'Tool for tracking and optimizing marketing campaign performance.',
            'System for monitoring sales metrics and team performance.',
            'Platform for understanding user interactions and engagement patterns.'
        ]
        
        # 生成设置
        settings = {
            'ai_features_enabled': random.choice([True, False]),
            'data_retention_days': random.choice([30, 60, 90, 180, 365]),
            'auto_backup_enabled': random.choice([True, False]),
            'collaboration_enabled': random.choice([True, False]),
            'max_file_size_mb': random.choice([10, 50, 100, 500]),
            'allowed_file_types': random.choice([
                ['csv', 'json', 'xlsx'],
                ['csv', 'json', 'xlsx', 'pdf', 'txt'],
                ['json', 'xml', 'csv']
            ])
        }
        
        # 生成标签
        all_tags = ['analytics', 'dashboard', 'ai', 'ml', 'data', 'business', 'finance', 'marketing', 'sales', 'crm']
        tag_count = random.randint(1, 4)
        tags = random.sample(all_tags, tag_count)
        
        return ProjectFixture(
            name=name,
            slug=slug,
            description=kwargs.get('description', random.choice(descriptions)),
            status=kwargs.get('status', random.choice(['active', 'inactive'])),
            visibility=kwargs.get('visibility', random.choice(['private', 'internal', 'public'])),
            settings=kwargs.get('settings', settings),
            tags=kwargs.get('tags', tags)
        )
    
    def generate_ai_task_fixture(self,
                               task_name: Optional[str] = None,
                               task_type: Optional[str] = None,
                               **kwargs) -> AITaskFixture:
        """生成AI任务固件"""
        task_types = ['text_analysis', 'image_recognition', 'data_processing', 'sentiment_analysis', 
                     'entity_extraction', 'classification', 'prediction', 'clustering']
        
        if task_type is None:
            task_type = random.choice(task_types)
        
        if task_name is None:
            task_names = [
                f'{task_type.replace("_", " ").title()} Task',
                f'Automated {task_type.replace("_", " ").title()}',
                f'AI-powered {task_type.replace("_", " ").title()}'
            ]
            task_name = random.choice(task_names)
        
        # 生成输入数据
        input_data = None
        if task_type == 'text_analysis':
            input_data = {
                'text': 'Sample text for analysis. This is a comprehensive document that needs to be processed.',
                'language': 'en',
                'analysis_type': random.choice(['sentiment', 'entities', 'keywords', 'summary'])
            }
        elif task_type == 'image_recognition':
            input_data = {
                'image_url': f'https://example.com/images/{self.generate_random_string(10)}.jpg',
                'detection_type': random.choice(['objects', 'faces', 'text', 'landmarks'])
            }
        elif task_type == 'data_processing':
            input_data = {
                'data_source': f'data_source_{self.generate_random_string(8)}',
                'processing_type': random.choice(['cleaning', 'transformation', 'aggregation']),
                'parameters': {'threshold': random.uniform(0.1, 0.9)}
            }
        
        return AITaskFixture(
            task_name=task_name,
            task_type=task_type,
            priority=kwargs.get('priority', random.choice(['low', 'normal', 'high', 'urgent'])),
            status=kwargs.get('status', random.choice(['pending', 'running', 'completed', 'failed'])),
            input_data=kwargs.get('input_data', input_data),
            progress_percentage=kwargs.get('progress_percentage', random.randint(0, 100) if kwargs.get('status') != 'pending' else 0),
            retry_count=kwargs.get('retry_count', random.randint(0, 2)),
            max_retries=kwargs.get('max_retries', 3)
        )
    
    def generate_file_fixture(self,
                            file_name: Optional[str] = None,
                            mime_type: Optional[str] = None,
                            **kwargs) -> FileFixture:
        """生成文件固件"""
        # 文件类型和对应的MIME类型
        file_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'mp4': 'video/mp4',
            'zip': 'application/zip'
        }
        
        if file_name is None:
            extension = random.choice(list(file_types.keys()))
            base_names = [
                'data_export', 'user_report', 'analysis_results', 'customer_data',
                'sales_report', 'marketing_metrics', 'financial_summary', 'project_files'
            ]
            base_name = random.choice(base_names)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"{base_name}_{timestamp}.{extension}"
            
            if mime_type is None:
                mime_type = file_types[extension]
        
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        # 生成文件大小（基于文件类型）
        size_ranges = {
            'text/csv': (1000, 50000),
            'application/json': (500, 25000),
            'application/pdf': (10000, 1000000),
            'image/png': (5000, 500000),
            'image/jpeg': (3000, 300000),
            'video/mp4': (1000000, 50000000),
            'application/zip': (10000, 10000000)
        }
        
        size_range = size_ranges.get(mime_type, (1000, 100000))
        file_size = random.randint(*size_range)
        
        return FileFixture(
            file_name=file_name,
            original_name=kwargs.get('original_name', file_name),
            file_path=kwargs.get('file_path', f"/storage/{file_name}"),
            file_hash=kwargs.get('file_hash', self.generate_file_hash()),
            file_size=kwargs.get('file_size', file_size),
            mime_type=mime_type,
            storage_type=kwargs.get('storage_type', random.choice(['local', 's3', 'minio', 'gcs'])),
            upload_status=kwargs.get('upload_status', 'completed'),
            is_public=kwargs.get('is_public', random.choice([True, False]))
        )
    
    def generate_bulk_users(self, count: int) -> List[UserFixture]:
        """生成批量用户数据"""
        users = []
        for i in range(count):
            user = self.generate_user_fixture(
                email=f"bulk_user_{i:04d}@saascontrol-test.com",
                username=f"bulk_user_{i:04d}"
            )
            users.append(user)
        return users
    
    def generate_bulk_projects(self, count: int) -> List[ProjectFixture]:
        """生成批量项目数据"""
        projects = []
        for i in range(count):
            project = self.generate_project_fixture(
                name=f"Test Project {i:04d}"
            )
            projects.append(project)
        return projects
    
    def generate_realistic_dataset(self) -> Dict[str, Any]:
        """生成真实场景的数据集"""
        # 生成用户群体
        users = []
        
        # 管理员用户
        admin_user = self.generate_user_fixture(
            email='admin@saascontrol-test.com',
            username='admin',
            is_active=True,
            is_verified=True
        )
        users.append(admin_user)
        
        # 普通活跃用户
        for i in range(20):
            user = self.generate_user_fixture(
                is_active=True,
                is_verified=random.choice([True, False])
            )
            users.append(user)
        
        # 非活跃用户
        for i in range(5):
            user = self.generate_user_fixture(
                is_active=False,
                is_verified=random.choice([True, False])
            )
            users.append(user)
        
        # 生成项目
        projects = []
        
        # 每个活跃用户创建1-3个项目
        active_users = [u for u in users if u.is_active]
        for user in active_users[:15]:  # 前15个活跃用户
            project_count = random.randint(1, 3)
            for _ in range(project_count):
                project = self.generate_project_fixture()
                projects.append(project)
        
        # 生成AI任务
        ai_tasks = []
        
        # 每个项目生成0-10个任务
        for project in projects:
            task_count = random.randint(0, 10)
            for _ in range(task_count):
                task = self.generate_ai_task_fixture()
                ai_tasks.append(task)
        
        # 生成文件
        files = []
        
        # 每个项目生成0-20个文件
        for project in projects:
            file_count = random.randint(0, 20)
            for _ in range(file_count):
                file = self.generate_file_fixture()
                files.append(file)
        
        return {
            'users': users,
            'projects': projects,
            'ai_tasks': ai_tasks,
            'files': files,
            'stats': {
                'total_users': len(users),
                'active_users': len([u for u in users if u.is_active]),
                'total_projects': len(projects),
                'total_tasks': len(ai_tasks),
                'total_files': len(files)
            }
        }


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self, generator: DatabaseFixtureGenerator):
        self.generator = generator
        self.created_data = {
            'users': [],
            'projects': [],
            'ai_tasks': [],
            'files': []
        }
    
    async def create_user_in_db(self, connection, user_fixture: UserFixture) -> str:
        """在数据库中创建用户"""
        user_id = await connection.fetchval(
            """
            INSERT INTO users (email, username, password_hash, is_active, is_verified)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            user_fixture.email, user_fixture.username, user_fixture.password_hash,
            user_fixture.is_active, user_fixture.is_verified
        )
        
        # 创建用户档案（如果表存在）
        try:
            await connection.execute(
                """
                INSERT INTO user_profiles 
                (user_id, first_name, last_name, display_name, phone, timezone, language)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id, user_fixture.first_name, user_fixture.last_name,
                user_fixture.display_name, user_fixture.phone,
                user_fixture.timezone, user_fixture.language
            )
        except:
            pass  # 表可能不存在
        
        self.created_data['users'].append(user_id)
        return user_id
    
    async def create_project_in_db(self, connection, project_fixture: ProjectFixture, owner_id: str) -> str:
        """在数据库中创建项目"""
        project_id = await connection.fetchval(
            """
            INSERT INTO projects (name, slug, description, owner_id, status, visibility, settings, tags)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            project_fixture.name, project_fixture.slug, project_fixture.description,
            owner_id, project_fixture.status, project_fixture.visibility,
            json.dumps(project_fixture.settings), project_fixture.tags
        )
        
        self.created_data['projects'].append(project_id)
        return project_id
    
    async def create_ai_task_in_db(self, connection, task_fixture: AITaskFixture, 
                                 project_id: str, user_id: str) -> str:
        """在数据库中创建AI任务"""
        task_id = await connection.fetchval(
            """
            INSERT INTO ai_tasks 
            (project_id, user_id, task_name, task_type, priority, status, 
             input_data, progress_percentage, retry_count, max_retries)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            project_id, user_id, task_fixture.task_name, task_fixture.task_type,
            task_fixture.priority, task_fixture.status,
            json.dumps(task_fixture.input_data), task_fixture.progress_percentage,
            task_fixture.retry_count, task_fixture.max_retries
        )
        
        self.created_data['ai_tasks'].append(task_id)
        return task_id
    
    async def create_file_in_db(self, connection, file_fixture: FileFixture,
                              project_id: str, user_id: str) -> str:
        """在数据库中创建文件记录"""
        file_id = await connection.fetchval(
            """
            INSERT INTO file_storage 
            (project_id, user_id, file_name, original_name, file_path, file_hash,
             file_size, mime_type, storage_type, upload_status, is_public)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            project_id, user_id, file_fixture.file_name, file_fixture.original_name,
            file_fixture.file_path, file_fixture.file_hash, file_fixture.file_size,
            file_fixture.mime_type, file_fixture.storage_type,
            file_fixture.upload_status, file_fixture.is_public
        )
        
        self.created_data['files'].append(file_id)
        return file_id
    
    async def cleanup_test_data(self, connection):
        """清理测试数据"""
        # 按依赖关系倒序删除
        cleanup_order = [
            ('ai_tasks', 'ai_tasks'),
            ('files', 'file_storage'),
            ('projects', 'projects'),
            ('users', 'users')
        ]
        
        for data_type, table_name in cleanup_order:
            if self.created_data[data_type]:
                try:
                    placeholders = ','.join(['$' + str(i+1) for i in range(len(self.created_data[data_type]))])
                    await connection.execute(
                        f"DELETE FROM {table_name} WHERE id IN ({placeholders})",
                        *self.created_data[data_type]
                    )
                except Exception as e:
                    print(f"清理 {table_name} 时出错: {e}")
        
        # 清空记录
        for data_type in self.created_data:
            self.created_data[data_type].clear()


def get_fixture_generator(seed: int = None) -> DatabaseFixtureGenerator:
    """获取固件生成器实例"""
    if seed is None:
        seed = int(datetime.now().timestamp()) % 10000
    return DatabaseFixtureGenerator(seed=seed)


def get_test_data_manager(seed: int = None) -> TestDataManager:
    """获取测试数据管理器实例"""
    generator = get_fixture_generator(seed)
    return TestDataManager(generator)