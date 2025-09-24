# Interaction Design - Data Management
## 数据管理功能交互体验设计

### Overview
This document defines the complete interaction design patterns for the data quality management system, focusing on intuitive user flows, meaningful micro-interactions, and intelligent assistance mechanisms.

---

## 🚀 Core User Journey Design

### 1. First-Time User Onboarding Flow

#### Welcome & Introduction
```tsx
// Progressive Onboarding Component
const OnboardingFlow = () => {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: "Welcome to Data Quality Control",
      description: "Transform your raw data into trustworthy insights with AI-powered quality assessment",
      visual: <DataQualityHero />,
      duration: 3000
    },
    {
      title: "Four Quality Dimensions",
      description: "We analyze completeness, accuracy, consistency, and validity to give you a complete picture",
      visual: <QualityDimensionsDemo />,
      interaction: "hover-to-explore"
    },
    {
      title: "AI-Powered Insights",
      description: "Get intelligent recommendations and automated fixes for common data issues",
      visual: <AIAssistantDemo />,
      interaction: "interactive-chat"
    },
    {
      title: "Ready to Start?",
      description: "Upload your first dataset and see the magic happen",
      visual: <UploadZonePreview />,
      cta: "Upload My Data"
    }
  ];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={currentStep}
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -50 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
        className="max-w-2xl mx-auto text-center"
      >
        {/* Step content */}
      </motion.div>
    </AnimatePresence>
  );
};
```

#### Interactive Tutorial Overlay
```tsx
// Contextual Help System
const TutorialOverlay = () => {
  const [activeHint, setActiveHint] = useState(null);

  const hints = [
    {
      target: ".upload-zone",
      title: "Upload Your Data",
      description: "Drag and drop or click to upload CSV, Excel, or JSON files",
      position: "bottom",
      highlight: true
    },
    {
      target: ".quality-dimensions",
      title: "Quality Assessment",
      description: "View your data quality across four key dimensions",
      position: "top",
      delay: 2000
    },
    {
      target: ".ai-assistant",
      title: "AI Recommendations",
      description: "Get smart suggestions to improve your data quality",
      position: "left",
      delay: 4000
    }
  ];

  return (
    <Joyride
      steps={hints}
      run={true}
      continuous={true}
      showProgress={true}
      styles={{
        options: {
          primaryColor: '#3b82f6',
          borderRadius: 8,
          arrowColor: '#3b82f6'
        }
      }}
    />
  );
};
```

### 2. Upload to Analysis Flow

#### Smart Upload Experience
```tsx
// Enhanced Upload Interaction
const SmartUploadZone = () => {
  const [uploadState, setUploadState] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [fileInfo, setFileInfo] = useState(null);

  const handleDrop = useCallback(async (files) => {
    setUploadState('uploading');

    // Immediate file validation feedback
    const file = files[0];
    setFileInfo({
      name: file.name,
      size: file.size,
      type: file.type,
      preview: await generatePreview(file)
    });

    // Simulate progressive upload with real feedback
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 100));
      setProgress(i);
    }

    setUploadState('processing');

    // Start quality analysis
    setTimeout(() => {
      setUploadState('complete');
    }, 2000);
  }, []);

  return (
    <div className="relative">
      <div
        className={`
          border-2 border-dashed rounded-lg p-12 transition-all duration-300
          ${uploadState === 'uploading' ? 'border-blue-400 bg-blue-50' :
            uploadState === 'processing' ? 'border-purple-400 bg-purple-50' :
            uploadState === 'complete' ? 'border-green-400 bg-green-50' :
            'border-gray-300 hover:border-gray-400'}
        `}
        onDrop={handleDrop}
      >
        <AnimatePresence mode="wait">
          {uploadState === 'idle' && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center"
            >
              <CloudUpload className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Drop your data file here</h3>
              <p className="text-gray-600">CSV, Excel, or JSON files up to 50MB</p>
            </motion.div>
          )}

          {uploadState === 'uploading' && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center"
            >
              <div className="relative w-16 h-16 mx-auto mb-4">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Upload className="w-16 h-16 text-blue-500" />
                </motion.div>
              </div>
              <h3 className="text-lg font-semibold mb-2">Uploading {fileInfo?.name}</h3>
              <Progress value={progress} className="w-full max-w-xs mx-auto" />
              <p className="text-sm text-gray-600 mt-2">{progress}% complete</p>
            </motion.div>
          )}

          {uploadState === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <div className="relative w-16 h-16 mx-auto mb-4">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <Bot className="w-16 h-16 text-purple-500" />
                </motion.div>
              </div>
              <h3 className="text-lg font-semibold mb-2">AI is analyzing your data</h3>
              <p className="text-gray-600">This usually takes 10-30 seconds</p>

              <div className="mt-4 space-y-2">
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span>File structure analyzed</span>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 1 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                  <span>Running quality assessment...</span>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
```

#### Progressive Results Reveal
```tsx
// Staggered Animation for Results
const ResultsReveal = ({ qualityData }) => {
  const [visibleCards, setVisibleCards] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setVisibleCards(prev => {
        if (prev < 4) return prev + 1;
        clearInterval(timer);
        return prev;
      });
    }, 500);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {qualityData.dimensions.map((dimension, index) => (
        <motion.div
          key={dimension.id}
          initial={{ opacity: 0, y: 50, scale: 0.9 }}
          animate={{
            opacity: visibleCards > index ? 1 : 0,
            y: visibleCards > index ? 0 : 50,
            scale: visibleCards > index ? 1 : 0.9
          }}
          transition={{
            duration: 0.6,
            ease: "easeOut",
            delay: index * 0.1
          }}
          whileHover={{ scale: 1.05, y: -5 }}
          className="relative"
        >
          <QualityDimensionCard
            dimension={dimension}
            animateScore={visibleCards > index}
          />

          {/* Celebration effect for excellent scores */}
          {dimension.score >= 90 && visibleCards > index && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: [0, 1.2, 1] }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="absolute -top-2 -right-2"
            >
              <Sparkles className="w-6 h-6 text-yellow-500" />
            </motion.div>
          )}
        </motion.div>
      ))}
    </div>
  );
};
```

---

## 🎭 Micro-Interactions & Animations

### 1. Quality Score Animations

#### Animated Score Counter
```tsx
// Smooth Number Animation
const AnimatedScore = ({ value, duration = 2000, quality }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime;
    let animationFrame;

    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);

      // Easing function for natural feel
      const easeOutCubic = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.floor(value * easeOutCubic));

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  const getQualityColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  return (
    <motion.span
      className={`text-4xl font-bold ${getQualityColor(value)}`}
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {displayValue}%
    </motion.span>
  );
};
```

#### Progress Bar Animation
```tsx
// Fluid Progress Animation
const QualityProgressBar = ({ value, quality, animated = true }) => {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (animated) {
      // Delay start for stagger effect
      const timer = setTimeout(() => {
        setWidth(value);
      }, 200);
      return () => clearTimeout(timer);
    } else {
      setWidth(value);
    }
  }, [value, animated]);

  const getProgressColor = (quality) => {
    const colors = {
      excellent: 'bg-gradient-to-r from-green-500 to-emerald-500',
      good: 'bg-gradient-to-r from-blue-500 to-cyan-500',
      fair: 'bg-gradient-to-r from-amber-500 to-yellow-500',
      poor: 'bg-gradient-to-r from-red-500 to-pink-500'
    };
    return colors[quality] || colors.fair;
  };

  return (
    <div className="relative w-full h-3 bg-gray-200 rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${getProgressColor(quality)}`}
        initial={{ width: 0 }}
        animate={{ width: `${width}%` }}
        transition={{
          duration: 1.5,
          ease: "easeOut",
          type: "spring",
          stiffness: 100
        }}
      />

      {/* Shine effect */}
      <motion.div
        className="absolute top-0 left-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent"
        initial={{ x: '-100%' }}
        animate={{ x: '300%' }}
        transition={{
          duration: 2,
          delay: 1,
          ease: "easeInOut"
        }}
      />
    </div>
  );
};
```

### 2. Interactive Data Table

#### Hover Effects & Cell Highlighting
```tsx
// Enhanced Table Interactions
const InteractiveDataTable = ({ data, issues }) => {
  const [hoveredCell, setHoveredCell] = useState(null);
  const [selectedColumn, setSelectedColumn] = useState(null);

  const getCellColor = (rowIndex, colIndex, value) => {
    const cellKey = `${rowIndex}-${colIndex}`;
    const hasIssue = issues.find(issue => issue.cellKey === cellKey);

    if (hasIssue) {
      return 'bg-red-50 border-red-200';
    }
    if (hoveredCell?.row === rowIndex) {
      return 'bg-blue-50';
    }
    if (selectedColumn === colIndex) {
      return 'bg-purple-50';
    }
    return 'bg-white hover:bg-gray-50';
  };

  return (
    <div className="relative overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            {data.columns.map((column, colIndex) => (
              <th
                key={colIndex}
                className={`
                  p-3 text-left border border-gray-200 bg-gray-50 cursor-pointer
                  transition-colors duration-200
                  ${selectedColumn === colIndex ? 'bg-purple-100' : 'hover:bg-gray-100'}
                `}
                onClick={() => setSelectedColumn(
                  selectedColumn === colIndex ? null : colIndex
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium">{column.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {column.type}
                  </Badge>
                  {column.issueCount > 0 && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      whilePulse={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 0.5 }}
                    >
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    </motion.div>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.cells.map((cell, colIndex) => (
                <td
                  key={colIndex}
                  className={`
                    p-3 border border-gray-200 transition-all duration-200
                    ${getCellColor(rowIndex, colIndex, cell.value)}
                  `}
                  onMouseEnter={() => setHoveredCell({ row: rowIndex, col: colIndex })}
                  onMouseLeave={() => setHoveredCell(null)}
                >
                  <motion.div
                    whileHover={{ scale: 1.02 }}
                    className="relative"
                  >
                    {cell.value}

                    {/* Issue indicator */}
                    {cell.hasIssue && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"
                      />
                    )}
                  </motion.div>
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

### 3. AI Assistant Interactions

#### Typing Indicator & Response Animation
```tsx
// Realistic AI Chat Experience
const AITypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg max-w-fit"
    >
      <Bot className="w-4 h-4 text-blue-600" />
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 bg-gray-500 rounded-full"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.2
            }}
          />
        ))}
      </div>
      <span className="text-sm text-gray-600">AI is thinking...</span>
    </motion.div>
  );
};

// AI Response with Suggestion Pills
const AIResponse = ({ message, suggestions }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: isVisible ? 1 : 0, y: isVisible ? 0 : 20 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex gap-3 mb-4"
    >
      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>

      <div className="flex-1">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-gray-100 rounded-lg p-3 mb-3"
        >
          <TypewriterText text={message} speed={30} />
        </motion.div>

        {suggestions && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="flex flex-wrap gap-2"
          >
            {suggestions.map((suggestion, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8 + index * 0.1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 transition-colors"
              >
                {suggestion}
              </motion.button>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

// Typewriter Effect Component
const TypewriterText = ({ text, speed = 50 }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(prev => prev + text[currentIndex]);
        setCurrentIndex(prev => prev + 1);
      }, speed);
      return () => clearTimeout(timer);
    }
  }, [currentIndex, text, speed]);

  return (
    <span>
      {displayText}
      {currentIndex < text.length && (
        <motion.span
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.8, repeat: Infinity }}
          className="inline-block w-0.5 h-4 bg-blue-600 ml-1"
        />
      )}
    </span>
  );
};
```

---

## 🧠 Intelligent Assistance System

### 1. Context-Aware Help

#### Smart Tooltip System
```tsx
// Contextual Help Tooltips
const SmartTooltip = ({ children, helpContent, context, position = "top" }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);

  // Show help automatically for first-time users
  useEffect(() => {
    const isFirstTime = !localStorage.getItem(`help-seen-${context}`);
    if (isFirstTime) {
      const timer = setTimeout(() => {
        setIsVisible(true);
        setHasInteracted(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [context]);

  const handleClose = () => {
    setIsVisible(false);
    localStorage.setItem(`help-seen-${context}`, 'true');
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => !hasInteracted && setIsVisible(false)}
      >
        {children}
      </div>

      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: position === 'top' ? 10 : -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={`
              absolute z-50 max-w-sm p-4 bg-white border border-gray-200 rounded-lg shadow-lg
              ${position === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
            `}
          >
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                <HelpCircle className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-sm mb-1">{helpContent.title}</h4>
                <p className="text-xs text-gray-600 mb-3">{helpContent.description}</p>
                {helpContent.action && (
                  <Button size="sm" variant="outline" className="text-xs h-6">
                    {helpContent.action}
                  </Button>
                )}
              </div>
              {hasInteracted && (
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Arrow */}
            <div className={`
              absolute w-3 h-3 bg-white border-l border-t border-gray-200 transform rotate-45
              ${position === 'top' ? 'top-full -mt-1.5 left-1/2 -ml-1.5' : 'bottom-full -mb-1.5 left-1/2 -ml-1.5'}
            `} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
```

#### Progressive Feature Discovery
```tsx
// Feature Discovery System
const FeatureDiscovery = () => {
  const [discoveredFeatures, setDiscoveredFeatures] = useState(new Set());
  const [currentHint, setCurrentHint] = useState(null);

  const features = [
    {
      id: 'bulk-fix',
      trigger: 'multiple-issues-detected',
      title: '💡 Bulk Fix Available',
      description: 'You can fix multiple similar issues at once using our AI-powered bulk fix feature.',
      element: '.bulk-fix-button',
      delay: 3000
    },
    {
      id: 'export-report',
      trigger: 'analysis-complete',
      title: '📊 Export Quality Report',
      description: 'Generate a professional report to share with your team or stakeholders.',
      element: '.export-button',
      delay: 5000
    },
    {
      id: 'column-profiling',
      trigger: 'column-click',
      title: '🔍 Deep Column Analysis',
      description: 'Click any column to see detailed profiling and quality metrics.',
      element: '.data-table th',
      immediate: true
    }
  ];

  useEffect(() => {
    features.forEach(feature => {
      if (!discoveredFeatures.has(feature.id)) {
        // Check if trigger condition is met
        if (shouldShowFeature(feature)) {
          const timer = setTimeout(() => {
            setCurrentHint(feature);
          }, feature.delay || 0);
          return () => clearTimeout(timer);
        }
      }
    });
  }, [discoveredFeatures]);

  const handleFeatureDiscovered = (featureId) => {
    setDiscoveredFeatures(prev => new Set([...prev, featureId]));
    setCurrentHint(null);
  };

  return (
    <AnimatePresence>
      {currentHint && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-4 right-4 max-w-sm bg-white border border-blue-200 rounded-lg shadow-lg p-4 z-50"
        >
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-blue-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-sm mb-1">{currentHint.title}</h4>
              <p className="text-xs text-gray-600 mb-3">{currentHint.description}</p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => handleFeatureDiscovered(currentHint.id)}
                  className="text-xs h-6"
                >
                  Try it
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => handleFeatureDiscovered(currentHint.id)}
                  className="text-xs h-6"
                >
                  Maybe later
                </Button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
```

### 2. Smart Recommendations

#### Contextual Action Suggestions
```tsx
// Intelligent Action Recommendations
const ActionRecommendations = ({ dataQuality, userBehavior }) => {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    const generateRecommendations = () => {
      const recs = [];

      // Based on data quality issues
      if (dataQuality.completeness < 80) {
        recs.push({
          id: 'improve-completeness',
          type: 'quality-improvement',
          priority: 'high',
          title: 'Improve Data Completeness',
          description: `${Math.round(100 - dataQuality.completeness)}% of your records have missing values`,
          action: 'Show Missing Value Analysis',
          icon: Database,
          color: 'amber'
        });
      }

      // Based on user behavior
      if (userBehavior.viewedColumns.length > 5 && !userBehavior.usedBulkActions) {
        recs.push({
          id: 'bulk-actions',
          type: 'efficiency',
          priority: 'medium',
          title: 'Speed Up Your Workflow',
          description: 'Use bulk actions to fix similar issues across multiple columns',
          action: 'Show Bulk Actions',
          icon: Zap,
          color: 'blue'
        });
      }

      return recs;
    };

    setRecommendations(generateRecommendations());
  }, [dataQuality, userBehavior]);

  return (
    <div className="space-y-3">
      <AnimatePresence>
        {recommendations.map((rec, index) => (
          <motion.div
            key={rec.id}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ delay: index * 0.1 }}
            className={`
              p-4 border-l-4 rounded-lg bg-${rec.color}-50 border-${rec.color}-400
            `}
          >
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 bg-${rec.color}-100 rounded-full flex items-center justify-center`}>
                <rec.icon className={`w-4 h-4 text-${rec.color}-600`} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-medium text-sm">{rec.title}</h4>
                  <Badge variant={rec.priority === 'high' ? 'destructive' : 'default'} className="text-xs">
                    {rec.priority}
                  </Badge>
                </div>
                <p className="text-xs text-gray-600 mb-3">{rec.description}</p>
                <Button size="sm" variant="outline" className="text-xs h-6">
                  {rec.action}
                </Button>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
```

---

## 📱 Responsive Interaction Patterns

### 1. Touch-Friendly Mobile Interactions

#### Mobile Upload Experience
```tsx
// Mobile-Optimized Upload
const MobileUploadZone = () => {
  const [isDragging, setIsDragging] = useState(false);

  return (
    <div className="sm:hidden">
      <motion.div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300
          ${isDragging ? 'border-blue-400 bg-blue-50 scale-105' : 'border-gray-300'}
        `}
        whileTap={{ scale: 0.98 }}
      >
        <div className="space-y-4">
          <motion.div
            animate={{ y: [0, -5, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <CloudUpload className="w-12 h-12 mx-auto text-gray-400" />
          </motion.div>

          <div>
            <h3 className="text-lg font-semibold mb-2">Tap to Upload</h3>
            <p className="text-sm text-gray-600">
              CSV, Excel, or JSON files
            </p>
          </div>

          <Button size="lg" className="w-full">
            <Plus className="w-5 h-5 mr-2" />
            Choose File
          </Button>
        </div>
      </motion.div>
    </div>
  );
};
```

#### Swipe Actions for Mobile
```tsx
// Swipe-to-Action Pattern
const SwipeableIssueCard = ({ issue, onFix, onDismiss }) => {
  const [swipeDirection, setSwipeDirection] = useState(null);

  return (
    <motion.div
      className="relative overflow-hidden bg-white border rounded-lg"
      drag="x"
      dragConstraints={{ left: -100, right: 100 }}
      dragElastic={0.2}
      onDragEnd={(_, info) => {
        if (info.offset.x > 50) {
          onFix(issue.id);
        } else if (info.offset.x < -50) {
          onDismiss(issue.id);
        }
      }}
      onDrag={(_, info) => {
        if (info.offset.x > 20) {
          setSwipeDirection('fix');
        } else if (info.offset.x < -20) {
          setSwipeDirection('dismiss');
        } else {
          setSwipeDirection(null);
        }
      }}
    >
      {/* Background actions */}
      <div className="absolute inset-0 flex">
        <div className={`
          flex-1 flex items-center justify-start pl-4 transition-colors
          ${swipeDirection === 'fix' ? 'bg-green-100' : 'bg-gray-50'}
        `}>
          <CheckCircle className="w-6 h-6 text-green-600" />
          <span className="ml-2 text-sm font-medium text-green-800">Fix</span>
        </div>
        <div className={`
          flex-1 flex items-center justify-end pr-4 transition-colors
          ${swipeDirection === 'dismiss' ? 'bg-red-100' : 'bg-gray-50'}
        `}>
          <span className="mr-2 text-sm font-medium text-red-800">Dismiss</span>
          <X className="w-6 h-6 text-red-600" />
        </div>
      </div>

      {/* Card content */}
      <div className="relative bg-white p-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          <div className="flex-1">
            <h4 className="font-medium text-sm">{issue.title}</h4>
            <p className="text-xs text-gray-600">{issue.description}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
```

### 2. Keyboard Navigation

#### Comprehensive Keyboard Support
```tsx
// Keyboard Navigation Handler
const useKeyboardNavigation = (items, onSelect, onAction) => {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, items.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          onSelect(items[selectedIndex]);
          break;
        case ' ': // Space
          e.preventDefault();
          onAction(items[selectedIndex]);
          break;
        case 'Escape':
          e.preventDefault();
          setSelectedIndex(0);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [items, selectedIndex, onSelect, onAction]);

  return selectedIndex;
};
```

This comprehensive interaction design system creates an intuitive, delightful, and efficient user experience for data quality management. Every interaction is designed to provide immediate feedback, guide users naturally through their tasks, and leverage AI assistance to make complex data operations simple and accessible.