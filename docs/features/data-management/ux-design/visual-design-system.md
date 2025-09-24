# Visual Design System - Data Management
## 数据管理功能视觉设计系统

### Overview
This document establishes the complete visual design system for the data quality management platform, ensuring consistency across all components while maintaining professional enterprise-grade aesthetics.

---

## 🎨 Color System

### Primary Quality Level Colors
```css
/* CSS Custom Properties for Quality Levels */
:root {
  /* Excellent - Green Palette */
  --quality-excellent: 134 239 172;    /* #86efac - green-300 */
  --quality-excellent-bg: 240 253 244; /* #f0fdf4 - green-50 */
  --quality-excellent-border: 187 247 208; /* #bbf7d0 - green-200 */
  --quality-excellent-text: 21 128 61;  /* #15803d - green-700 */

  /* Good - Blue Palette */
  --quality-good: 96 165 250;         /* #60a5fa - blue-400 */
  --quality-good-bg: 239 246 255;     /* #eff6ff - blue-50 */
  --quality-good-border: 147 197 253; /* #93c5fd - blue-300 */
  --quality-good-text: 29 78 216;     /* #1d4ed8 - blue-700 */

  /* Fair - Amber Palette */
  --quality-fair: 251 191 36;         /* #fbbf24 - amber-400 */
  --quality-fair-bg: 255 251 235;     /* #fffbeb - amber-50 */
  --quality-fair-border: 252 211 77;  /* #fcd34d - amber-300 */
  --quality-fair-text: 180 83 9;      /* #b45309 - amber-700 */

  /* Poor - Red Palette */
  --quality-poor: 248 113 113;        /* #f87171 - red-400 */
  --quality-poor-bg: 254 242 242;     /* #fef2f2 - red-50 */
  --quality-poor-border: 252 165 165; /* #fca5a5 - red-300 */
  --quality-poor-text: 185 28 28;     /* #b91c1c - red-700 */

  /* Processing/Loading States */
  --quality-processing: 168 162 158;  /* #a8a29e - stone-400 */
  --quality-processing-bg: 250 250 249; /* #fafaf9 - stone-50 */
  --quality-processing-text: 87 83 78; /* #57534e - stone-600 */
}
```

### Data Type Colors
```css
/* Data Type Identification Colors */
:root {
  /* Numeric Data */
  --data-numeric: 59 130 246;         /* #3b82f6 - blue-500 */
  --data-numeric-bg: 239 246 255;     /* #eff6ff - blue-50 */

  /* Text/String Data */
  --data-text: 139 69 19;             /* #8b4513 - amber-800 */
  --data-text-bg: 255 251 235;        /* #fffbeb - amber-50 */

  /* Date/Time Data */
  --data-datetime: 147 51 234;        /* #9333ea - purple-600 */
  --data-datetime-bg: 250 245 255;    /* #faf5ff - purple-50 */

  /* Boolean Data */
  --data-boolean: 34 197 94;          /* #22c55e - green-500 */
  --data-boolean-bg: 240 253 244;     /* #f0fdf4 - green-50 */

  /* Null/Missing Data */
  --data-null: 156 163 175;           /* #9ca3af - gray-400 */
  --data-null-bg: 249 250 251;        /* #f9fafb - gray-50 */
}
```

### Status and Interaction Colors
```css
/* Status Colors */
:root {
  /* Success States */
  --status-success: 34 197 94;        /* #22c55e - green-500 */
  --status-success-bg: 240 253 244;   /* #f0fdf4 - green-50 */

  /* Warning States */
  --status-warning: 245 158 11;       /* #f59e0b - amber-500 */
  --status-warning-bg: 255 251 235;   /* #fffbeb - amber-50 */

  /* Error States */
  --status-error: 239 68 68;          /* #ef4444 - red-500 */
  --status-error-bg: 254 242 242;     /* #fef2f2 - red-50 */

  /* Info States */
  --status-info: 59 130 246;          /* #3b82f6 - blue-500 */
  --status-info-bg: 239 246 255;      /* #eff6ff - blue-50 */

  /* Processing States */
  --status-processing: 168 162 158;   /* #a8a29e - stone-400 */
  --status-processing-bg: 250 250 249; /* #fafaf9 - stone-50 */
}
```

### Gradient Definitions
```css
/* AI and Premium Feature Gradients */
.gradient-ai-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
}

.gradient-ai-secondary {
  background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
}

.gradient-quality-excellent {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.gradient-quality-poor {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
}

/* Chart and Data Visualization Gradients */
.gradient-chart-primary {
  background: linear-gradient(180deg, #3b82f680 0%, #3b82f620 100%);
}

.gradient-chart-secondary {
  background: linear-gradient(180deg, #8b5cf680 0%, #8b5cf620 100%);
}
```

---

## 🎯 Icon System

### Quality Dimension Icons
```tsx
// Icon mappings with consistent sizing and styling
export const QualityIcons = {
  // Four Dimensions
  completeness: {
    icon: Database,
    color: "text-blue-600",
    bgColor: "bg-blue-100",
    description: "Data completeness and coverage"
  },
  accuracy: {
    icon: Target,
    color: "text-green-600",
    bgColor: "bg-green-100",
    description: "Data accuracy and correctness"
  },
  consistency: {
    icon: Layers,
    color: "text-purple-600",
    bgColor: "bg-purple-100",
    description: "Data consistency across sources"
  },
  validity: {
    icon: Shield,
    color: "text-amber-600",
    bgColor: "bg-amber-100",
    description: "Data format and business rule validity"
  },

  // Status Icons
  excellent: {
    icon: CheckCircle,
    color: "text-green-600",
    bgColor: "bg-green-100"
  },
  good: {
    icon: CheckCircle2,
    color: "text-blue-600",
    bgColor: "bg-blue-100"
  },
  fair: {
    icon: AlertCircle,
    color: "text-amber-600",
    bgColor: "bg-amber-100"
  },
  poor: {
    icon: XCircle,
    color: "text-red-600",
    bgColor: "bg-red-100"
  },

  // Action Icons
  analyze: {
    icon: BarChart3,
    color: "text-blue-600",
    bgColor: "bg-blue-100"
  },
  fix: {
    icon: Wand2,
    color: "text-purple-600",
    bgColor: "bg-purple-100"
  },
  export: {
    icon: Download,
    color: "text-gray-600",
    bgColor: "bg-gray-100"
  },
  refresh: {
    icon: RefreshCw,
    color: "text-gray-600",
    bgColor: "bg-gray-100"
  }
}
```

### Data Type Icons
```tsx
export const DataTypeIcons = {
  string: {
    icon: Type,
    color: "text-amber-600",
    bgColor: "bg-amber-100"
  },
  number: {
    icon: Hash,
    color: "text-blue-600",
    bgColor: "bg-blue-100"
  },
  date: {
    icon: Calendar,
    color: "text-purple-600",
    bgColor: "bg-purple-100"
  },
  boolean: {
    icon: ToggleLeft,
    color: "text-green-600",
    bgColor: "bg-green-100"
  },
  null: {
    icon: Minus,
    color: "text-gray-500",
    bgColor: "bg-gray-100"
  },
  email: {
    icon: Mail,
    color: "text-indigo-600",
    bgColor: "bg-indigo-100"
  },
  phone: {
    icon: Phone,
    color: "text-cyan-600",
    bgColor: "bg-cyan-100"
  },
  url: {
    icon: Link,
    color: "text-teal-600",
    bgColor: "bg-teal-100"
  }
}
```

### AI and Smart Feature Icons
```tsx
export const AIIcons = {
  assistant: {
    icon: Bot,
    color: "text-blue-600",
    bgColor: "bg-gradient-to-br from-blue-500 to-purple-600"
  },
  insight: {
    icon: Lightbulb,
    color: "text-yellow-600",
    bgColor: "bg-yellow-100"
  },
  recommendation: {
    icon: Sparkles,
    color: "text-purple-600",
    bgColor: "bg-purple-100"
  },
  autofix: {
    icon: Zap,
    color: "text-orange-600",
    bgColor: "bg-orange-100"
  },
  learning: {
    icon: Brain,
    color: "text-pink-600",
    bgColor: "bg-pink-100"
  }
}
```

---

## 📝 Typography System

### Heading Hierarchy
```css
/* Heading Styles */
.heading-hero {
  font-size: 3rem;           /* 48px */
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: -0.025em;
}

.heading-display {
  font-size: 2.5rem;         /* 40px */
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.heading-xl {
  font-size: 2rem;           /* 32px */
  line-height: 1.25;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.heading-lg {
  font-size: 1.5rem;         /* 24px */
  line-height: 1.33;
  font-weight: 600;
}

.heading-md {
  font-size: 1.25rem;        /* 20px */
  line-height: 1.4;
  font-weight: 600;
}

.heading-sm {
  font-size: 1.125rem;       /* 18px */
  line-height: 1.44;
  font-weight: 600;
}

.heading-xs {
  font-size: 1rem;           /* 16px */
  line-height: 1.5;
  font-weight: 600;
}
```

### Body Text Styles
```css
/* Body Text */
.text-body-lg {
  font-size: 1.125rem;       /* 18px */
  line-height: 1.6;
  font-weight: 400;
}

.text-body {
  font-size: 1rem;           /* 16px */
  line-height: 1.6;
  font-weight: 400;
}

.text-body-sm {
  font-size: 0.875rem;       /* 14px */
  line-height: 1.57;
  font-weight: 400;
}

.text-caption {
  font-size: 0.75rem;        /* 12px */
  line-height: 1.5;
  font-weight: 400;
  color: rgb(var(--muted-foreground));
}

.text-overline {
  font-size: 0.75rem;        /* 12px */
  line-height: 1.5;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgb(var(--muted-foreground));
}
```

### Data Display Typography
```css
/* Specialized Data Typography */
.text-metric-hero {
  font-size: 3.5rem;         /* 56px */
  line-height: 1;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.text-metric-lg {
  font-size: 2.5rem;         /* 40px */
  line-height: 1;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.text-metric-md {
  font-size: 1.5rem;         /* 24px */
  line-height: 1;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.text-metric-sm {
  font-size: 1rem;           /* 16px */
  line-height: 1;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.text-code {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
  font-size: 0.875rem;       /* 14px */
  line-height: 1.43;
  font-weight: 400;
}
```

---

## 📐 Layout and Spacing

### Grid System
```css
/* Container Sizes */
.container-sm { max-width: 640px; }   /* Small devices */
.container-md { max-width: 768px; }   /* Medium devices */
.container-lg { max-width: 1024px; }  /* Large devices */
.container-xl { max-width: 1280px; }  /* Extra large devices */
.container-2xl { max-width: 1536px; } /* 2X large devices */

/* Dashboard Grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.dashboard-grid-dense {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

/* Card Grid */
.card-grid-sm {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.card-grid-md {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.card-grid-lg {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}
```

### Spacing Scale
```css
/* Consistent Spacing System */
:root {
  --space-0: 0;
  --space-1: 0.25rem;        /* 4px */
  --space-2: 0.5rem;         /* 8px */
  --space-3: 0.75rem;        /* 12px */
  --space-4: 1rem;           /* 16px */
  --space-5: 1.25rem;        /* 20px */
  --space-6: 1.5rem;         /* 24px */
  --space-8: 2rem;           /* 32px */
  --space-10: 2.5rem;        /* 40px */
  --space-12: 3rem;          /* 48px */
  --space-16: 4rem;          /* 64px */
  --space-20: 5rem;          /* 80px */
  --space-24: 6rem;          /* 96px */
}

/* Component Spacing */
.component-padding-sm { padding: var(--space-4); }
.component-padding-md { padding: var(--space-6); }
.component-padding-lg { padding: var(--space-8); }

.component-margin-sm { margin: var(--space-4); }
.component-margin-md { margin: var(--space-6); }
.component-margin-lg { margin: var(--space-8); }
```

### Border Radius System
```css
/* Border Radius Scale */
:root {
  --radius-sm: 0.25rem;      /* 4px */
  --radius-md: 0.375rem;     /* 6px */
  --radius-lg: 0.5rem;       /* 8px */
  --radius-xl: 0.75rem;      /* 12px */
  --radius-2xl: 1rem;        /* 16px */
  --radius-full: 9999px;     /* Full round */
}

/* Component Specific Radius */
.card-radius { border-radius: var(--radius-lg); }
.button-radius { border-radius: var(--radius-md); }
.input-radius { border-radius: var(--radius-md); }
.badge-radius { border-radius: var(--radius-full); }
```

---

## 🎭 Component Visual Patterns

### Card Elevation System
```css
/* Shadow Definitions */
.shadow-sm {
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.shadow-md {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

.shadow-xl {
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}

/* Hover Elevations */
.hover-lift {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 20px -5px rgb(0 0 0 / 0.15);
}
```

### Button Variants
```css
/* Primary Button */
.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: 1px solid transparent;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.btn-primary:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

/* AI Action Button */
.btn-ai {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  position: relative;
  overflow: hidden;
}

.btn-ai::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.btn-ai:hover::before {
  left: 100%;
}

/* Quality Level Buttons */
.btn-excellent {
  background-color: rgb(var(--quality-excellent-bg));
  color: rgb(var(--quality-excellent-text));
  border: 1px solid rgb(var(--quality-excellent-border));
}

.btn-good {
  background-color: rgb(var(--quality-good-bg));
  color: rgb(var(--quality-good-text));
  border: 1px solid rgb(var(--quality-good-border));
}

.btn-fair {
  background-color: rgb(var(--quality-fair-bg));
  color: rgb(var(--quality-fair-text));
  border: 1px solid rgb(var(--quality-fair-border));
}

.btn-poor {
  background-color: rgb(var(--quality-poor-bg));
  color: rgb(var(--quality-poor-text));
  border: 1px solid rgb(var(--quality-poor-border));
}
```

### Progress Indicators
```css
/* Animated Progress Bars */
.progress-bar {
  background: linear-gradient(90deg, #e5e7eb 0%, #e5e7eb 100%);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar-fill {
  border-radius: var(--radius-full);
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-excellent {
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
}

.progress-good {
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
}

.progress-fair {
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
}

.progress-poor {
  background: linear-gradient(90deg, #ef4444 0%, #f87171 100%);
}

/* Animated Gradient Progress */
.progress-animated {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
  background-size: 200% 100%;
  animation: gradient-shift 2s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

---

## 🌓 Dark Mode Support

### Dark Mode Color Overrides
```css
/* Dark Mode Quality Colors */
@media (prefers-color-scheme: dark) {
  :root {
    /* Excellent - Darker Green */
    --quality-excellent: 34 197 94;      /* #22c55e - green-500 */
    --quality-excellent-bg: 20 83 45;    /* #14532d - green-900 */
    --quality-excellent-border: 22 101 52; /* #166534 - green-800 */
    --quality-excellent-text: 134 239 172; /* #86efac - green-300 */

    /* Good - Darker Blue */
    --quality-good: 59 130 246;          /* #3b82f6 - blue-500 */
    --quality-good-bg: 30 58 138;        /* #1e3a8a - blue-900 */
    --quality-good-border: 30 64 175;    /* #1e40af - blue-800 */
    --quality-good-text: 147 197 253;    /* #93c5fd - blue-300 */

    /* Fair - Darker Amber */
    --quality-fair: 245 158 11;          /* #f59e0b - amber-500 */
    --quality-fair-bg: 146 64 14;        /* #92400e - amber-900 */
    --quality-fair-border: 180 83 9;     /* #b45309 - amber-800 */
    --quality-fair-text: 252 211 77;     /* #fcd34d - amber-300 */

    /* Poor - Darker Red */
    --quality-poor: 239 68 68;           /* #ef4444 - red-500 */
    --quality-poor-bg: 153 27 27;        /* #991b1b - red-900 */
    --quality-poor-border: 185 28 28;    /* #b91c1c - red-800 */
    --quality-poor-text: 252 165 165;    /* #fca5a5 - red-300 */
  }
}

/* Dark Mode Class-based Implementation */
.dark {
  /* Override quality colors for class-based dark mode */
  --quality-excellent: 34 197 94;
  --quality-excellent-bg: 20 83 45;
  --quality-good: 59 130 246;
  --quality-good-bg: 30 58 138;
  --quality-fair: 245 158 11;
  --quality-fair-bg: 146 64 14;
  --quality-poor: 239 68 68;
  --quality-poor-bg: 153 27 27;
}
```

### Dark Mode Specific Components
```css
/* Dark Mode Card Shadows */
.dark .shadow-md {
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.3), 0 2px 4px -2px rgb(0 0 0 / 0.2);
}

.dark .shadow-lg {
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.3), 0 4px 6px -4px rgb(0 0 0 / 0.2);
}

/* Dark Mode Borders */
.dark .border {
  border-color: rgb(var(--border));
}

.dark .border-quality-excellent {
  border-color: rgb(var(--quality-excellent-border));
}

/* Dark Mode Text Contrast */
.dark .text-quality-excellent {
  color: rgb(var(--quality-excellent-text));
}

.dark .bg-quality-excellent {
  background-color: rgb(var(--quality-excellent-bg));
}
```

---

## 📊 Data Visualization Colors

### Chart Color Palettes
```css
/* Primary Chart Colors */
:root {
  --chart-primary: #3b82f6;     /* Blue */
  --chart-secondary: #8b5cf6;   /* Purple */
  --chart-tertiary: #10b981;    /* Emerald */
  --chart-quaternary: #f59e0b;  /* Amber */
  --chart-quinary: #ef4444;     /* Red */
  --chart-senary: #06b6d4;      /* Cyan */
  --chart-septenary: #84cc16;   /* Lime */
  --chart-octonary: #f97316;    /* Orange */
}

/* Sequential Color Scale (Light to Dark) */
.chart-sequential {
  --seq-1: #eff6ff;  /* blue-50 */
  --seq-2: #dbeafe;  /* blue-100 */
  --seq-3: #bfdbfe;  /* blue-200 */
  --seq-4: #93c5fd;  /* blue-300 */
  --seq-5: #60a5fa;  /* blue-400 */
  --seq-6: #3b82f6;  /* blue-500 */
  --seq-7: #2563eb;  /* blue-600 */
  --seq-8: #1d4ed8;  /* blue-700 */
  --seq-9: #1e40af;  /* blue-800 */
}

/* Diverging Color Scale (Poor to Excellent) */
.chart-diverging {
  --div-1: #dc2626;  /* red-600 - Poor */
  --div-2: #ea580c;  /* orange-600 */
  --div-3: #f59e0b;  /* amber-500 - Fair */
  --div-4: #84cc16;  /* lime-500 */
  --div-5: #22c55e;  /* green-500 - Good */
  --div-6: #10b981;  /* emerald-500 - Excellent */
}
```

### Heat Map Colors
```css
/* Heat Map Intensity Scale */
.heatmap-scale {
  --heat-0: #f8fafc;   /* slate-50 - No data */
  --heat-1: #e2e8f0;   /* slate-200 - Very low */
  --heat-2: #cbd5e1;   /* slate-300 - Low */
  --heat-3: #94a3b8;   /* slate-400 - Medium-low */
  --heat-4: #64748b;   /* slate-500 - Medium */
  --heat-5: #475569;   /* slate-600 - Medium-high */
  --heat-6: #334155;   /* slate-700 - High */
  --heat-7: #1e293b;   /* slate-800 - Very high */
  --heat-8: #0f172a;   /* slate-900 - Extreme */
}

/* Quality Heat Map */
.quality-heatmap {
  --qual-heat-excellent: #dcfce7;  /* green-100 */
  --qual-heat-good: #dbeafe;       /* blue-100 */
  --qual-heat-fair: #fef3c7;       /* amber-100 */
  --qual-heat-poor: #fee2e2;       /* red-100 */
  --qual-heat-missing: #f1f5f9;    /* slate-100 */
}
```

---

## 🎨 CSS Utility Classes

### Quality Level Utilities
```css
/* Background Colors */
.bg-quality-excellent { background-color: rgb(var(--quality-excellent-bg)); }
.bg-quality-good { background-color: rgb(var(--quality-good-bg)); }
.bg-quality-fair { background-color: rgb(var(--quality-fair-bg)); }
.bg-quality-poor { background-color: rgb(var(--quality-poor-bg)); }

/* Text Colors */
.text-quality-excellent { color: rgb(var(--quality-excellent-text)); }
.text-quality-good { color: rgb(var(--quality-good-text)); }
.text-quality-fair { color: rgb(var(--quality-fair-text)); }
.text-quality-poor { color: rgb(var(--quality-poor-text)); }

/* Border Colors */
.border-quality-excellent { border-color: rgb(var(--quality-excellent-border)); }
.border-quality-good { border-color: rgb(var(--quality-good-border)); }
.border-quality-fair { border-color: rgb(var(--quality-fair-border)); }
.border-quality-poor { border-color: rgb(var(--quality-poor-border)); }
```

### Animation Utilities
```css
/* Fade In Animation */
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Slide In Animation */
.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateX(-20px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Pulse Animation for Loading */
.animate-pulse-soft {
  animation: pulseSoft 2s ease-in-out infinite;
}

@keyframes pulseSoft {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

/* Scale Animation for Interactions */
.animate-scale {
  transition: transform 0.2s ease;
}

.animate-scale:hover {
  transform: scale(1.05);
}
```

This comprehensive visual design system provides a solid foundation for creating consistent, professional, and accessible data management interfaces. All colors, typography, and components are designed to work seamlessly with our existing Radix UI + Tailwind CSS architecture while maintaining enterprise-grade aesthetics.