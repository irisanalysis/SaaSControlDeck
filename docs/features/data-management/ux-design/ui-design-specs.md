# UI Design Specifications - Data Management
## 数据管理功能界面设计规范

### Overview
This document defines the complete UI design specifications for the data quality management system, building on our existing Next.js + Radix UI + Tailwind CSS foundation.

---

## 🔌 Data Source Connection Interface

### Upload Zone Design
```tsx
// Primary Upload Area
<div className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 text-center hover:border-primary/50 transition-colors">
  <CloudUpload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
  <h3 className="text-lg font-semibold mb-2">Upload Your Data File</h3>
  <p className="text-muted-foreground mb-4">
    Drop your CSV, Excel, or JSON file here, or click to browse
  </p>
  <Button size="lg" className="mb-4">
    <Plus className="w-4 h-4 mr-2" />
    Choose File
  </Button>

  {/* Supported Formats */}
  <div className="flex justify-center gap-4 text-sm text-muted-foreground">
    <Badge variant="outline">.CSV</Badge>
    <Badge variant="outline">.XLSX</Badge>
    <Badge variant="outline">.JSON</Badge>
  </div>
</div>
```

### Upload Progress Indicator
```tsx
// Multi-stage Progress Component
<Card className="w-full">
  <CardContent className="p-6">
    <div className="flex items-center justify-between mb-4">
      <span className="font-medium">Processing your data...</span>
      <span className="text-sm text-muted-foreground">2 of 4 steps</span>
    </div>

    <Progress value={50} className="mb-4" />

    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <CheckCircle className="w-5 h-5 text-green-500" />
        <span className="text-sm">File uploaded successfully</span>
      </div>
      <div className="flex items-center gap-3">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
        <span className="text-sm">Analyzing data structure...</span>
      </div>
      <div className="flex items-center gap-3 opacity-50">
        <Circle className="w-5 h-5" />
        <span className="text-sm">Running quality assessment</span>
      </div>
      <div className="flex items-center gap-3 opacity-50">
        <Circle className="w-5 h-5" />
        <span className="text-sm">Generating insights</span>
      </div>
    </div>
  </CardContent>
</Card>
```

### Data Preview Table
```tsx
// Enhanced Data Preview
<Card className="w-full">
  <CardHeader>
    <div className="flex justify-between items-center">
      <div>
        <CardTitle>Data Preview</CardTitle>
        <CardDescription>
          Showing 10 of 1,247 rows • 8 columns detected
        </CardDescription>
      </div>
      <Button variant="outline" size="sm">
        <Eye className="w-4 h-4 mr-2" />
        View Full Dataset
      </Button>
    </div>
  </CardHeader>

  <CardContent>
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column) => (
              <TableHead key={column.id} className="relative">
                <div className="flex items-center gap-2">
                  <span>{column.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {column.type}
                  </Badge>
                  {column.hasIssues && (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  )}
                </div>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {previewData.map((row, index) => (
            <TableRow key={index}>
              {row.cells.map((cell, cellIndex) => (
                <TableCell key={cellIndex} className={cell.hasIssue ? "bg-red-50" : ""}>
                  {cell.value}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  </CardContent>
</Card>
```

---

## 📊 Quality Assessment Results Interface

### Four-Dimension Assessment Dashboard
```tsx
// Quality Dimensions Overview
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
  {qualityDimensions.map((dimension) => (
    <Card key={dimension.id} className="relative overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {dimension.icon}
              <h3 className="font-semibold">{dimension.name}</h3>
            </div>
            <p className="text-2xl font-bold mb-1">{dimension.score}%</p>
            <p className="text-sm text-muted-foreground">{dimension.status}</p>
          </div>
          <Badge variant={dimension.variant}>
            {dimension.level}
          </Badge>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <Progress
            value={dimension.score}
            className={`h-2 ${dimension.progressColor}`}
          />
        </div>

        {/* Issues Count */}
        {dimension.issuesCount > 0 && (
          <div className="mt-3 flex items-center gap-1 text-sm text-amber-600">
            <AlertCircle className="w-4 h-4" />
            <span>{dimension.issuesCount} issues found</span>
          </div>
        )}
      </CardContent>
    </Card>
  ))}
</div>
```

### Detailed Issues Breakdown
```tsx
// Issues Distribution Chart
<Card className="mb-6">
  <CardHeader>
    <CardTitle>Issue Distribution</CardTitle>
    <CardDescription>
      Detailed breakdown of data quality issues by category
    </CardDescription>
  </CardHeader>

  <CardContent>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={issueDistribution}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomizedLabel}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {issueDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend & Details */}
      <div className="space-y-3">
        {issueDistribution.map((issue, index) => (
          <div key={issue.name} className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: COLORS[index % COLORS.length] }}
              />
              <div>
                <p className="font-medium">{issue.name}</p>
                <p className="text-sm text-muted-foreground">{issue.description}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-semibold">{issue.value}</p>
              <p className="text-sm text-muted-foreground">{issue.percentage}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  </CardContent>
</Card>
```

### Column-Level Quality Heatmap
```tsx
// Quality Heatmap Component
<Card>
  <CardHeader>
    <CardTitle>Column Quality Heatmap</CardTitle>
    <CardDescription>
      Visual representation of data quality across all columns
    </CardDescription>
  </CardHeader>

  <CardContent>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      {columns.map((column) => (
        <div key={column.id} className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium truncate">{column.name}</span>
            <Badge variant="outline" className="text-xs">
              {column.type}
            </Badge>
          </div>

          <div className="space-y-1">
            {qualityMetrics.map((metric) => (
              <div key={metric.id} className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground w-20 truncate">
                  {metric.name}
                </span>
                <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${getQualityColor(column.metrics[metric.id])}`}
                    style={{ width: `${column.metrics[metric.id]}%` }}
                  />
                </div>
                <span className="text-xs w-8 text-right">
                  {column.metrics[metric.id]}%
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

---

## 🤖 AI Quality Analysis Interface

### AI Analysis Results Cards
```tsx
// Smart Insights Container
<div className="space-y-6">
  {aiInsights.map((insight, index) => (
    <Card key={insight.id} className="relative">
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className={`p-2 rounded-lg ${insight.iconBg}`}>
            {insight.icon}
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold">{insight.title}</h3>
              <Badge variant={insight.priority === 'high' ? 'destructive' :
                             insight.priority === 'medium' ? 'default' : 'secondary'}>
                {insight.priority} priority
              </Badge>
            </div>

            <p className="text-muted-foreground mb-4">{insight.description}</p>

            {/* Affected Columns */}
            <div className="flex flex-wrap gap-2 mb-4">
              {insight.affectedColumns.map((column) => (
                <Badge key={column} variant="outline" className="text-xs">
                  {column}
                </Badge>
              ))}
            </div>

            {/* Recommendations */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-blue-600" />
                AI Recommendation
              </h4>
              <p className="text-sm text-blue-800 mb-3">{insight.recommendation}</p>

              <div className="flex gap-2">
                <Button size="sm" variant="default">
                  <Wand2 className="w-4 h-4 mr-2" />
                  Apply Fix
                </Button>
                <Button size="sm" variant="outline">
                  Learn More
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  ))}
</div>
```

### Interactive AI Chat Interface
```tsx
// AI Assistant Chat
<Card className="h-96 flex flex-col">
  <CardHeader className="border-b">
    <div className="flex items-center gap-3">
      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div>
        <CardTitle className="text-lg">AI Data Quality Assistant</CardTitle>
        <CardDescription>Ask questions about your data quality</CardDescription>
      </div>
    </div>
  </CardHeader>

  <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
    {chatMessages.map((message, index) => (
      <div key={index} className={`flex gap-3 ${message.isUser ? 'justify-end' : ''}`}>
        {!message.isUser && (
          <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
            <Bot className="w-3 h-3 text-blue-600" />
          </div>
        )}

        <div className={`max-w-[80%] p-3 rounded-lg ${
          message.isUser
            ? 'bg-primary text-primary-foreground'
            : 'bg-muted'
        }`}>
          <p className="text-sm">{message.content}</p>
          {message.suggestions && (
            <div className="mt-2 space-y-1">
              {message.suggestions.map((suggestion, i) => (
                <Button key={i} variant="ghost" size="sm" className="text-xs h-6">
                  {suggestion}
                </Button>
              ))}
            </div>
          )}
        </div>

        {message.isUser && (
          <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
            <User className="w-3 h-3 text-gray-600" />
          </div>
        )}
      </div>
    ))}
  </CardContent>

  <div className="border-t p-4">
    <div className="flex gap-2">
      <Input
        placeholder="Ask about your data quality..."
        className="flex-1"
        value={chatInput}
        onChange={(e) => setChatInput(e.target.value)}
      />
      <Button size="sm">
        <Send className="w-4 h-4" />
      </Button>
    </div>

    {/* Quick Questions */}
    <div className="flex flex-wrap gap-2 mt-2">
      {quickQuestions.map((question) => (
        <Button key={question} variant="ghost" size="sm" className="text-xs h-6">
          {question}
        </Button>
      ))}
    </div>
  </div>
</Card>
```

---

## 📈 Data Scoring Dashboard Interface

### Comprehensive Score Display
```tsx
// Main Score Dashboard
<div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
  {/* Overall Score */}
  <Card className="lg:col-span-2">
    <CardContent className="p-8 text-center">
      <div className="relative w-40 h-40 mx-auto mb-6">
        <svg className="transform -rotate-90 w-40 h-40">
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-gray-200"
          />
          <circle
            cx="80"
            cy="80"
            r="70"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={`${2 * Math.PI * 70}`}
            strokeDashoffset={`${2 * Math.PI * 70 * (1 - overallScore / 100)}`}
            className="text-primary transition-all duration-1000 ease-out"
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div>
            <div className="text-4xl font-bold text-primary">{overallScore}</div>
            <div className="text-sm text-muted-foreground">Overall Score</div>
          </div>
        </div>
      </div>

      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Data Quality Assessment</h2>
        <p className="text-muted-foreground">
          Your data quality is <span className="font-semibold text-primary">Good</span>
        </p>
      </div>
    </CardContent>
  </Card>

  {/* Quick Stats */}
  <div className="space-y-4">
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Records Analyzed</p>
            <p className="text-2xl font-bold">1,247</p>
          </div>
          <Database className="w-8 h-8 text-blue-500" />
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Issues Found</p>
            <p className="text-2xl font-bold text-amber-600">23</p>
          </div>
          <AlertTriangle className="w-8 h-8 text-amber-500" />
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Clean Records</p>
            <p className="text-2xl font-bold text-green-600">98.2%</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>
      </CardContent>
    </Card>
  </div>
</div>
```

### Radar Chart for Dimensions
```tsx
// Quality Dimensions Radar
<Card>
  <CardHeader>
    <CardTitle>Quality Dimensions Analysis</CardTitle>
    <CardDescription>
      Comprehensive view of all quality aspects
    </CardDescription>
  </CardHeader>

  <CardContent>
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
          <PolarGrid />
          <PolarAngleAxis dataKey="dimension" className="text-sm" />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
          />
          <Radar
            name="Current Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.1}
            strokeWidth={2}
          />
          <Radar
            name="Industry Average"
            dataKey="industryAverage"
            stroke="#e5e7eb"
            fill="transparent"
            strokeWidth={1}
            strokeDasharray="5 5"
          />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    </div>

    {/* Legend */}
    <div className="flex justify-center gap-6 mt-4">
      <div className="flex items-center gap-2">
        <div className="w-3 h-3 bg-blue-500 rounded"></div>
        <span className="text-sm">Your Data</span>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-3 h-1 bg-gray-300"></div>
        <span className="text-sm">Industry Average</span>
      </div>
    </div>
  </CardContent>
</Card>
```

### Industry Comparison Section
```tsx
// Industry Benchmarking
<Card>
  <CardHeader>
    <CardTitle>Industry Comparison</CardTitle>
    <CardDescription>
      See how your data quality compares to industry standards
    </CardDescription>
  </CardHeader>

  <CardContent>
    <div className="space-y-6">
      {industryMetrics.map((metric) => (
        <div key={metric.name} className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="font-medium">{metric.name}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                You: {metric.yourScore}%
              </span>
              <span className="text-sm text-muted-foreground">
                Industry: {metric.industryAverage}%
              </span>
            </div>
          </div>

          <div className="relative">
            <Progress value={metric.industryAverage} className="h-3 bg-gray-200" />
            <div
              className="absolute top-0 h-3 bg-primary rounded-full"
              style={{ width: `${metric.yourScore}%` }}
            />
            <div
              className="absolute -top-1 w-1 h-5 bg-gray-600"
              style={{ left: `${metric.industryAverage}%` }}
            />
          </div>

          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Poor</span>
            <span>Average</span>
            <span>Excellent</span>
          </div>
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

---

## 🎨 Design System Integration

### Component Variants
```tsx
// Quality Level Badges
const qualityBadgeVariants = {
  excellent: "bg-green-100 text-green-800 border-green-200",
  good: "bg-blue-100 text-blue-800 border-blue-200",
  fair: "bg-yellow-100 text-yellow-800 border-yellow-200",
  poor: "bg-red-100 text-red-800 border-red-200"
}

// Progress Bar Colors
const qualityProgressColors = {
  excellent: "bg-green-500",
  good: "bg-blue-500",
  fair: "bg-yellow-500",
  poor: "bg-red-500"
}

// Icon Mappings
const qualityIcons = {
  completeness: <Database className="w-5 h-5" />,
  accuracy: <Target className="w-5 h-5" />,
  consistency: <Layers className="w-5 h-5" />,
  validity: <Shield className="w-5 h-5" />
}
```

### Responsive Layout Patterns
```tsx
// Mobile-First Grid System
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {/* Responsive card layout */}
</div>

// Mobile Navigation
<div className="lg:hidden">
  <Sheet>
    <SheetTrigger asChild>
      <Button variant="ghost" size="sm">
        <Menu className="w-4 h-4" />
      </Button>
    </SheetTrigger>
    <SheetContent side="left">
      {/* Mobile menu content */}
    </SheetContent>
  </Sheet>
</div>
```

### Accessibility Features
```tsx
// Screen Reader Support
<div role="region" aria-label="Data Quality Assessment Results">
  <h2 className="sr-only">Quality Assessment Summary</h2>
  {/* Content */}
</div>

// Keyboard Navigation
<Button
  onKeyDown={(e) => e.key === 'Enter' && handleAction()}
  aria-describedby="action-description"
>
  Apply Recommendation
</Button>

// High Contrast Mode Support
<div className="contrast-more:border-2 contrast-more:border-black">
  {/* High contrast enhanced content */}
</div>
```

---

## 📱 Mobile Optimization

### Mobile-Specific Components
```tsx
// Mobile Score Card
<Card className="sm:hidden">
  <CardContent className="p-4">
    <div className="text-center">
      <div className="text-3xl font-bold text-primary mb-1">{score}%</div>
      <div className="text-sm text-muted-foreground mb-3">Overall Quality</div>
      <Progress value={score} className="h-2" />
    </div>
  </CardContent>
</Card>

// Mobile Data Table
<div className="sm:hidden space-y-3">
  {data.map((row, index) => (
    <Card key={index} className="p-4">
      {Object.entries(row).map(([key, value]) => (
        <div key={key} className="flex justify-between py-1">
          <span className="text-sm text-muted-foreground">{key}</span>
          <span className="text-sm font-medium">{value}</span>
        </div>
      ))}
    </Card>
  ))}
</div>
```

This comprehensive UI design specification provides a complete foundation for building the data management interface. Each component is designed to work seamlessly with our existing Radix UI + Tailwind CSS system while providing an intuitive and professional user experience.