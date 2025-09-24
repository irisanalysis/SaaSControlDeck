# 数据质量评估算法框架设计
## Data Quality Assessment Algorithm Framework

**文档版本**: v1.0
**创建时间**: 2025-09-20
**负责人**: Analytics Reporter
**项目**: SaaS Control Deck - Data Management Module

---

## 📋 概述

本文档定义了SaaS Control Deck平台数据管理功能的核心算法框架，涵盖数据质量评估的4个维度：完整性、一致性、准确性、时效性。所有算法设计面向6天开发周期，确保技术可行性和实现效率。

---

## 🎯 算法设计原则

### 性能约束
- **处理时间**: 中等数据集(10K-100K行) < 30秒
- **文件大小**: 支持最大100MB数据文件
- **内存使用**: 单次分析 < 2GB RAM
- **并发支持**: 最多5个并发分析任务

### 技术栈集成
- **后端框架**: FastAPI + asyncio异步处理
- **数据处理**: pandas + numpy + scikit-learn
- **数据库**: PostgreSQL存储分析结果
- **AI集成**: OpenAI API进行智能分析
- **缓存**: Redis缓存计算结果

---

## 🔍 算法架构总览

```python
class DataQualityFramework:
    """数据质量评估核心框架"""

    def __init__(self):
        self.analyzers = {
            'completeness': CompletenessAnalyzer(),
            'consistency': ConsistencyAnalyzer(),
            'accuracy': AccuracyAnalyzer(),
            'timeliness': TimelinessAnalyzer()
        }

    async def analyze(self, dataset: pd.DataFrame) -> QualityReport:
        """执行完整的数据质量分析"""
        results = {}

        # 并行执行各维度分析
        tasks = [
            self.analyze_completeness(dataset),
            self.analyze_consistency(dataset),
            self.analyze_accuracy(dataset),
            self.analyze_timeliness(dataset)
        ]

        completeness, consistency, accuracy, timeliness = await asyncio.gather(*tasks)

        # 生成综合评分
        overall_score = self.calculate_composite_score(
            completeness, consistency, accuracy, timeliness
        )

        return QualityReport(
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            timeliness=timeliness,
            overall_score=overall_score,
            recommendations=await self.generate_ai_recommendations(results)
        )
```

---

## 📊 维度1: 完整性分析 (Completeness Analysis)

### 核心指标
- **缺失值比例**: Missing value percentage per column
- **空值模式**: Empty string, null, undefined patterns
- **必填字段**: Required field validation
- **记录完整度**: Row-level completeness score

### 算法实现

```python
class CompletenessAnalyzer:
    """数据完整性分析器"""

    def __init__(self):
        self.null_patterns = [None, '', 'NULL', 'null', 'N/A', 'n/a', '#N/A']
        self.numeric_null_patterns = [-999, -9999, 999999]

    async def analyze(self, df: pd.DataFrame) -> CompletenessResult:
        """执行完整性分析"""

        results = {}

        for column in df.columns:
            column_analysis = await self._analyze_column_completeness(df[column])
            results[column] = column_analysis

        # 计算整体完整性得分
        overall_score = self._calculate_completeness_score(results)

        # 识别关键问题
        critical_issues = self._identify_critical_issues(results)

        return CompletenessResult(
            column_results=results,
            overall_score=overall_score,
            critical_issues=critical_issues,
            recommendations=self._generate_completeness_recommendations(results)
        )

    async def _analyze_column_completeness(self, series: pd.Series) -> dict:
        """单列完整性分析"""

        total_count = len(series)

        # 标准null值检测
        null_count = series.isnull().sum()

        # 扩展null值模式检测
        extended_null_count = sum([
            (series == pattern).sum() for pattern in self.null_patterns
        ])

        # 数值类型特殊null值检测
        if pd.api.types.is_numeric_dtype(series):
            numeric_null_count = sum([
                (series == pattern).sum() for pattern in self.numeric_null_patterns
            ])
            extended_null_count += numeric_null_count

        # 空白字符串检测
        if pd.api.types.is_string_dtype(series):
            whitespace_count = series.str.strip().eq('').sum()
            extended_null_count += whitespace_count

        # 计算完整性得分
        completeness_rate = (total_count - extended_null_count) / total_count

        return {
            'total_count': total_count,
            'null_count': null_count,
            'extended_null_count': extended_null_count,
            'completeness_rate': completeness_rate,
            'completeness_score': self._rate_to_score(completeness_rate),
            'data_type': str(series.dtype),
            'unique_count': series.nunique(),
            'null_patterns_found': self._identify_null_patterns(series)
        }

    def _rate_to_score(self, rate: float) -> int:
        """完整性比率转换为评分(0-100)"""
        if rate >= 0.95:
            return 100
        elif rate >= 0.90:
            return 85
        elif rate >= 0.80:
            return 70
        elif rate >= 0.70:
            return 55
        elif rate >= 0.50:
            return 40
        else:
            return max(0, int(rate * 50))
```

### 评分标准
```python
COMPLETENESS_SCORING = {
    'excellent': {'threshold': 0.95, 'score': 90-100},
    'good': {'threshold': 0.90, 'score': 80-89},
    'fair': {'threshold': 0.80, 'score': 70-79},
    'poor': {'threshold': 0.70, 'score': 50-69},
    'critical': {'threshold': 0.50, 'score': 0-49}
}
```

---

## 🔧 维度2: 一致性分析 (Consistency Analysis)

### 核心指标
- **数据类型一致性**: Data type consistency across columns
- **格式一致性**: Format pattern consistency (dates, emails, phone)
- **取值范围一致性**: Value range and constraint validation
- **关联一致性**: Cross-column relationship validation

### 算法实现

```python
class ConsistencyAnalyzer:
    """数据一致性分析器"""

    def __init__(self):
        self.pattern_validators = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9][\d]{0,15}$',
            'url': r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$',
            'date_iso': r'^\d{4}-\d{2}-\d{2}$',
            'numeric_id': r'^\d+$'
        }

    async def analyze(self, df: pd.DataFrame) -> ConsistencyResult:
        """执行一致性分析"""

        results = {}

        # 1. 数据类型一致性分析
        type_consistency = await self._analyze_type_consistency(df)

        # 2. 格式模式一致性分析
        format_consistency = await self._analyze_format_consistency(df)

        # 3. 取值范围一致性分析
        range_consistency = await self._analyze_range_consistency(df)

        # 4. 关联一致性分析
        relationship_consistency = await self._analyze_relationship_consistency(df)

        # 计算综合一致性得分
        overall_score = self._calculate_consistency_score(
            type_consistency, format_consistency,
            range_consistency, relationship_consistency
        )

        return ConsistencyResult(
            type_consistency=type_consistency,
            format_consistency=format_consistency,
            range_consistency=range_consistency,
            relationship_consistency=relationship_consistency,
            overall_score=overall_score,
            recommendations=self._generate_consistency_recommendations(results)
        )

    async def _analyze_format_consistency(self, df: pd.DataFrame) -> dict:
        """格式一致性分析"""

        results = {}

        for column in df.columns:
            if pd.api.types.is_string_dtype(df[column]):
                # 自动检测列的可能格式类型
                detected_format = self._detect_column_format(df[column])

                if detected_format:
                    # 验证格式一致性
                    pattern = self.pattern_validators[detected_format]
                    valid_count = df[column].str.match(pattern, na=False).sum()
                    total_count = df[column].notna().sum()

                    consistency_rate = valid_count / total_count if total_count > 0 else 0

                    results[column] = {
                        'detected_format': detected_format,
                        'valid_count': valid_count,
                        'total_count': total_count,
                        'consistency_rate': consistency_rate,
                        'consistency_score': self._rate_to_score(consistency_rate),
                        'invalid_samples': self._get_invalid_samples(df[column], pattern)
                    }

        return results

    def _detect_column_format(self, series: pd.Series) -> str:
        """自动检测列的数据格式类型"""

        # 获取非空样本
        samples = series.dropna().head(100).astype(str)

        if len(samples) == 0:
            return None

        # 格式检测优先级
        format_scores = {}

        for format_name, pattern in self.pattern_validators.items():
            matches = samples.str.match(pattern).sum()
            score = matches / len(samples)
            format_scores[format_name] = score

        # 返回匹配度最高的格式（阈值0.8）
        best_format = max(format_scores, key=format_scores.get)
        if format_scores[best_format] >= 0.8:
            return best_format

        return None
```

---

## 🎯 维度3: 准确性分析 (Accuracy Analysis)

### 核心指标
- **异常值检测**: Statistical outlier detection
- **数据分布分析**: Distribution analysis and anomaly detection
- **业务规则验证**: Domain-specific validation rules
- **参照完整性**: Reference data validation

### 算法实现

```python
class AccuracyAnalyzer:
    """数据准确性分析器"""

    def __init__(self):
        self.outlier_methods = ['iqr', 'zscore', 'isolation_forest']
        self.business_rules = {}

    async def analyze(self, df: pd.DataFrame) -> AccuracyResult:
        """执行准确性分析"""

        results = {}

        # 1. 统计异常值检测
        outlier_analysis = await self._analyze_outliers(df)

        # 2. 数据分布分析
        distribution_analysis = await self._analyze_distributions(df)

        # 3. 业务规则验证
        business_rule_analysis = await self._analyze_business_rules(df)

        # 4. 参照完整性检查
        reference_integrity = await self._analyze_reference_integrity(df)

        # 计算综合准确性得分
        overall_score = self._calculate_accuracy_score(
            outlier_analysis, distribution_analysis,
            business_rule_analysis, reference_integrity
        )

        return AccuracyResult(
            outlier_analysis=outlier_analysis,
            distribution_analysis=distribution_analysis,
            business_rule_analysis=business_rule_analysis,
            reference_integrity=reference_integrity,
            overall_score=overall_score,
            recommendations=self._generate_accuracy_recommendations(results)
        )

    async def _analyze_outliers(self, df: pd.DataFrame) -> dict:
        """异常值检测分析"""

        results = {}

        numeric_columns = df.select_dtypes(include=[np.number]).columns

        for column in numeric_columns:
            series = df[column].dropna()

            if len(series) < 10:  # 数据量太少跳过
                continue

            # 多方法异常值检测
            outlier_results = {}

            # 1. IQR方法
            outlier_results['iqr'] = self._detect_outliers_iqr(series)

            # 2. Z-Score方法
            outlier_results['zscore'] = self._detect_outliers_zscore(series)

            # 3. Isolation Forest方法
            outlier_results['isolation_forest'] = self._detect_outliers_isolation_forest(series)

            # 综合异常值判断
            consensus_outliers = self._get_consensus_outliers(outlier_results)

            outlier_rate = len(consensus_outliers) / len(series)
            accuracy_score = max(0, 100 - outlier_rate * 100)

            results[column] = {
                'total_count': len(series),
                'outlier_count': len(consensus_outliers),
                'outlier_rate': outlier_rate,
                'accuracy_score': accuracy_score,
                'outlier_indices': consensus_outliers.tolist(),
                'outlier_values': series.iloc[consensus_outliers].tolist(),
                'detection_methods': outlier_results,
                'statistics': {
                    'mean': float(series.mean()),
                    'median': float(series.median()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'max': float(series.max())
                }
            }

        return results

    def _detect_outliers_iqr(self, series: pd.Series, factor: float = 1.5) -> np.ndarray:
        """IQR方法检测异常值"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR

        outlier_mask = (series < lower_bound) | (series > upper_bound)
        return np.where(outlier_mask)[0]

    def _detect_outliers_zscore(self, series: pd.Series, threshold: float = 3.0) -> np.ndarray:
        """Z-Score方法检测异常值"""
        z_scores = np.abs((series - series.mean()) / series.std())
        outlier_mask = z_scores > threshold
        return np.where(outlier_mask)[0]

    def _detect_outliers_isolation_forest(self, series: pd.Series, contamination: float = 0.1) -> np.ndarray:
        """Isolation Forest方法检测异常值"""
        from sklearn.ensemble import IsolationForest

        # 重塑数据为二维数组
        data = series.values.reshape(-1, 1)

        # 训练Isolation Forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        outlier_labels = iso_forest.fit_predict(data)

        # 返回异常值索引（-1表示异常值）
        return np.where(outlier_labels == -1)[0]
```

---

## ⏰ 维度4: 时效性分析 (Timeliness Analysis)

### 核心指标
- **数据新鲜度**: Data freshness and update frequency
- **时间戳一致性**: Timestamp validation and consistency
- **时序完整性**: Time series completeness and gaps
- **业务时效性**: Business-specific timeliness requirements

### 算法实现

```python
class TimelinessAnalyzer:
    """数据时效性分析器"""

    def __init__(self):
        self.datetime_patterns = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]

    async def analyze(self, df: pd.DataFrame) -> TimelinessResult:
        """执行时效性分析"""

        results = {}

        # 1. 识别时间列
        datetime_columns = self._identify_datetime_columns(df)

        # 2. 数据新鲜度分析
        freshness_analysis = await self._analyze_data_freshness(df, datetime_columns)

        # 3. 时间戳一致性分析
        timestamp_consistency = await self._analyze_timestamp_consistency(df, datetime_columns)

        # 4. 时序完整性分析
        temporal_completeness = await self._analyze_temporal_completeness(df, datetime_columns)

        # 计算综合时效性得分
        overall_score = self._calculate_timeliness_score(
            freshness_analysis, timestamp_consistency, temporal_completeness
        )

        return TimelinessResult(
            datetime_columns=datetime_columns,
            freshness_analysis=freshness_analysis,
            timestamp_consistency=timestamp_consistency,
            temporal_completeness=temporal_completeness,
            overall_score=overall_score,
            recommendations=self._generate_timeliness_recommendations(results)
        )

    def _identify_datetime_columns(self, df: pd.DataFrame) -> list:
        """识别数据集中的时间列"""

        datetime_columns = []

        for column in df.columns:
            # 检查列名是否包含时间相关关键词
            if any(keyword in column.lower() for keyword in
                   ['time', 'date', 'created', 'updated', 'modified', 'timestamp']):
                datetime_columns.append(column)
                continue

            # 检查数据类型
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                datetime_columns.append(column)
                continue

            # 尝试解析为时间格式
            if self._can_parse_as_datetime(df[column]):
                datetime_columns.append(column)

        return datetime_columns

    async def _analyze_data_freshness(self, df: pd.DataFrame, datetime_columns: list) -> dict:
        """数据新鲜度分析"""

        results = {}
        current_time = datetime.now()

        for column in datetime_columns:
            # 转换为datetime类型
            datetime_series = pd.to_datetime(df[column], errors='coerce')
            valid_dates = datetime_series.dropna()

            if len(valid_dates) == 0:
                continue

            # 计算数据新鲜度指标
            latest_date = valid_dates.max()
            oldest_date = valid_dates.min()

            # 数据年龄（天）
            data_age_days = (current_time - latest_date).days

            # 数据跨度（天）
            data_span_days = (latest_date - oldest_date).days

            # 更新频率分析
            date_diff = valid_dates.diff().dropna()
            avg_update_interval = date_diff.mean().days if len(date_diff) > 0 else 0

            # 新鲜度评分
            freshness_score = self._calculate_freshness_score(data_age_days)

            results[column] = {
                'latest_date': latest_date.isoformat(),
                'oldest_date': oldest_date.isoformat(),
                'data_age_days': data_age_days,
                'data_span_days': data_span_days,
                'avg_update_interval_days': avg_update_interval,
                'freshness_score': freshness_score,
                'total_records': len(valid_dates),
                'date_range_analysis': self._analyze_date_distribution(valid_dates)
            }

        return results

    def _calculate_freshness_score(self, age_days: int) -> int:
        """计算数据新鲜度评分"""
        if age_days <= 1:
            return 100  # 1天内
        elif age_days <= 7:
            return 90   # 1周内
        elif age_days <= 30:
            return 75   # 1月内
        elif age_days <= 90:
            return 50   # 3月内
        elif age_days <= 365:
            return 25   # 1年内
        else:
            return 10   # 超过1年
```

---

## 🤖 AI智能分析集成

### OpenAI API集成架构

```python
class AIAnalysisEngine:
    """AI智能分析引擎"""

    def __init__(self, openai_api_key: str):
        self.client = openai.AsyncOpenAI(api_key=openai_api_key)
        self.model = "gpt-4-turbo-preview"

    async def generate_quality_insights(self, quality_report: QualityReport) -> AIInsights:
        """生成智能质量洞察"""

        # 构建分析上下文
        context = self._build_analysis_context(quality_report)

        # 生成AI提示词
        prompt = self._create_analysis_prompt(context)

        # 调用OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        # 解析AI响应
        ai_analysis = self._parse_ai_response(response.choices[0].message.content)

        return AIInsights(
            executive_summary=ai_analysis['executive_summary'],
            key_findings=ai_analysis['key_findings'],
            root_cause_analysis=ai_analysis['root_cause_analysis'],
            recommendations=ai_analysis['recommendations'],
            priority_actions=ai_analysis['priority_actions'],
            business_impact=ai_analysis['business_impact']
        )

    def _get_system_prompt(self) -> str:
        """AI分析系统提示词"""
        return """
        你是一个专业的数据质量分析专家，拥有深厚的统计学、数据科学和业务分析背景。

        你的任务是基于数据质量评估结果，提供：
        1. 高层次的执行摘要
        2. 关键发现和问题识别
        3. 根本原因分析
        4. 具体的改进建议
        5. 优先级行动计划
        6. 业务影响评估

        请确保你的分析：
        - 基于具体的数据指标和证据
        - 提供可操作的建议
        - 考虑业务场景和实际约束
        - 使用清晰、专业的语言
        - 突出最关键的问题和机会
        """

    def _create_analysis_prompt(self, context: dict) -> str:
        """创建分析提示词"""
        return f"""
        请分析以下数据质量评估报告：

        数据集概况：
        - 总记录数：{context['total_records']}
        - 总字段数：{context['total_columns']}
        - 数据类型分布：{context['data_type_distribution']}

        质量维度得分：
        - 完整性得分：{context['completeness_score']}/100
        - 一致性得分：{context['consistency_score']}/100
        - 准确性得分：{context['accuracy_score']}/100
        - 时效性得分：{context['timeliness_score']}/100
        - 综合得分：{context['overall_score']}/100

        关键问题：
        {context['critical_issues']}

        详细统计信息：
        {context['detailed_statistics']}

        请提供结构化的分析报告，包括执行摘要、关键发现、根本原因分析、改进建议和行动计划。
        """
```

---

## 📊 综合评分模型

### 多维度权重配置

```python
class CompositeScoreCalculator:
    """综合评分计算器"""

    def __init__(self):
        # 默认权重配置
        self.default_weights = {
            'completeness': 0.30,  # 完整性
            'consistency': 0.25,   # 一致性
            'accuracy': 0.25,      # 准确性
            'timeliness': 0.20     # 时效性
        }

        # 业务场景权重配置
        self.scenario_weights = {
            'financial': {
                'completeness': 0.35,
                'consistency': 0.25,
                'accuracy': 0.35,
                'timeliness': 0.05
            },
            'real_time': {
                'completeness': 0.20,
                'consistency': 0.20,
                'accuracy': 0.25,
                'timeliness': 0.35
            },
            'analytics': {
                'completeness': 0.25,
                'consistency': 0.30,
                'accuracy': 0.30,
                'timeliness': 0.15
            }
        }

    def calculate_composite_score(
        self,
        completeness_score: float,
        consistency_score: float,
        accuracy_score: float,
        timeliness_score: float,
        scenario: str = 'default'
    ) -> dict:
        """计算综合质量得分"""

        # 获取权重配置
        weights = self.scenario_weights.get(scenario, self.default_weights)

        # 计算加权平均得分
        weighted_score = (
            completeness_score * weights['completeness'] +
            consistency_score * weights['consistency'] +
            accuracy_score * weights['accuracy'] +
            timeliness_score * weights['timeliness']
        )

        # 质量等级判定
        quality_grade = self._determine_quality_grade(weighted_score)

        # 置信度计算
        confidence_score = self._calculate_confidence(
            completeness_score, consistency_score, accuracy_score, timeliness_score
        )

        return {
            'overall_score': round(weighted_score, 2),
            'quality_grade': quality_grade,
            'confidence_score': confidence_score,
            'dimension_scores': {
                'completeness': completeness_score,
                'consistency': consistency_score,
                'accuracy': accuracy_score,
                'timeliness': timeliness_score
            },
            'weights_used': weights,
            'scenario': scenario
        }

    def _determine_quality_grade(self, score: float) -> str:
        """确定质量等级"""
        if score >= 90:
            return 'A'  # 优秀
        elif score >= 80:
            return 'B'  # 良好
        elif score >= 70:
            return 'C'  # 一般
        elif score >= 60:
            return 'D'  # 较差
        else:
            return 'F'  # 不合格

    def _calculate_confidence(self, *scores) -> float:
        """计算评分置信度"""
        # 基于分数方差计算置信度
        scores_array = np.array(scores)
        variance = np.var(scores_array)

        # 方差越小，置信度越高
        confidence = max(0, 100 - variance)
        return round(confidence, 2)
```

---

## 🚀 性能优化策略

### 1. 异步处理优化

```python
class PerformanceOptimizer:
    """性能优化器"""

    @staticmethod
    async def process_large_dataset(df: pd.DataFrame, chunk_size: int = 10000) -> list:
        """大数据集分块处理"""

        chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

        # 并行处理各个分块
        tasks = [
            DataQualityFramework().analyze(chunk)
            for chunk in chunks
        ]

        chunk_results = await asyncio.gather(*tasks)

        # 合并分块结果
        return PerformanceOptimizer._merge_chunk_results(chunk_results)

    @staticmethod
    def _merge_chunk_results(chunk_results: list) -> QualityReport:
        """合并分块分析结果"""
        # 实现结果合并逻辑
        pass
```

### 2. 缓存策略

```python
class CacheManager:
    """缓存管理器"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_ttl = 3600  # 1小时

    async def get_cached_result(self, data_hash: str) -> Optional[QualityReport]:
        """获取缓存的分析结果"""

        cached_data = await self.redis.get(f"quality_analysis:{data_hash}")

        if cached_data:
            return QualityReport.from_json(cached_data)

        return None

    async def cache_result(self, data_hash: str, result: QualityReport):
        """缓存分析结果"""

        await self.redis.setex(
            f"quality_analysis:{data_hash}",
            self.cache_ttl,
            result.to_json()
        )
```

---

## 📈 数据模型定义

### 核心数据结构

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class QualityReport:
    """数据质量报告"""

    # 基本信息
    dataset_id: str
    dataset_name: str
    analysis_timestamp: datetime
    total_records: int
    total_columns: int

    # 维度分析结果
    completeness: CompletenessResult
    consistency: ConsistencyResult
    accuracy: AccuracyResult
    timeliness: TimelinessResult

    # 综合评分
    overall_score: float
    quality_grade: str
    confidence_score: float

    # AI洞察
    ai_insights: Optional[AIInsights] = None

    # 元数据
    processing_time_seconds: float
    algorithm_version: str

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset_name,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'summary': {
                'total_records': self.total_records,
                'total_columns': self.total_columns,
                'overall_score': self.overall_score,
                'quality_grade': self.quality_grade,
                'confidence_score': self.confidence_score
            },
            'dimension_scores': {
                'completeness': self.completeness.overall_score,
                'consistency': self.consistency.overall_score,
                'accuracy': self.accuracy.overall_score,
                'timeliness': self.timeliness.overall_score
            },
            'detailed_results': {
                'completeness': self.completeness.to_dict(),
                'consistency': self.consistency.to_dict(),
                'accuracy': self.accuracy.to_dict(),
                'timeliness': self.timeliness.to_dict()
            },
            'ai_insights': self.ai_insights.to_dict() if self.ai_insights else None,
            'metadata': {
                'processing_time_seconds': self.processing_time_seconds,
                'algorithm_version': self.algorithm_version
            }
        }

@dataclass
class CompletenessResult:
    """完整性分析结果"""
    column_results: Dict[str, dict]
    overall_score: float
    critical_issues: List[str]
    recommendations: List[str]

@dataclass
class AIInsights:
    """AI智能洞察"""
    executive_summary: str
    key_findings: List[str]
    root_cause_analysis: Dict[str, str]
    recommendations: List[dict]
    priority_actions: List[dict]
    business_impact: str
```

---

## 🔗 API接口规范

### FastAPI端点定义

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

router = APIRouter(prefix="/api/v1/data-quality", tags=["data-quality"])

@router.post("/analyze")
async def analyze_data_quality(
    dataset_id: str,
    analysis_config: Optional[dict] = None,
    background_tasks: BackgroundTasks = None
) -> dict:
    """执行数据质量分析"""

    try:
        # 获取数据集
        dataset = await get_dataset(dataset_id)

        # 执行分析
        framework = DataQualityFramework()
        result = await framework.analyze(dataset)

        # 保存结果
        await save_analysis_result(result)

        # 异步生成AI洞察
        if analysis_config.get('include_ai_insights', True):
            background_tasks.add_task(generate_ai_insights, result.id)

        return {
            'success': True,
            'analysis_id': result.id,
            'overall_score': result.overall_score,
            'quality_grade': result.quality_grade,
            'summary': result.to_dict()['summary']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str) -> QualityReport:
    """获取分析结果"""

    result = await get_analysis_by_id(analysis_id)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return result

@router.get("/analysis/{analysis_id}/recommendations")
async def get_recommendations(analysis_id: str) -> dict:
    """获取改进建议"""

    result = await get_analysis_by_id(analysis_id)

    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        'completeness_recommendations': result.completeness.recommendations,
        'consistency_recommendations': result.consistency.recommendations,
        'accuracy_recommendations': result.accuracy.recommendations,
        'timeliness_recommendations': result.timeliness.recommendations,
        'ai_recommendations': result.ai_insights.recommendations if result.ai_insights else []
    }
```

---

## 📋 实施检查清单

### Phase 1: 核心算法实现 (Day 1-2)
- [ ] 完整性分析器实现
- [ ] 一致性分析器实现
- [ ] 准确性分析器实现
- [ ] 时效性分析器实现
- [ ] 综合评分计算器实现
- [ ] 基础单元测试

### Phase 2: AI集成 (Day 3)
- [ ] OpenAI API集成
- [ ] AI提示词设计和优化
- [ ] 智能建议生成逻辑
- [ ] 响应解析和处理

### Phase 3: 性能优化 (Day 4)
- [ ] 异步处理优化
- [ ] 缓存机制实现
- [ ] 大数据集分块处理
- [ ] 内存使用优化

### Phase 4: API开发 (Day 5)
- [ ] FastAPI端点实现
- [ ] 数据库模型设计
- [ ] 结果存储和检索
- [ ] 错误处理和验证

### Phase 5: 测试和文档 (Day 6)
- [ ] 集成测试
- [ ] 性能测试
- [ ] API文档生成
- [ ] 部署配置

---

**文档审核**: Analytics Reporter
**技术审核**: Backend Architect
**最后更新**: 2025-09-20
**版本**: v1.0