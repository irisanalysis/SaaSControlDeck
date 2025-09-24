# Responsive Design Guide - Data Management
## 响应式设计指南

### Overview
This document provides comprehensive responsive design guidelines for the data quality management platform, ensuring optimal user experience across all devices from mobile phones to large desktop displays.

---

## 📱 Breakpoint System

### Tailwind CSS Breakpoints
```css
/* Standard Tailwind CSS Breakpoints */
/* xs: default (0px and up) */
/* sm: 640px and up */
/* md: 768px and up */
/* lg: 1024px and up */
/* xl: 1280px and up */
/* 2xl: 1536px and up */

/* Custom Breakpoints for Data Management */
@media (max-width: 480px) {
  /* Extra small mobile devices */
}

@media (min-width: 481px) and (max-width: 640px) {
  /* Large mobile devices */
}

@media (min-width: 641px) and (max-width: 768px) {
  /* Small tablets */
}

@media (min-width: 769px) and (max-width: 1024px) {
  /* Large tablets / Small laptops */
}

@media (min-width: 1025px) and (max-width: 1280px) {
  /* Desktop */
}

@media (min-width: 1281px) {
  /* Large desktop */
}
```

### Device-Specific Considerations
```tsx
// Device Detection Hook
const useDeviceType = () => {
  const [deviceType, setDeviceType] = useState('desktop');

  useEffect(() => {
    const checkDevice = () => {
      const width = window.innerWidth;
      if (width < 640) setDeviceType('mobile');
      else if (width < 1024) setDeviceType('tablet');
      else setDeviceType('desktop');
    };

    checkDevice();
    window.addEventListener('resize', checkDevice);
    return () => window.removeEventListener('resize', checkDevice);
  }, []);

  return deviceType;
};

// Usage in Components
const DataManagementDashboard = () => {
  const deviceType = useDeviceType();

  return (
    <div className={`
      ${deviceType === 'mobile' ? 'p-4 space-y-4' : ''}
      ${deviceType === 'tablet' ? 'p-6 space-y-6' : ''}
      ${deviceType === 'desktop' ? 'p-8 space-y-8' : ''}
    `}>
      {/* Responsive content */}
    </div>
  );
};
```

---

## 📐 Layout Adaptations

### 1. Grid System Responsive Patterns

#### Dashboard Grid Layout
```tsx
// Responsive Dashboard Grid
const ResponsiveDashboardGrid = ({ children }) => {
  return (
    <div className="
      grid gap-4
      grid-cols-1
      sm:grid-cols-2
      lg:grid-cols-3
      xl:grid-cols-4
      2xl:grid-cols-6
    ">
      {children}
    </div>
  );
};

// Quality Dimensions Grid
const QualityDimensionsGrid = ({ dimensions }) => {
  return (
    <div className="
      grid gap-4
      grid-cols-1
      sm:grid-cols-2
      lg:grid-cols-4
    ">
      {dimensions.map(dimension => (
        <QualityDimensionCard key={dimension.id} dimension={dimension} />
      ))}
    </div>
  );
};

// Chart Layout Grid
const ChartsGrid = ({ charts }) => {
  return (
    <div className="
      grid gap-6
      grid-cols-1
      lg:grid-cols-2
      2xl:grid-cols-3
    ">
      {charts.map(chart => (
        <Card key={chart.id} className="p-6">
          {chart.component}
        </Card>
      ))}
    </div>
  );
};
```

#### Content Area Layouts
```tsx
// Main Content with Sidebar
const ResponsiveContentLayout = ({ sidebar, main, details }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen">
      {/* Mobile Sidebar Overlay */}
      <div className={`
        lg:hidden fixed inset-0 z-50 transition-opacity
        ${sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
      `}>
        <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
        <div className="absolute left-0 top-0 h-full w-80 bg-white shadow-xl">
          {sidebar}
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-80 lg:flex-col lg:border-r">
        {sidebar}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </Button>
          <h1 className="font-semibold">Data Quality</h1>
          <div className="w-8" /> {/* Spacer */}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="
            p-4 sm:p-6 lg:p-8
            max-w-none lg:max-w-6xl xl:max-w-7xl
            mx-auto
          ">
            {main}
          </div>
        </div>
      </div>

      {/* Details Panel (Desktop Only) */}
      <div className="hidden xl:flex xl:w-96 xl:flex-col xl:border-l">
        {details}
      </div>
    </div>
  );
};
```

### 2. Component Responsive Behavior

#### Data Table Responsive Design
```tsx
// Responsive Data Table
const ResponsiveDataTable = ({ data, columns }) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (isMobile) {
    // Mobile Card Layout
    return (
      <div className="space-y-4">
        {data.map((row, index) => (
          <Card key={index} className="p-4">
            <div className="space-y-3">
              {columns.map((column, colIndex) => (
                <div key={colIndex} className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">
                    {column.header}
                  </span>
                  <span className="text-sm">
                    {row[column.accessor]}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    );
  }

  // Desktop Table Layout
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b">
            {columns.map((column, index) => (
              <th
                key={index}
                className="text-left p-3 font-medium text-gray-900"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b hover:bg-gray-50">
              {columns.map((column, colIndex) => (
                <td key={colIndex} className="p-3">
                  {row[column.accessor]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

#### Quality Score Display Responsive
```tsx
// Responsive Quality Score Component
const ResponsiveQualityScore = ({ score, quality, showDetails = true }) => {
  return (
    <>
      {/* Mobile Layout */}
      <div className="block sm:hidden">
        <Card className="p-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary mb-2">
              {score}%
            </div>
            <div className="text-sm text-muted-foreground mb-3">
              Overall Quality: {quality}
            </div>
            <Progress value={score} className="h-2" />
          </div>
        </Card>
      </div>

      {/* Tablet Layout */}
      <div className="hidden sm:block lg:hidden">
        <Card className="p-6">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-primary mb-1">
                {score}%
              </div>
              <div className="text-sm text-muted-foreground">
                {quality}
              </div>
            </div>
            <div className="flex-1">
              <Progress value={score} className="h-3 mb-2" />
              {showDetails && (
                <div className="text-sm text-muted-foreground">
                  Quality assessment based on 4 dimensions
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Desktop Layout */}
      <div className="hidden lg:block">
        <Card className="p-8">
          <div className="flex items-center gap-8">
            <QualityScoreCircle score={score} quality={quality} size={120} />
            <div className="flex-1">
              <h3 className="text-xl font-semibold mb-2">
                Data Quality Score
              </h3>
              <p className="text-muted-foreground mb-4">
                Your data quality is rated as <strong>{quality}</strong> based on
                comprehensive analysis across four key dimensions.
              </p>
              {showDetails && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-sm">
                    <span className="text-muted-foreground">Last Updated:</span>
                    <div className="font-medium">2 minutes ago</div>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">Records Analyzed:</span>
                    <div className="font-medium">1,247</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>
    </>
  );
};
```

---

## 📊 Chart Responsive Patterns

### 1. Chart Container Adaptations

#### Responsive Chart Heights
```tsx
// Dynamic Chart Heights
const useResponsiveChartHeight = () => {
  const [height, setHeight] = useState(400);

  useEffect(() => {
    const updateHeight = () => {
      const width = window.innerWidth;
      if (width < 640) setHeight(250);      // Mobile
      else if (width < 1024) setHeight(300); // Tablet
      else setHeight(400);                    // Desktop
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  return height;
};

// Responsive Chart Component
const ResponsiveChart = ({ data, type = 'line' }) => {
  const height = useResponsiveChartHeight();
  const [showLegend, setShowLegend] = useState(true);

  useEffect(() => {
    const updateLegend = () => {
      setShowLegend(window.innerWidth >= 768);
    };

    updateLegend();
    window.addEventListener('resize', updateLegend);
    return () => window.removeEventListener('resize', updateLegend);
  }, []);

  return (
    <Card className="p-4 sm:p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Quality Trends</h3>
        <p className="text-sm text-muted-foreground">
          Last 30 days
        </p>
      </div>

      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 20
          }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              fontSize={12}
              hide={window.innerWidth < 480} // Hide on very small screens
            />
            <YAxis fontSize={12} />
            <Tooltip />
            {showLegend && <Legend />}
            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
```

#### Chart Legend Adaptations
```tsx
// Responsive Chart Legend
const ResponsiveChartLegend = ({ items, orientation = 'auto' }) => {
  const [isHorizontal, setIsHorizontal] = useState(true);

  useEffect(() => {
    const updateOrientation = () => {
      if (orientation === 'auto') {
        setIsHorizontal(window.innerWidth >= 768);
      }
    };

    updateOrientation();
    window.addEventListener('resize', updateOrientation);
    return () => window.removeEventListener('resize', updateOrientation);
  }, [orientation]);

  return (
    <div className={`
      flex gap-4
      ${isHorizontal ? 'flex-row flex-wrap justify-center' : 'flex-col'}
    `}>
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: item.color }}
          />
          <span className="text-sm">{item.name}</span>
        </div>
      ))}
    </div>
  );
};
```

### 2. Mobile Chart Optimizations

#### Touch-Friendly Chart Interactions
```tsx
// Mobile-Optimized Chart
const MobileOptimizedChart = ({ data }) => {
  const [selectedDataPoint, setSelectedDataPoint] = useState(null);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="
          bg-white p-3 border border-gray-200 rounded-lg shadow-lg
          text-sm max-w-xs
        ">
          <h4 className="font-medium mb-2">{label}</h4>
          {payload.map((entry, index) => (
            <div key={index} className="flex justify-between gap-4">
              <span>{entry.name}:</span>
              <span className="font-medium">{entry.value}%</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const CustomDot = ({ cx, cy, payload, dataKey }) => {
    return (
      <circle
        cx={cx}
        cy={cy}
        r={6} // Larger touch targets for mobile
        fill="#3b82f6"
        stroke="#ffffff"
        strokeWidth={2}
        style={{ cursor: 'pointer' }}
        onClick={() => setSelectedDataPoint(payload)}
      />
    );
  };

  return (
    <div className="w-full">
      {/* Mobile Chart */}
      <div className="block sm:hidden h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 20, right: 10, left: 10, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              fontSize={10}
              interval="preserveStartEnd"
            />
            <YAxis hide />
            <Tooltip
              content={<CustomTooltip />}
              position={{ x: 10, y: 10 }}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={<CustomDot />}
              activeDot={{ r: 8 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Tablet/Desktop Chart */}
      <div className="hidden sm:block h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Selected Data Point Details (Mobile) */}
      {selectedDataPoint && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg sm:hidden">
          <h4 className="font-medium mb-2">
            {selectedDataPoint.date}
          </h4>
          <div className="text-sm">
            Quality Score: <span className="font-medium">{selectedDataPoint.score}%</span>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 🎯 Navigation Responsive Patterns

### 1. Mobile Navigation

#### Collapsible Sidebar
```tsx
// Mobile-First Sidebar Navigation
const ResponsiveNavigation = ({ items, currentPath }) => {
  const [isOpen, setIsOpen] = useState(false);

  const NavItem = ({ item, isMobile = false }) => (
    <a
      href={item.path}
      className={`
        flex items-center gap-3 px-3 py-2 rounded-lg transition-colors
        ${currentPath === item.path
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:text-foreground hover:bg-muted'
        }
        ${isMobile ? 'text-lg' : 'text-sm'}
      `}
      onClick={() => isMobile && setIsOpen(false)}
    >
      <item.icon className={`${isMobile ? 'w-6 h-6' : 'w-4 h-4'}`} />
      <span>{item.label}</span>
    </a>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsOpen(true)}
        >
          <Menu className="w-4 h-4" />
        </Button>
      </div>

      {/* Mobile Overlay */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setIsOpen(false)}
          />
        </div>
      )}

      {/* Mobile Sidebar */}
      <div className={`
        lg:hidden fixed left-0 top-0 h-full w-80 bg-background z-50
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-xl font-semibold">Data Quality</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <nav className="space-y-2">
            {items.map((item) => (
              <NavItem key={item.path} item={item} isMobile />
            ))}
          </nav>
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-6">Data Quality</h2>
          <nav className="space-y-1">
            {items.map((item) => (
              <NavItem key={item.path} item={item} />
            ))}
          </nav>
        </div>
      </div>
    </>
  );
};
```

#### Bottom Tab Navigation (Mobile)
```tsx
// Mobile Bottom Navigation
const MobileBottomNav = ({ items, currentPath }) => {
  return (
    <div className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t z-40">
      <div className="flex">
        {items.slice(0, 4).map((item) => (
          <a
            key={item.path}
            href={item.path}
            className={`
              flex-1 flex flex-col items-center py-3 px-2 text-xs
              ${currentPath === item.path
                ? 'text-primary'
                : 'text-muted-foreground'
              }
            `}
          >
            <item.icon className="w-5 h-5 mb-1" />
            <span className="truncate">{item.shortLabel || item.label}</span>
          </a>
        ))}
      </div>
    </div>
  );
};
```

### 2. Breadcrumb Responsive Design

#### Collapsible Breadcrumbs
```tsx
// Responsive Breadcrumb Navigation
const ResponsiveBreadcrumbs = ({ items }) => {
  const [showAll, setShowAll] = useState(false);

  // Show only first, last, and current on mobile
  const getMobileItems = () => {
    if (items.length <= 3) return items;
    return [
      items[0],
      { label: '...', isEllipsis: true },
      items[items.length - 1]
    ];
  };

  const displayItems = showAll ? items : getMobileItems();

  return (
    <nav className="flex items-center space-x-2 text-sm">
      {/* Mobile Breadcrumbs */}
      <div className="flex items-center space-x-2 sm:hidden">
        {displayItems.map((item, index) => (
          <React.Fragment key={index}>
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            )}
            {item.isEllipsis ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAll(true)}
                className="p-1"
              >
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            ) : (
              <span className={
                index === displayItems.length - 1
                  ? 'font-medium text-foreground'
                  : 'text-muted-foreground hover:text-foreground cursor-pointer'
              }>
                {item.label}
              </span>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Desktop Breadcrumbs */}
      <div className="hidden sm:flex items-center space-x-2">
        {items.map((item, index) => (
          <React.Fragment key={index}>
            {index > 0 && (
              <ChevronRight className="w-4 h-4 text-muted-foreground" />
            )}
            <span className={
              index === items.length - 1
                ? 'font-medium text-foreground'
                : 'text-muted-foreground hover:text-foreground cursor-pointer'
            }>
              {item.label}
            </span>
          </React.Fragment>
        ))}
      </div>
    </nav>
  );
};
```

---

## 🎨 Typography Responsive Scaling

### Responsive Text Scales
```css
/* Responsive Typography Classes */
.text-responsive-xs {
  font-size: 0.75rem;    /* 12px */
  line-height: 1rem;     /* 16px */
}

.text-responsive-sm {
  font-size: 0.875rem;   /* 14px */
  line-height: 1.25rem;  /* 20px */
}

.text-responsive-base {
  font-size: 1rem;       /* 16px */
  line-height: 1.5rem;   /* 24px */
}

.text-responsive-lg {
  font-size: 1.125rem;   /* 18px */
  line-height: 1.75rem;  /* 28px */
}

.text-responsive-xl {
  font-size: 1.25rem;    /* 20px */
  line-height: 1.75rem;  /* 28px */
}

.text-responsive-2xl {
  font-size: 1.5rem;     /* 24px */
  line-height: 2rem;     /* 32px */
}

.text-responsive-3xl {
  font-size: 1.875rem;   /* 30px */
  line-height: 2.25rem;  /* 36px */
}

/* Mobile adjustments */
@media (max-width: 640px) {
  .text-responsive-2xl {
    font-size: 1.25rem;   /* 20px */
    line-height: 1.75rem; /* 28px */
  }

  .text-responsive-3xl {
    font-size: 1.5rem;    /* 24px */
    line-height: 2rem;    /* 32px */
  }
}

/* Responsive heading classes */
.heading-responsive-1 {
  font-size: 2.5rem;     /* 40px */
  line-height: 1.2;
  font-weight: 800;
}

.heading-responsive-2 {
  font-size: 2rem;       /* 32px */
  line-height: 1.25;
  font-weight: 700;
}

.heading-responsive-3 {
  font-size: 1.5rem;     /* 24px */
  line-height: 1.33;
  font-weight: 600;
}

@media (max-width: 640px) {
  .heading-responsive-1 {
    font-size: 2rem;      /* 32px */
  }

  .heading-responsive-2 {
    font-size: 1.5rem;    /* 24px */
  }

  .heading-responsive-3 {
    font-size: 1.25rem;   /* 20px */
  }
}
```

### Dynamic Font Scaling Component
```tsx
// Responsive Text Component
const ResponsiveText = ({
  children,
  variant = 'body',
  responsive = true,
  className = ''
}) => {
  const getResponsiveClasses = () => {
    if (!responsive) return '';

    const variants = {
      'heading-1': 'text-2xl sm:text-3xl lg:text-4xl',
      'heading-2': 'text-xl sm:text-2xl lg:text-3xl',
      'heading-3': 'text-lg sm:text-xl lg:text-2xl',
      'body': 'text-sm sm:text-base',
      'small': 'text-xs sm:text-sm',
      'caption': 'text-xs'
    };

    return variants[variant] || variants.body;
  };

  return (
    <span className={`${getResponsiveClasses()} ${className}`}>
      {children}
    </span>
  );
};
```

---

## 🎛️ Form Responsive Patterns

### Adaptive Form Layouts
```tsx
// Responsive Form Component
const ResponsiveForm = ({ children, layout = 'auto' }) => {
  const [formLayout, setFormLayout] = useState('single');

  useEffect(() => {
    const updateLayout = () => {
      if (layout === 'auto') {
        const width = window.innerWidth;
        if (width < 768) setFormLayout('single');
        else if (width < 1024) setFormLayout('double');
        else setFormLayout('triple');
      } else {
        setFormLayout(layout);
      }
    };

    updateLayout();
    window.addEventListener('resize', updateLayout);
    return () => window.removeEventListener('resize', updateLayout);
  }, [layout]);

  const getGridClasses = () => {
    switch (formLayout) {
      case 'single': return 'grid-cols-1';
      case 'double': return 'grid-cols-1 md:grid-cols-2';
      case 'triple': return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
      default: return 'grid-cols-1';
    }
  };

  return (
    <form className={`grid gap-4 ${getGridClasses()}`}>
      {children}
    </form>
  );
};

// Responsive Form Field
const ResponsiveFormField = ({
  label,
  children,
  description,
  fullWidth = false,
  required = false
}) => {
  return (
    <div className={`space-y-2 ${fullWidth ? 'md:col-span-2 lg:col-span-3' : ''}`}>
      <label className="text-sm font-medium">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {children}
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
};
```

---

## 📏 Spacing Responsive System

### Adaptive Spacing Classes
```css
/* Responsive Spacing System */
.spacing-responsive-sm {
  padding: 1rem;
}

.spacing-responsive-md {
  padding: 1rem;
}

.spacing-responsive-lg {
  padding: 1rem;
}

@media (min-width: 640px) {
  .spacing-responsive-md {
    padding: 1.5rem;
  }

  .spacing-responsive-lg {
    padding: 1.5rem;
  }
}

@media (min-width: 768px) {
  .spacing-responsive-lg {
    padding: 2rem;
  }
}

@media (min-width: 1024px) {
  .spacing-responsive-lg {
    padding: 2.5rem;
  }
}

/* Container responsive padding */
.container-responsive {
  padding-left: 1rem;
  padding-right: 1rem;
}

@media (min-width: 640px) {
  .container-responsive {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }
}

@media (min-width: 1024px) {
  .container-responsive {
    padding-left: 2rem;
    padding-right: 2rem;
  }
}
```

### Dynamic Spacing Hook
```tsx
// Responsive Spacing Hook
const useResponsiveSpacing = () => {
  const [spacing, setSpacing] = useState({
    container: 'px-4',
    section: 'py-6',
    card: 'p-4'
  });

  useEffect(() => {
    const updateSpacing = () => {
      const width = window.innerWidth;

      if (width < 640) {
        setSpacing({
          container: 'px-4',
          section: 'py-4',
          card: 'p-4'
        });
      } else if (width < 1024) {
        setSpacing({
          container: 'px-6',
          section: 'py-6',
          card: 'p-6'
        });
      } else {
        setSpacing({
          container: 'px-8',
          section: 'py-8',
          card: 'p-8'
        });
      }
    };

    updateSpacing();
    window.addEventListener('resize', updateSpacing);
    return () => window.removeEventListener('resize', updateSpacing);
  }, []);

  return spacing;
};
```

This comprehensive responsive design guide ensures that the data management platform provides an optimal user experience across all devices, from mobile phones to large desktop displays, while maintaining functionality and visual appeal at every breakpoint.