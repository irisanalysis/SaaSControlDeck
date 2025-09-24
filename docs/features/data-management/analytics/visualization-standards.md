# 可视化标准与报告规范
## Visualization Standards and Reporting Specifications

**文档版本**: v1.0
**创建时间**: 2025-09-20
**负责人**: Analytics Reporter
**项目**: SaaS Control Deck - Data Management Module

---

## 📋 概述

本文档定义了SaaS Control Deck数据管理功能的可视化标准和报告规范，包括图表类型选择、指标展示规范、交互设计标准、以及自动化报告模板。确保数据分析结果以直观、专业、可操作的方式呈现给用户。

---

## 🎨 设计系统规范

### 色彩体系

```typescript
// 数据质量专用色彩体系
export const DataQualityColors = {
  // 主要质量等级色彩
  qualityGrades: {
    excellent: '#10B981',    // 绿色 - 优秀 (90-100分)
    good: '#3B82F6',        // 蓝色 - 良好 (80-89分)
    fair: '#F59E0B',        // 橙色 - 一般 (70-79分)
    poor: '#EF4444',        // 红色 - 较差 (60-69分)
    critical: '#DC2626'     // 深红色 - 严重 (0-59分)
  },

  // 维度特定色彩
  dimensions: {
    completeness: '#8B5CF6',  // 紫色
    consistency: '#06B6D4',   // 青色
    accuracy: '#10B981',      // 绿色
    timeliness: '#F59E0B'     // 橙色
  },

  // 中性色彩系统
  neutral: {
    gray50: '#F9FAFB',
    gray100: '#F3F4F6',
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',
    gray400: '#9CA3AF',
    gray500: '#6B7280',
    gray600: '#4B5563',
    gray700: '#374151',
    gray800: '#1F2937',
    gray900: '#111827'
  },

  // 语义色彩
  semantic: {
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    neutral: '#6B7280'
  },

  // 渐变色彩
  gradients: {
    qualityScore: ['#EF4444', '#F59E0B', '#10B981'], // 从差到好
    heatmap: ['#FEF3F2', '#FEE2E2', '#FECACA', '#FCA5A5', '#F87171', '#EF4444', '#DC2626'],
    trend: ['#DBEAFE', '#93C5FD', '#60A5FA', '#3B82F6', '#2563EB']
  }
} as const;

// 图表主题配置
export const ChartTheme = {
  fontFamily: 'Inter, system-ui, sans-serif',
  fontSize: {
    xs: '12px',
    sm: '14px',
    base: '16px',
    lg: '18px',
    xl: '20px'
  },
  borderRadius: '8px',
  boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
  animation: {
    duration: 300,
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
  }
} as const;
```

### 图标系统

```typescript
// 数据质量相关图标映射
export const DataQualityIcons = {
  dimensions: {
    completeness: 'CheckCircle',
    consistency: 'RefreshCw',
    accuracy: 'Target',
    timeliness: 'Clock'
  },

  qualityLevels: {
    excellent: 'Award',
    good: 'ThumbsUp',
    fair: 'AlertTriangle',
    poor: 'AlertCircle',
    critical: 'XCircle'
  },

  actions: {
    analyze: 'BarChart3',
    repair: 'Wrench',
    export: 'Download',
    refresh: 'RotateCcw',
    settings: 'Settings',
    info: 'Info'
  },

  trends: {
    up: 'TrendingUp',
    down: 'TrendingDown',
    stable: 'Minus'
  }
} as const;
```

---

## 📊 核心图表组件库

### 1. 质量得分仪表盘

```typescript
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface QualityScoreMeterProps {
  score: number;
  label: string;
  dimension?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const QualityScoreMeter: React.FC<QualityScoreMeterProps> = ({
  score,
  label,
  dimension,
  size = 'md',
  showLabel = true
}) => {
  const getScoreColor = (score: number): string => {
    if (score >= 90) return DataQualityColors.qualityGrades.excellent;
    if (score >= 80) return DataQualityColors.qualityGrades.good;
    if (score >= 70) return DataQualityColors.qualityGrades.fair;
    if (score >= 60) return DataQualityColors.qualityGrades.poor;
    return DataQualityColors.qualityGrades.critical;
  };

  const getScoreLevel = (score: number): string => {
    if (score >= 90) return '优秀';
    if (score >= 80) return '良好';
    if (score >= 70) return '一般';
    if (score >= 60) return '较差';
    return '严重';
  };

  const sizeConfig = {
    sm: { diameter: 80, strokeWidth: 6 },
    md: { diameter: 120, strokeWidth: 8 },
    lg: { diameter: 160, strokeWidth: 10 }
  };

  const config = sizeConfig[size];
  const radius = config.diameter / 2;
  const circumference = 2 * Math.PI * (radius - config.strokeWidth);
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center space-y-2">
      <div className="relative">
        <svg width={config.diameter} height={config.diameter}>
          {/* 背景圆环 */}
          <circle
            cx={radius}
            cy={radius}
            r={radius - config.strokeWidth}
            fill="none"
            stroke={DataQualityColors.neutral.gray200}
            strokeWidth={config.strokeWidth}
          />

          {/* 进度圆环 */}
          <circle
            cx={radius}
            cy={radius}
            r={radius - config.strokeWidth}
            fill="none"
            stroke={getScoreColor(score)}
            strokeWidth={config.strokeWidth}
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            transform={`rotate(-90 ${radius} ${radius})`}
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {/* 中心文字 */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-gray-900">{score}</span>
          <span className="text-xs text-gray-500">分</span>
        </div>
      </div>

      {showLabel && (
        <div className="text-center">
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-xs text-gray-500">{getScoreLevel(score)}</p>
        </div>
      )}
    </div>
  );
};
```

### 2. 多维度雷达图

```typescript
import React from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend
} from 'recharts';

interface DimensionRadarProps {
  data: {
    dimension: string;
    score: number;
    benchmark?: number;
    maxScore?: number;
  }[];
  showBenchmark?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const DimensionRadarChart: React.FC<DimensionRadarProps> = ({
  data,
  showBenchmark = true,
  size = 'md'
}) => {
  const sizeConfig = {
    sm: { height: 200 },
    md: { height: 300 },
    lg: { height: 400 }
  };

  const chartData = data.map(item => ({
    dimension: item.dimension,
    '当前得分': item.score,
    '行业基准': item.benchmark || 75,
    fullMark: 100
  }));

  return (
    <div style={{ height: sizeConfig[size].height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={chartData} margin={{ top: 20, right: 80, bottom: 20, left: 80 }}>
          <PolarGrid
            gridType="polygon"
            strokeWidth={1}
            stroke={DataQualityColors.neutral.gray300}
          />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 12, fill: DataQualityColors.neutral.gray600 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: DataQualityColors.neutral.gray500 }}
            strokeWidth={0}
          />

          {/* 当前得分 */}
          <Radar
            name="当前得分"
            dataKey="当前得分"
            stroke={DataQualityColors.semantic.info}
            fill={DataQualityColors.semantic.info}
            fillOpacity={0.3}
            strokeWidth={2}
            dot={{ fill: DataQualityColors.semantic.info, strokeWidth: 2, r: 4 }}
          />

          {/* 行业基准 */}
          {showBenchmark && (
            <Radar
              name="行业基准"
              dataKey="行业基准"
              stroke={DataQualityColors.neutral.gray400}
              fill="none"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ fill: DataQualityColors.neutral.gray400, strokeWidth: 2, r: 3 }}
            />
          )}

          <Legend
            verticalAlign="bottom"
            align="center"
            wrapperStyle={{ paddingTop: '20px' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 3. 质量趋势折线图

```typescript
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { format } from 'date-fns';

interface QualityTrendProps {
  data: {
    timestamp: string;
    completeness: number;
    consistency: number;
    accuracy: number;
    timeliness: number;
    overall: number;
  }[];
  selectedDimensions?: string[];
  showTarget?: boolean;
  targetScore?: number;
}

export const QualityTrendChart: React.FC<QualityTrendProps> = ({
  data,
  selectedDimensions = ['overall'],
  showTarget = true,
  targetScore = 85
}) => {
  const formatTooltipLabel = (label: string) => {
    return format(new Date(label), 'yyyy年MM月dd日 HH:mm');
  };

  const formatTooltipValue = (value: number, name: string) => {
    const dimensionNames = {
      completeness: '完整性',
      consistency: '一致性',
      accuracy: '准确性',
      timeliness: '时效性',
      overall: '综合得分'
    };
    return [`${value}分`, dimensionNames[name as keyof typeof dimensionNames] || name];
  };

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={DataQualityColors.neutral.gray200}
          />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => format(new Date(value), 'MM/dd')}
            stroke={DataQualityColors.neutral.gray500}
            fontSize={12}
          />
          <YAxis
            domain={[0, 100]}
            stroke={DataQualityColors.neutral.gray500}
            fontSize={12}
          />
          <Tooltip
            labelFormatter={formatTooltipLabel}
            formatter={formatTooltipValue}
            contentStyle={{
              backgroundColor: 'white',
              border: `1px solid ${DataQualityColors.neutral.gray200}`,
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />

          {/* 目标线 */}
          {showTarget && (
            <ReferenceLine
              y={targetScore}
              stroke={DataQualityColors.semantic.warning}
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ value: `目标: ${targetScore}分`, position: 'topRight' }}
            />
          )}

          {/* 维度线条 */}
          {selectedDimensions.includes('completeness') && (
            <Line
              type="monotone"
              dataKey="completeness"
              stroke={DataQualityColors.dimensions.completeness}
              strokeWidth={2}
              dot={{ fill: DataQualityColors.dimensions.completeness, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          )}

          {selectedDimensions.includes('consistency') && (
            <Line
              type="monotone"
              dataKey="consistency"
              stroke={DataQualityColors.dimensions.consistency}
              strokeWidth={2}
              dot={{ fill: DataQualityColors.dimensions.consistency, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          )}

          {selectedDimensions.includes('accuracy') && (
            <Line
              type="monotone"
              dataKey="accuracy"
              stroke={DataQualityColors.dimensions.accuracy}
              strokeWidth={2}
              dot={{ fill: DataQualityColors.dimensions.accuracy, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          )}

          {selectedDimensions.includes('timeliness') && (
            <Line
              type="monotone"
              dataKey="timeliness"
              stroke={DataQualityColors.dimensions.timeliness}
              strokeWidth={2}
              dot={{ fill: DataQualityColors.dimensions.timeliness, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
          )}

          {selectedDimensions.includes('overall') && (
            <Line
              type="monotone"
              dataKey="overall"
              stroke={DataQualityColors.semantic.info}
              strokeWidth={3}
              dot={{ fill: DataQualityColors.semantic.info, strokeWidth: 2, r: 5 }}
              activeDot={{ r: 7 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 4. 问题分布热力图

```typescript
import React from 'react';
import { HeatMapGrid } from 'react-grid-heatmap';

interface DataQualityHeatmapProps {
  data: {
    field: string;
    issues: {
      missing: number;
      inconsistent: number;
      inaccurate: number;
      outdated: number;
    };
  }[];
  maxValue?: number;
}

export const DataQualityHeatmap: React.FC<DataQualityHeatmapProps> = ({
  data,
  maxValue = 100
}) => {
  // 转换数据格式为热力图所需格式
  const heatmapData = data.map(item => [
    item.issues.missing,
    item.issues.inconsistent,
    item.issues.inaccurate,
    item.issues.outdated
  ]);

  const xLabels = ['缺失值', '不一致', '不准确', '过时'];
  const yLabels = data.map(item => item.field);

  const getCellColor = (value: number, min: number, max: number): string => {
    const normalizedValue = (value - min) / (max - min);

    if (normalizedValue <= 0.2) return DataQualityColors.gradients.heatmap[0];
    if (normalizedValue <= 0.4) return DataQualityColors.gradients.heatmap[1];
    if (normalizedValue <= 0.6) return DataQualityColors.gradients.heatmap[2];
    if (normalizedValue <= 0.8) return DataQualityColors.gradients.heatmap[3];
    return DataQualityColors.gradients.heatmap[4];
  };

  return (
    <div className="w-full">
      <HeatMapGrid
        data={heatmapData}
        xLabels={xLabels}
        yLabels={yLabels}
        cellRender={(x, y, value) => (
          <div
            className="w-full h-full flex items-center justify-center text-white text-xs font-medium"
            style={{
              backgroundColor: getCellColor(value, 0, maxValue)
            }}
          >
            {value}%
          </div>
        )}
        xLabelsStyle={(index) => ({
          color: DataQualityColors.neutral.gray700,
          fontSize: '12px',
          fontWeight: '500'
        })}
        yLabelsStyle={(index) => ({
          color: DataQualityColors.neutral.gray700,
          fontSize: '12px',
          fontWeight: '500'
        })}
        cellStyle={(_x, _y, ratio) => ({
          backgroundColor: getCellColor(ratio * maxValue, 0, maxValue),
          fontSize: '11px',
          color: ratio > 0.5 ? 'white' : DataQualityColors.neutral.gray800
        })}
        cellHeight="40px"
        cellWidth="80px"
        square={false}
      />

      {/* 图例 */}
      <div className="mt-4 flex items-center justify-center space-x-4">
        <span className="text-sm text-gray-600">问题严重程度:</span>
        <div className="flex items-center space-x-2">
          {DataQualityColors.gradients.heatmap.slice(0, 5).map((color, index) => (
            <div key={index} className="flex items-center space-x-1">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-xs text-gray-500">
                {index === 0 ? '低' : index === 4 ? '高' : ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

---

## 📊 仪表盘布局规范

### 1. 主仪表盘布局

```typescript
import React from 'react';
import { Grid, Card, CardHeader, CardContent } from '@/components/ui';

interface MainDashboardProps {
  overallScore: number;
  dimensionScores: {
    completeness: number;
    consistency: number;
    accuracy: number;
    timeliness: number;
  };
  trendData: any[];
  issueDistribution: any[];
}

export const MainDashboard: React.FC<MainDashboardProps> = ({
  overallScore,
  dimensionScores,
  trendData,
  issueDistribution
}) => {
  return (
    <div className="p-6 space-y-6">
      {/* 顶部概览区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* 综合得分 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <h3 className="text-lg font-semibold">综合得分</h3>
          </CardHeader>
          <CardContent>
            <QualityScoreMeter
              score={overallScore}
              label="数据质量"
              size="lg"
            />
          </CardContent>
        </Card>

        {/* 维度得分 */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <h3 className="text-lg font-semibold">维度评分</h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(dimensionScores).map(([dimension, score]) => (
                <QualityScoreMeter
                  key={dimension}
                  score={score}
                  label={getDimensionLabel(dimension)}
                  dimension={dimension}
                  size="md"
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 中部分析区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 趋势分析 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">质量趋势</h3>
          </CardHeader>
          <CardContent>
            <QualityTrendChart data={trendData} />
          </CardContent>
        </Card>

        {/* 雷达图 */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">多维度对比</h3>
          </CardHeader>
          <CardContent>
            <DimensionRadarChart
              data={Object.entries(dimensionScores).map(([dim, score]) => ({
                dimension: getDimensionLabel(dim),
                score,
                benchmark: 75
              }))}
            />
          </CardContent>
        </Card>
      </div>

      {/* 底部详细分析区域 */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">问题分布热力图</h3>
        </CardHeader>
        <CardContent>
          <DataQualityHeatmap data={issueDistribution} />
        </CardContent>
      </Card>
    </div>
  );
};

const getDimensionLabel = (dimension: string): string => {
  const labels = {
    completeness: '完整性',
    consistency: '一致性',
    accuracy: '准确性',
    timeliness: '时效性'
  };
  return labels[dimension as keyof typeof labels] || dimension;
};
```

### 2. 响应式设计规范

```typescript
// 响应式断点配置
export const ResponsiveBreakpoints = {
  sm: '640px',   // 手机横屏
  md: '768px',   // 平板竖屏
  lg: '1024px',  // 平板横屏/小笔记本
  xl: '1280px',  // 桌面显示器
  '2xl': '1536px' // 大桌面显示器
} as const;

// 响应式布局配置
export const ResponsiveLayouts = {
  dashboard: {
    sm: 'grid-cols-1',
    md: 'grid-cols-2',
    lg: 'grid-cols-3',
    xl: 'grid-cols-4'
  },
  charts: {
    sm: 'h-64',
    md: 'h-80',
    lg: 'h-96'
  },
  cards: {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }
} as const;

// 移动端优化组件
export const MobileDashboard: React.FC<MainDashboardProps> = (props) => {
  return (
    <div className="p-4 space-y-4">
      {/* 移动端紧凑布局 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <QualityScoreMeter
              score={props.overallScore}
              label="综合得分"
              size="sm"
            />
            <div className="flex flex-col space-y-2">
              {Object.entries(props.dimensionScores).map(([dim, score]) => (
                <div key={dim} className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 w-16">
                    {getDimensionLabel(dim)}
                  </span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${score}%`,
                        backgroundColor: getScoreColor(score)
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium w-8">{score}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 移动端图表 - 可滑动 */}
      <div className="overflow-x-auto">
        <div className="flex space-x-4 w-max">
          <Card className="w-80">
            <CardHeader>
              <h3 className="text-base font-semibold">趋势</h3>
            </CardHeader>
            <CardContent>
              <QualityTrendChart data={props.trendData} />
            </CardContent>
          </Card>

          <Card className="w-80">
            <CardHeader>
              <h3 className="text-base font-semibold">对比</h3>
            </CardHeader>
            <CardContent>
              <DimensionRadarChart
                data={Object.entries(props.dimensionScores).map(([dim, score]) => ({
                  dimension: getDimensionLabel(dim),
                  score,
                  benchmark: 75
                }))}
                size="sm"
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
```

---

## 📋 报告模板系统

### 1. 执行摘要报告模板

```typescript
interface ExecutiveSummaryReportProps {
  reportData: {
    overallScore: number;
    previousScore?: number;
    dimensionScores: Record<string, number>;
    keyFindings: string[];
    criticalIssues: string[];
    recommendations: string[];
    businessImpact: string;
    timeframe: {
      start: string;
      end: string;
    };
  };
}

export const ExecutiveSummaryReport: React.FC<ExecutiveSummaryReportProps> = ({
  reportData
}) => {
  const scoreChange = reportData.previousScore
    ? reportData.overallScore - reportData.previousScore
    : null;

  return (
    <div className="max-w-4xl mx-auto p-8 bg-white">
      {/* 报告头部 */}
      <div className="border-b-2 border-gray-200 pb-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              数据质量执行摘要报告
            </h1>
            <p className="text-gray-600 mt-2">
              报告期间: {formatDate(reportData.timeframe.start)} - {formatDate(reportData.timeframe.end)}
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-blue-600">
              {reportData.overallScore}
            </div>
            <div className="text-sm text-gray-500">综合得分</div>
            {scoreChange && (
              <div className={`text-sm ${scoreChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {scoreChange >= 0 ? '+' : ''}{scoreChange.toFixed(1)} 较上期
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 关键指标概览 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">关键指标概览</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(reportData.dimensionScores).map(([dimension, score]) => (
            <div key={dimension} className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{score}</div>
              <div className="text-sm text-gray-600">{getDimensionLabel(dimension)}</div>
              <div className="mt-2">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="h-2 rounded-full"
                    style={{
                      width: `${score}%`,
                      backgroundColor: getScoreColor(score)
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 关键发现 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">关键发现</h2>
        <div className="space-y-3">
          {reportData.keyFindings.map((finding, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </div>
              <p className="text-gray-700">{finding}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 关键问题 */}
      {reportData.criticalIssues.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 text-red-600">关键问题</h2>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <ul className="space-y-2">
              {reportData.criticalIssues.map((issue, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <span className="text-red-500 mt-1">⚠️</span>
                  <span className="text-red-700">{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 改进建议 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">改进建议</h2>
        <div className="space-y-4">
          {reportData.recommendations.map((recommendation, index) => (
            <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <p className="text-green-700">{recommendation}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 业务影响分析 */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">业务影响分析</h2>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <p className="text-blue-800">{reportData.businessImpact}</p>
        </div>
      </div>

      {/* 报告尾部 */}
      <div className="border-t-2 border-gray-200 pt-6 text-center text-gray-500">
        <p>报告生成时间: {formatDate(new Date().toISOString())}</p>
        <p>SaaS Control Deck - 数据质量管理平台</p>
      </div>
    </div>
  );
};
```

### 2. 详细技术报告模板

```typescript
interface TechnicalReportProps {
  reportData: {
    datasetInfo: {
      name: string;
      records: number;
      columns: number;
      size: string;
    };
    qualityMetrics: {
      completeness: {
        overall: number;
        byColumn: Record<string, number>;
        missingPatterns: any[];
      };
      consistency: {
        overall: number;
        formatIssues: any[];
        typeIssues: any[];
      };
      accuracy: {
        overall: number;
        outliers: any[];
        validationErrors: any[];
      };
      timeliness: {
        overall: number;
        freshnessScore: number;
        updateFrequency: string;
      };
    };
    recommendations: any[];
    technicalDetails: {
      analysisMethod: string;
      processingTime: number;
      algorithmVersion: string;
    };
  };
}

export const TechnicalReport: React.FC<TechnicalReportProps> = ({
  reportData
}) => {
  return (
    <div className="max-w-6xl mx-auto p-8 bg-white">
      {/* 数据集信息 */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">数据集信息</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold">{reportData.datasetInfo.name}</div>
            <div className="text-sm text-gray-600">数据集名称</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold">{reportData.datasetInfo.records.toLocaleString()}</div>
            <div className="text-sm text-gray-600">记录数</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold">{reportData.datasetInfo.columns}</div>
            <div className="text-sm text-gray-600">字段数</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-lg font-semibold">{reportData.datasetInfo.size}</div>
            <div className="text-sm text-gray-600">数据大小</div>
          </div>
        </div>
      </div>

      {/* 详细质量分析 */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">详细质量分析</h2>

        {/* 完整性分析 */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-3">完整性分析</h3>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <span>总体完整性得分</span>
              <span className="text-xl font-bold">{reportData.qualityMetrics.completeness.overall}</span>
            </div>

            {/* 字段级别完整性 */}
            <div className="space-y-2">
              <h4 className="font-medium">字段完整性详情</h4>
              {Object.entries(reportData.qualityMetrics.completeness.byColumn).map(([column, score]) => (
                <div key={column} className="flex items-center justify-between">
                  <span className="text-sm">{column}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${score}%`,
                          backgroundColor: getScoreColor(score)
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{score}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 其他维度分析... */}
      </div>

      {/* 技术细节 */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">技术细节</h2>
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <span className="text-sm text-gray-600">分析方法</span>
              <div className="font-medium">{reportData.technicalDetails.analysisMethod}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">处理时间</span>
              <div className="font-medium">{reportData.technicalDetails.processingTime}秒</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">算法版本</span>
              <div className="font-medium">{reportData.technicalDetails.algorithmVersion}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

---

## 📱 交互设计规范

### 1. 交互状态定义

```typescript
// 交互状态枚举
export enum InteractionState {
  Default = 'default',
  Hover = 'hover',
  Active = 'active',
  Disabled = 'disabled',
  Loading = 'loading',
  Error = 'error',
  Success = 'success'
}

// 状态样式映射
export const StateStyles = {
  [InteractionState.Default]: {
    opacity: 1,
    cursor: 'default',
    transform: 'scale(1)'
  },
  [InteractionState.Hover]: {
    opacity: 0.8,
    cursor: 'pointer',
    transform: 'scale(1.02)'
  },
  [InteractionState.Active]: {
    opacity: 0.9,
    cursor: 'pointer',
    transform: 'scale(0.98)'
  },
  [InteractionState.Disabled]: {
    opacity: 0.5,
    cursor: 'not-allowed',
    transform: 'scale(1)'
  },
  [InteractionState.Loading]: {
    opacity: 0.7,
    cursor: 'wait',
    transform: 'scale(1)'
  }
} as const;
```

### 2. 工具提示规范

```typescript
import React from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';

interface DataTooltipProps {
  content: string | React.ReactNode;
  children: React.ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
  align?: 'start' | 'center' | 'end';
}

export const DataTooltip: React.FC<DataTooltipProps> = ({
  content,
  children,
  side = 'top',
  align = 'center'
}) => {
  return (
    <Tooltip.Provider delayDuration={300}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          {children}
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            side={side}
            align={align}
            className="bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg max-w-xs z-50"
            sideOffset={5}
          >
            {content}
            <Tooltip.Arrow className="fill-gray-900" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
};

// 数据质量专用工具提示
export const QualityScoreTooltip: React.FC<{
  score: number;
  dimension: string;
  details: string[];
  children: React.ReactNode;
}> = ({ score, dimension, details, children }) => {
  const tooltipContent = (
    <div className="space-y-2">
      <div className="font-semibold">{getDimensionLabel(dimension)}: {score}分</div>
      <div className="text-xs space-y-1">
        {details.map((detail, index) => (
          <div key={index}>• {detail}</div>
        ))}
      </div>
    </div>
  );

  return (
    <DataTooltip content={tooltipContent}>
      {children}
    </DataTooltip>
  );
};
```

### 3. 数据钻取交互

```typescript
interface DrillDownChartProps {
  data: any[];
  onDrillDown: (level: string, item: any) => void;
  currentLevel: 'overview' | 'dimension' | 'field';
  breadcrumb: { label: string; level: string; data?: any }[];
}

export const DrillDownChart: React.FC<DrillDownChartProps> = ({
  data,
  onDrillDown,
  currentLevel,
  breadcrumb
}) => {
  const handleChartClick = (item: any) => {
    switch (currentLevel) {
      case 'overview':
        onDrillDown('dimension', item);
        break;
      case 'dimension':
        onDrillDown('field', item);
        break;
      default:
        break;
    }
  };

  return (
    <div className="space-y-4">
      {/* 面包屑导航 */}
      <nav className="flex items-center space-x-2 text-sm">
        {breadcrumb.map((crumb, index) => (
          <React.Fragment key={index}>
            {index > 0 && <span className="text-gray-400">/</span>}
            <button
              onClick={() => onDrillDown(crumb.level, crumb.data)}
              className="text-blue-600 hover:text-blue-800 hover:underline"
            >
              {crumb.label}
            </button>
          </React.Fragment>
        ))}
      </nav>

      {/* 图表内容 */}
      <div className="relative">
        {/* 根据当前层级渲染不同的图表 */}
        {currentLevel === 'overview' && (
          <DimensionOverviewChart
            data={data}
            onClick={handleChartClick}
          />
        )}

        {currentLevel === 'dimension' && (
          <DimensionDetailChart
            data={data}
            onClick={handleChartClick}
          />
        )}

        {currentLevel === 'field' && (
          <FieldLevelChart
            data={data}
            onClick={handleChartClick}
          />
        )}

        {/* 钻取提示 */}
        {currentLevel !== 'field' && (
          <div className="absolute top-2 right-2 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            点击进行详细分析
          </div>
        )}
      </div>
    </div>
  );
};
```

---

## 📊 导出和分享功能

### 1. 导出配置

```typescript
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

export class ReportExporter {
  static async exportToPDF(elementId: string, filename: string) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const canvas = await html2canvas(element, {
      scale: 2,
      logging: false,
      useCORS: true
    });

    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const imgWidth = 210;
    const pageHeight = 295;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
    let heightLeft = imgHeight;

    let position = 0;

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
    heightLeft -= pageHeight;

    while (heightLeft >= 0) {
      position = heightLeft - imgHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
    }

    pdf.save(filename);
  }

  static async exportToImage(elementId: string, filename: string, format: 'png' | 'jpeg' = 'png') {
    const element = document.getElementById(elementId);
    if (!element) return;

    const canvas = await html2canvas(element, {
      scale: 2,
      logging: false,
      useCORS: true
    });

    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL(`image/${format}`);
    link.click();
  }

  static exportToExcel(data: any[], filename: string) {
    // 使用 xlsx 库导出 Excel
    // 实现省略...
  }
}

// 导出按钮组件
export const ExportButton: React.FC<{
  targetId: string;
  filename: string;
  formats?: ('pdf' | 'png' | 'excel')[];
}> = ({ targetId, filename, formats = ['pdf', 'png'] }) => {
  const handleExport = async (format: string) => {
    switch (format) {
      case 'pdf':
        await ReportExporter.exportToPDF(targetId, `${filename}.pdf`);
        break;
      case 'png':
        await ReportExporter.exportToImage(targetId, `${filename}.png`);
        break;
      case 'excel':
        // 导出 Excel 逻辑
        break;
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          导出
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        {formats.map(format => (
          <DropdownMenuItem key={format} onClick={() => handleExport(format)}>
            导出为 {format.toUpperCase()}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

### 2. 分享功能

```typescript
export const ShareButton: React.FC<{
  reportId: string;
  reportTitle: string;
}> = ({ reportId, reportTitle }) => {
  const [shareUrl, setShareUrl] = useState('');
  const [isPublic, setIsPublic] = useState(false);

  const handleShare = async () => {
    // 生成分享链接
    const url = await generateShareUrl(reportId, isPublic);
    setShareUrl(url);

    // 复制到剪贴板
    await navigator.clipboard.writeText(url);

    // 显示成功提示
    toast.success('分享链接已复制到剪贴板');
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Share className="w-4 h-4 mr-2" />
          分享
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>分享报告</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              checked={isPublic}
              onCheckedChange={setIsPublic}
            />
            <label>公开分享（无需登录即可查看）</label>
          </div>

          {shareUrl && (
            <div className="space-y-2">
              <label className="text-sm font-medium">分享链接</label>
              <div className="flex items-center space-x-2">
                <Input value={shareUrl} readOnly />
                <Button size="sm" onClick={() => navigator.clipboard.writeText(shareUrl)}>
                  复制
                </Button>
              </div>
            </div>
          )}

          <Button onClick={handleShare} className="w-full">
            生成分享链接
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

---

## 📋 实施检查清单

### Phase 1: 基础组件库 (Day 1-2)
- [ ] 色彩体系和设计规范
- [ ] 质量得分仪表盘组件
- [ ] 多维度雷达图组件
- [ ] 趋势折线图组件
- [ ] 热力图组件

### Phase 2: 仪表盘布局 (Day 2-3)
- [ ] 主仪表盘布局实现
- [ ] 响应式设计适配
- [ ] 移动端优化
- [ ] 交互状态管理

### Phase 3: 报告模板 (Day 3-4)
- [ ] 执行摘要报告模板
- [ ] 详细技术报告模板
- [ ] 自定义报告构建器
- [ ] 报告数据绑定

### Phase 4: 交互功能 (Day 4-5)
- [ ] 工具提示系统
- [ ] 数据钻取功能
- [ ] 筛选和搜索
- [ ] 实时数据更新

### Phase 5: 导出分享 (Day 5-6)
- [ ] PDF/图片导出功能
- [ ] Excel数据导出
- [ ] 分享链接生成
- [ ] 性能优化和测试

---

**文档审核**: Analytics Reporter
**设计审核**: Visual Storyteller
**技术审核**: Backend Architect
**最后更新**: 2025-09-20
**版本**: v1.0