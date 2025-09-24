# Data Visualization Specifications - Data Management
## 数据可视化规范设计

### Overview
This document defines comprehensive data visualization specifications for the data quality management platform, focusing on clear communication of quality metrics, trends, and actionable insights through professional charts and interactive dashboards.

---

## 📊 Chart Component Library

### 1. Quality Score Visualizations

#### Circular Progress (Donut Chart)
```tsx
// Quality Score Circle Component
import { ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const QualityScoreCircle = ({
  score,
  size = 120,
  strokeWidth = 12,
  quality = 'good',
  animated = true
}) => {
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score }
  ];

  const getColors = (quality) => {
    const colorMap = {
      excellent: { active: '#22c55e', inactive: '#f0fdf4' },
      good: { active: '#3b82f6', inactive: '#eff6ff' },
      fair: { active: '#f59e0b', inactive: '#fffbeb' },
      poor: { active: '#ef4444', inactive: '#fef2f2' }
    };
    return colorMap[quality] || colorMap.good;
  };

  const colors = getColors(quality);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={size * 0.3}
            outerRadius={size * 0.45}
            startAngle={90}
            endAngle={-270}
            dataKey="value"
            strokeWidth={0}
            animationBegin={0}
            animationDuration={animated ? 1500 : 0}
          >
            <Cell fill={colors.active} />
            <Cell fill={colors.inactive} />
          </Pie>
        </PieChart>
      </ResponsiveContainer>

      {/* Center Score Display */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{score}%</div>
          <div className="text-xs text-gray-500 uppercase tracking-wide">
            {quality}
          </div>
        </div>
      </div>
    </div>
  );
};
```

#### Quality Dimensions Radar Chart
```tsx
// Multi-Dimensional Quality Radar
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const QualityRadarChart = ({
  data,
  industryBenchmark,
  height = 300,
  showBenchmark = true
}) => {
  const radarData = [
    {
      dimension: 'Completeness',
      score: data.completeness,
      benchmark: industryBenchmark?.completeness || 75,
      fullName: 'Data Completeness'
    },
    {
      dimension: 'Accuracy',
      score: data.accuracy,
      benchmark: industryBenchmark?.accuracy || 80,
      fullName: 'Data Accuracy'
    },
    {
      dimension: 'Consistency',
      score: data.consistency,
      benchmark: industryBenchmark?.consistency || 70,
      fullName: 'Data Consistency'
    },
    {
      dimension: 'Validity',
      score: data.validity,
      benchmark: industryBenchmark?.validity || 85,
      fullName: 'Data Validity'
    }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-2">{data.fullName}</h4>
          <div className="space-y-1">
            <div className="flex justify-between gap-4 text-sm">
              <span className="text-blue-600">Your Score:</span>
              <span className="font-medium">{data.score}%</span>
            </div>
            {showBenchmark && (
              <div className="flex justify-between gap-4 text-sm">
                <span className="text-gray-500">Industry Avg:</span>
                <span className="font-medium">{data.benchmark}%</span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={radarData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <PolarGrid
            stroke="#e2e8f0"
            strokeWidth={1}
            radialLines={true}
          />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fontSize: 12, fill: '#64748b' }}
            className="text-sm"
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            tickCount={5}
          />

          {/* Industry Benchmark */}
          {showBenchmark && (
            <Radar
              name="Industry Average"
              dataKey="benchmark"
              stroke="#cbd5e1"
              fill="transparent"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
            />
          )}

          {/* Your Score */}
          <Radar
            name="Your Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f680"
            strokeWidth={3}
            fillOpacity={0.1}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
          />

          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 2. Issue Distribution Charts

#### Issue Category Breakdown (Treemap)
```tsx
// Hierarchical Issue Visualization
import { ResponsiveContainer, Treemap } from 'recharts';

const IssueTreemap = ({ issueData, width = 400, height = 300 }) => {
  const processedData = issueData.map(category => ({
    name: category.name,
    size: category.count,
    children: category.subCategories?.map(sub => ({
      name: sub.name,
      size: sub.count,
      severity: sub.severity
    }))
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-1">{data.name}</h4>
          <p className="text-sm text-gray-600">
            {data.size} issues
            {data.severity && (
              <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                data.severity === 'high' ? 'bg-red-100 text-red-800' :
                data.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-green-100 text-green-800'
              }`}>
                {data.severity}
              </span>
            )}
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomContent = ({ depth, x, y, width, height, name, size, severity }) => {
    const getSeverityColor = (severity) => {
      const colors = {
        high: '#fee2e2',
        medium: '#fef3c7',
        low: '#dcfce7',
        default: '#f1f5f9'
      };
      return colors[severity] || colors.default;
    };

    return (
      <g>
        <rect
          x={x}
          y={y}
          width={width}
          height={height}
          fill={getSeverityColor(severity)}
          stroke="#ffffff"
          strokeWidth={2}
          rx={4}
        />
        {width > 60 && height > 40 && (
          <text
            x={x + width / 2}
            y={y + height / 2}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={Math.min(width / 8, height / 4, 12)}
            fill="#374151"
            className="font-medium"
          >
            {name}
          </text>
        )}
        {width > 80 && height > 60 && (
          <text
            x={x + width / 2}
            y={y + height / 2 + 16}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={10}
            fill="#6b7280"
          >
            {size} issues
          </text>
        )}
      </g>
    );
  };

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={processedData}
          dataKey="size"
          aspectRatio={4/3}
          stroke="#ffffff"
          content={<CustomContent />}
        >
          <Tooltip content={<CustomTooltip />} />
        </Treemap>
      </ResponsiveContainer>
    </div>
  );
};
```

#### Issue Severity Distribution (Stacked Bar)
```tsx
// Severity-Based Issue Analysis
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const SeverityDistributionChart = ({ data, height = 300 }) => {
  const chartData = data.map(column => ({
    column: column.name.length > 10 ? column.name.substring(0, 10) + '...' : column.name,
    fullName: column.name,
    high: column.issues.high || 0,
    medium: column.issues.medium || 0,
    low: column.issues.low || 0,
    total: (column.issues.high || 0) + (column.issues.medium || 0) + (column.issues.low || 0)
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-2">{data.fullName}</h4>
          <div className="space-y-1">
            <div className="flex justify-between gap-4 text-sm">
              <span className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded"></div>
                High Severity:
              </span>
              <span className="font-medium">{data.high}</span>
            </div>
            <div className="flex justify-between gap-4 text-sm">
              <span className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                Medium Severity:
              </span>
              <span className="font-medium">{data.medium}</span>
            </div>
            <div className="flex justify-between gap-4 text-sm">
              <span className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded"></div>
                Low Severity:
              </span>
              <span className="font-medium">{data.low}</span>
            </div>
            <div className="border-t pt-1 flex justify-between gap-4 text-sm font-medium">
              <span>Total Issues:</span>
              <span>{data.total}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="column"
            angle={-45}
            textAnchor="end"
            height={80}
            fontSize={12}
            stroke="#64748b"
          />
          <YAxis
            fontSize={12}
            stroke="#64748b"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            height={36}
            iconType="rect"
          />
          <Bar
            dataKey="high"
            stackId="a"
            fill="#ef4444"
            name="High Severity"
            radius={[0, 0, 0, 0]}
          />
          <Bar
            dataKey="medium"
            stackId="a"
            fill="#f59e0b"
            name="Medium Severity"
            radius={[0, 0, 0, 0]}
          />
          <Bar
            dataKey="low"
            stackId="a"
            fill="#22c55e"
            name="Low Severity"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 3. Trend Analysis Charts

#### Quality Score Timeline
```tsx
// Historical Quality Trends
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, AreaChart } from 'recharts';

const QualityTrendChart = ({
  data,
  timeRange = '30d',
  showProjection = true,
  height = 300
}) => {
  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-2">{formatDate(label)}</h4>
          <div className="space-y-1">
            {payload.map((entry, index) => (
              <div key={index} className="flex justify-between gap-4 text-sm">
                <span className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{ backgroundColor: entry.color }}
                  ></div>
                  {entry.name}:
                </span>
                <span className="font-medium">{entry.value}%</span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomDot = ({ cx, cy, payload, dataKey }) => {
    if (payload.isProjection) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={3}
          fill="none"
          stroke="#8b5cf6"
          strokeWidth={2}
          strokeDasharray="2 2"
        />
      );
    }
    return null;
  };

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <defs>
            <linearGradient id="qualityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="projectionGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />

          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            fontSize={12}
            stroke="#64748b"
          />

          <YAxis
            domain={[0, 100]}
            fontSize={12}
            stroke="#64748b"
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Historical Data */}
          <Area
            type="monotone"
            dataKey="overallScore"
            stroke="#3b82f6"
            strokeWidth={3}
            fill="url(#qualityGradient)"
            fillOpacity={1}
            connectNulls={false}
            name="Overall Quality"
          />

          {/* Projection */}
          {showProjection && (
            <Area
              type="monotone"
              dataKey="projectedScore"
              stroke="#8b5cf6"
              strokeWidth={2}
              strokeDasharray="8 4"
              fill="url(#projectionGradient)"
              fillOpacity={1}
              connectNulls={false}
              name="Projected Quality"
              dot={<CustomDot />}
            />
          )}

          {/* Individual Dimensions */}
          <Line
            type="monotone"
            dataKey="completeness"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
            name="Completeness"
          />
          <Line
            type="monotone"
            dataKey="accuracy"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            name="Accuracy"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 4. Comparative Analysis Charts

#### Industry Benchmark Comparison
```tsx
// Multi-Metric Comparison Chart
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

const BenchmarkComparisonChart = ({
  data,
  industry = 'Technology',
  height = 350
}) => {
  const chartData = [
    {
      metric: 'Overall Quality',
      yourScore: data.overall,
      industryAvg: data.benchmarks.industry,
      topQuartile: data.benchmarks.topQuartile,
      category: 'overall'
    },
    {
      metric: 'Completeness',
      yourScore: data.completeness,
      industryAvg: data.benchmarks.completeness,
      topQuartile: data.benchmarks.completenessTop,
      category: 'dimension'
    },
    {
      metric: 'Accuracy',
      yourScore: data.accuracy,
      industryAvg: data.benchmarks.accuracy,
      topQuartile: data.benchmarks.accuracyTop,
      category: 'dimension'
    },
    {
      metric: 'Consistency',
      yourScore: data.consistency,
      industryAvg: data.benchmarks.consistency,
      topQuartile: data.benchmarks.consistencyTop,
      category: 'dimension'
    },
    {
      metric: 'Validity',
      yourScore: data.validity,
      industryAvg: data.benchmarks.validity,
      topQuartile: data.benchmarks.validityTop,
      category: 'dimension'
    }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-3">{label}</h4>
          <div className="space-y-2">
            {payload.map((entry, index) => {
              const performance = entry.dataKey === 'yourScore' ?
                entry.value > payload.find(p => p.dataKey === 'industryAvg')?.value ? 'above' : 'below' : null;

              return (
                <div key={index} className="flex justify-between gap-4 text-sm">
                  <span className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded"
                      style={{ backgroundColor: entry.color }}
                    ></div>
                    {entry.name}:
                  </span>
                  <span className={`font-medium ${
                    performance === 'above' ? 'text-green-600' :
                    performance === 'below' ? 'text-red-600' :
                    'text-gray-900'
                  }`}>
                    {entry.value}%
                  </span>
                </div>
              );
            })}
          </div>
          {payload[0] && (
            <div className="border-t pt-2 mt-3">
              <div className="text-xs text-gray-600">
                Industry: {industry}
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          barGap={10}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />

          <XAxis
            dataKey="metric"
            angle={-45}
            textAnchor="end"
            height={80}
            fontSize={12}
            stroke="#64748b"
          />

          <YAxis
            domain={[0, 100]}
            fontSize={12}
            stroke="#64748b"
          />

          <Tooltip content={<CustomTooltip />} />

          <Legend
            verticalAlign="top"
            height={36}
            iconType="rect"
          />

          {/* Top Quartile Reference */}
          <Bar
            dataKey="topQuartile"
            fill="#e5e7eb"
            name="Top 25%"
            radius={[2, 2, 0, 0]}
          />

          {/* Industry Average */}
          <Bar
            dataKey="industryAvg"
            fill="#9ca3af"
            name="Industry Average"
            radius={[2, 2, 0, 0]}
          />

          {/* Your Score */}
          <Bar
            dataKey="yourScore"
            fill="#3b82f6"
            name="Your Score"
            radius={[2, 2, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

---

## 🎛️ Interactive Dashboard Components

### 1. Quality Overview Dashboard

#### Executive Summary Widget
```tsx
// High-Level KPI Dashboard
const ExecutiveSummary = ({ data, period = '30d' }) => {
  const kpis = [
    {
      label: 'Overall Quality Score',
      value: data.overallScore,
      change: data.scoreChange,
      trend: data.scoreTrend,
      format: 'percentage',
      color: data.overallScore >= 80 ? 'green' : data.overallScore >= 60 ? 'yellow' : 'red'
    },
    {
      label: 'Issues Resolved',
      value: data.issuesResolved,
      change: data.issuesResolvedChange,
      trend: 'up',
      format: 'number',
      color: 'blue'
    },
    {
      label: 'Data Completeness',
      value: data.completeness,
      change: data.completenessChange,
      trend: data.completenessTrend,
      format: 'percentage',
      color: data.completeness >= 90 ? 'green' : 'yellow'
    },
    {
      label: 'Clean Records',
      value: data.cleanRecords,
      change: data.cleanRecordsChange,
      trend: data.cleanRecordsTrend,
      format: 'percentage',
      color: 'green'
    }
  ];

  const formatValue = (value, format) => {
    if (format === 'percentage') return `${value}%`;
    if (format === 'number') return value.toLocaleString();
    return value;
  };

  const getChangeColor = (change, trend) => {
    if (change > 0 && trend === 'up') return 'text-green-600';
    if (change < 0 && trend === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change, trend) => {
    if (change > 0 && trend === 'up') return <TrendingUp className="w-4 h-4" />;
    if (change < 0 && trend === 'down') return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {kpis.map((kpi, index) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm text-muted-foreground mb-1">{kpi.label}</p>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-2xl font-bold text-${kpi.color}-600`}>
                      {formatValue(kpi.value, kpi.format)}
                    </span>
                    {kpi.change !== 0 && (
                      <div className={`flex items-center gap-1 text-sm ${getChangeColor(kpi.change, kpi.trend)}`}>
                        {getChangeIcon(kpi.change, kpi.trend)}
                        <span>{Math.abs(kpi.change)}%</span>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">vs last {period}</p>
                </div>

                {/* Mini Chart */}
                <div className="w-16 h-12">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={kpi.sparklineData || []}>
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke={`var(--${kpi.color}-500)`}
                        fill={`var(--${kpi.color}-100)`}
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};
```

### 2. Column-Level Quality Heatmap

#### Interactive Quality Matrix
```tsx
// Column Quality Heatmap Component
const QualityHeatmap = ({
  columns,
  metrics = ['completeness', 'accuracy', 'consistency', 'validity'],
  onCellClick
}) => {
  const [hoveredCell, setHoveredCell] = useState(null);
  const [selectedColumn, setSelectedColumn] = useState(null);

  const getIntensityColor = (score) => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 75) return 'bg-green-400';
    if (score >= 60) return 'bg-yellow-400';
    if (score >= 40) return 'bg-orange-400';
    if (score >= 20) return 'bg-red-400';
    return 'bg-red-500';
  };

  const getIntensityOpacity = (score) => {
    return Math.max(0.3, score / 100);
  };

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-full">
        {/* Header */}
        <div className="flex">
          <div className="w-48 p-3 font-medium text-sm bg-gray-50 border-b border-r">
            Column Name
          </div>
          {metrics.map(metric => (
            <div
              key={metric}
              className="flex-1 min-w-24 p-3 text-center font-medium text-sm bg-gray-50 border-b capitalize"
            >
              {metric}
            </div>
          ))}
          <div className="w-20 p-3 text-center font-medium text-sm bg-gray-50 border-b border-l">
            Overall
          </div>
        </div>

        {/* Data Rows */}
        {columns.map((column, rowIndex) => (
          <div
            key={column.name}
            className={`flex ${selectedColumn === column.name ? 'bg-blue-50' : ''}`}
          >
            {/* Column Name */}
            <div
              className="w-48 p-3 border-b border-r cursor-pointer hover:bg-gray-50"
              onClick={() => setSelectedColumn(
                selectedColumn === column.name ? null : column.name
              )}
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium truncate" title={column.name}>
                  {column.name}
                </span>
                <Badge variant="outline" className="text-xs">
                  {column.type}
                </Badge>
              </div>
            </div>

            {/* Metric Cells */}
            {metrics.map(metric => {
              const score = column.quality[metric];
              const cellKey = `${rowIndex}-${metric}`;
              const isHovered = hoveredCell === cellKey;

              return (
                <div
                  key={metric}
                  className="flex-1 min-w-24 p-3 border-b cursor-pointer relative"
                  onMouseEnter={() => setHoveredCell(cellKey)}
                  onMouseLeave={() => setHoveredCell(null)}
                  onClick={() => onCellClick?.(column.name, metric, score)}
                >
                  <div
                    className={`
                      w-full h-8 rounded flex items-center justify-center text-white text-sm font-medium
                      transition-all duration-200 ${getIntensityColor(score)}
                      ${isHovered ? 'scale-105 shadow-lg' : ''}
                    `}
                    style={{ opacity: getIntensityOpacity(score) }}
                  >
                    {score}%
                  </div>

                  {/* Hover Tooltip */}
                  {isHovered && (
                    <div className="absolute z-10 bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                      <div className="bg-black text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                        {column.name} - {metric}: {score}%
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-black"></div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Overall Score */}
            <div className="w-20 p-3 border-b border-l text-center">
              <div className={`
                inline-flex items-center justify-center w-12 h-8 rounded text-white text-sm font-medium
                ${getIntensityColor(column.overallScore)}
              `}>
                {column.overallScore}%
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-4 text-sm">
        <span className="text-gray-600">Quality Score:</span>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Poor (0-40%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-400 rounded"></div>
          <span>Fair (40-75%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-400 rounded"></div>
          <span>Good (75-90%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Excellent (90%+)</span>
        </div>
      </div>
    </div>
  );
};
```

---

## 📈 Advanced Chart Patterns

### 1. Multi-Series Time Analysis

#### Quality Dimension Trends
```tsx
// Multi-Line Quality Trends
const QualityDimensionTrends = ({
  data,
  selectedDimensions = ['completeness', 'accuracy', 'consistency', 'validity'],
  height = 400
}) => {
  const [visibleLines, setVisibleLines] = useState(new Set(selectedDimensions));

  const dimensionColors = {
    completeness: '#3b82f6',
    accuracy: '#10b981',
    consistency: '#8b5cf6',
    validity: '#f59e0b'
  };

  const toggleLine = (dimension) => {
    const newVisible = new Set(visibleLines);
    if (newVisible.has(dimension)) {
      newVisible.delete(dimension);
    } else {
      newVisible.add(dimension);
    }
    setVisibleLines(newVisible);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <h4 className="font-medium text-sm mb-3">
            {new Date(label).toLocaleDateString()}
          </h4>
          <div className="space-y-2">
            {payload
              .filter(entry => visibleLines.has(entry.dataKey))
              .map((entry, index) => (
                <div key={index} className="flex justify-between gap-6 text-sm">
                  <span className="flex items-center gap-2 capitalize">
                    <div
                      className="w-3 h-3 rounded"
                      style={{ backgroundColor: entry.color }}
                    ></div>
                    {entry.dataKey}:
                  </span>
                  <span className="font-medium">{entry.value}%</span>
                </div>
              ))}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Legend with Toggle */}
      <div className="flex flex-wrap gap-4">
        {selectedDimensions.map(dimension => (
          <button
            key={dimension}
            onClick={() => toggleLine(dimension)}
            className={`
              flex items-center gap-2 px-3 py-1 rounded-full text-sm transition-all
              ${visibleLines.has(dimension)
                ? 'bg-gray-100 text-gray-900'
                : 'bg-gray-50 text-gray-400'
              }
            `}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: dimensionColors[dimension] }}
            ></div>
            <span className="capitalize">{dimension}</span>
          </button>
        ))}
      </div>

      {/* Chart */}
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />

            <XAxis
              dataKey="date"
              tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              fontSize={12}
              stroke="#64748b"
            />

            <YAxis
              domain={[0, 100]}
              fontSize={12}
              stroke="#64748b"
            />

            <Tooltip content={<CustomTooltip />} />

            {selectedDimensions.map(dimension => (
              <Line
                key={dimension}
                type="monotone"
                dataKey={dimension}
                stroke={dimensionColors[dimension]}
                strokeWidth={visibleLines.has(dimension) ? 3 : 0}
                dot={false}
                connectNulls={false}
                strokeDasharray={visibleLines.has(dimension) ? "0" : "0"}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
```

### 2. Data Quality Correlation Matrix

#### Correlation Heatmap
```tsx
// Quality Metrics Correlation
const CorrelationMatrix = ({ correlationData, height = 300 }) => {
  const metrics = ['completeness', 'accuracy', 'consistency', 'validity'];

  const getCorrelationColor = (value) => {
    const intensity = Math.abs(value);
    if (value > 0) {
      return `rgba(34, 197, 94, ${intensity})`; // Green for positive correlation
    } else {
      return `rgba(239, 68, 68, ${intensity})`; // Red for negative correlation
    }
  };

  const formatCorrelation = (value) => {
    return value.toFixed(2);
  };

  return (
    <div className="w-full">
      <div className="grid grid-cols-5 gap-1 mb-4">
        {/* Header row */}
        <div></div>
        {metrics.map(metric => (
          <div key={metric} className="text-center text-sm font-medium p-2 capitalize">
            {metric}
          </div>
        ))}

        {/* Data rows */}
        {metrics.map(rowMetric => (
          <React.Fragment key={rowMetric}>
            <div className="text-sm font-medium p-2 capitalize text-right">
              {rowMetric}
            </div>
            {metrics.map(colMetric => {
              const correlation = correlationData[rowMetric]?.[colMetric] ?? 0;
              const isIdentity = rowMetric === colMetric;

              return (
                <div
                  key={colMetric}
                  className="aspect-square flex items-center justify-center text-xs font-medium rounded"
                  style={{
                    backgroundColor: isIdentity ? '#f3f4f6' : getCorrelationColor(correlation),
                    color: Math.abs(correlation) > 0.5 ? 'white' : '#374151'
                  }}
                  title={`${rowMetric} vs ${colMetric}: ${formatCorrelation(correlation)}`}
                >
                  {formatCorrelation(correlation)}
                </div>
              );
            })}
          </React.Fragment>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>Negative Correlation</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-200 rounded"></div>
          <span>No Correlation</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Positive Correlation</span>
        </div>
      </div>
    </div>
  );
};
```

---

## 🎨 Chart Styling Guidelines

### Color Palettes
```css
/* Primary Quality Colors */
:root {
  --excellent: #22c55e;
  --good: #3b82f6;
  --fair: #f59e0b;
  --poor: #ef4444;
  --processing: #8b5cf6;
}

/* Chart Series Colors */
:root {
  --chart-1: #3b82f6;   /* Blue */
  --chart-2: #8b5cf6;   /* Purple */
  --chart-3: #10b981;   /* Emerald */
  --chart-4: #f59e0b;   /* Amber */
  --chart-5: #ef4444;   /* Red */
  --chart-6: #06b6d4;   /* Cyan */
}

/* Semantic Colors */
:root {
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
  --neutral: #6b7280;
}
```

### Typography for Charts
```css
/* Chart Text Styles */
.chart-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.5rem;
}

.chart-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 1rem;
}

.chart-axis-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.chart-legend {
  font-size: 0.75rem;
  color: #374151;
}

.chart-tooltip-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 0.5rem;
}

.chart-tooltip-value {
  font-size: 0.75rem;
  color: #374151;
}
```

### Responsive Chart Containers
```css
/* Responsive Chart Breakpoints */
.chart-container-sm {
  height: 200px;
}

.chart-container-md {
  height: 300px;
}

.chart-container-lg {
  height: 400px;
}

.chart-container-xl {
  height: 500px;
}

/* Mobile Optimizations */
@media (max-width: 640px) {
  .chart-container-responsive {
    height: 250px;
  }

  .chart-axis-label {
    font-size: 0.625rem;
  }

  .chart-legend {
    font-size: 0.625rem;
  }
}

/* Tablet Optimizations */
@media (min-width: 641px) and (max-width: 1024px) {
  .chart-container-responsive {
    height: 350px;
  }
}

/* Desktop Optimizations */
@media (min-width: 1025px) {
  .chart-container-responsive {
    height: 400px;
  }
}
```

This comprehensive data visualization specification provides a complete toolkit for creating professional, accessible, and insightful charts for the data quality management platform. Each component is designed to work seamlessly with our existing design system while providing clear communication of complex data quality metrics.