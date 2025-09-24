# Data Source Connection Components

This directory contains the complete frontend implementation for the Data Source Connection feature.

## 📁 File Structure

```
src/components/data-management/
├── data-source-connection.tsx    # Main component orchestrating the workflow
└── index.ts                      # Component exports

src/components/ui/
├── file-dropzone.tsx            # File upload drag & drop interface
├── upload-progress.tsx           # Upload progress tracking component
└── data-preview-table.tsx       # Data preview and quality check display

src/hooks/
├── use-data-source-upload.ts     # Upload state management hook
└── use-data-preview.ts          # Data preview state management hook

src/lib/api/
├── data-sources.ts              # API client for backend integration
└── types/data-sources.ts        # TypeScript type definitions

src/app/
└── data-management/
    └── page.tsx                 # Main data management page
```

## 🚀 Key Features Implemented

### 1. **File Upload with Drag & Drop**
- Support for CSV, JSON, Excel (.xlsx, .xls), and Parquet files
- Drag & drop interface with visual feedback
- File validation (size, type, format)
- Maximum file size: 100MB

### 2. **Chunked Upload System**
- Large file support with chunked upload
- Real-time progress tracking
- Resume capability and error handling
- Upload cancellation support

### 3. **Data Preview & Quality Checks**
- Automatic data type detection
- Sample data preview with pagination
- Column statistics (unique values, missing values, min/max)
- Data quality issue detection and reporting
- Interactive column details

### 4. **Multi-Step User Interface**
- Step-by-step guided workflow
- Progress indicator with visual states
- Error states and retry mechanisms
- Responsive design for all screen sizes

### 5. **TypeScript Integration**
- Complete type safety with backend API
- Proper error handling and validation
- Type definitions for all components and hooks

## 🔧 API Integration

The components integrate with the backend APIs at:
- **Upload**: `POST /api/v1/data/upload`
- **Preview**: `GET /api/v1/data/preview/{datasetId}`
- **Management**: `/api/v1/data/sources/*`

## 📊 Component Usage

### Basic Usage

```tsx
import { DataSourceConnection } from '@/components/data-management';

function MyPage() {
  return (
    <DataSourceConnection
      projectId={1}
      onConnectionComplete={(dataset) => {
        console.log('Dataset connected:', dataset);
      }}
    />
  );
}
```

### Individual Components

```tsx
import {
  FileDropzone,
  UploadProgress,
  DataPreviewTable
} from '@/components/data-management';

// File upload only
<FileDropzone
  onFileSelect={handleFileSelect}
  onError={handleError}
/>

// Upload progress tracking
<UploadProgress
  progress={uploadProgress}
  fileName={file.name}
  fileSize={file.size}
  uploadedSize={uploadedBytes}
  status="uploading"
  onCancel={handleCancel}
/>

// Data preview
<DataPreviewTable
  preview={previewData}
  qualityChecks={qualityChecks}
  maxRows={10}
/>
```

### Custom Hooks

```tsx
import {
  useDataSourceUpload,
  useDataPreview
} from '@/components/data-management';

function MyUploadComponent() {
  const { uploadState, uploadFile, cancelUpload } = useDataSourceUpload({
    projectId: 1,
    onUploadComplete: (dataset) => {
      // Handle completion
    }
  });

  const { state: previewState, loadPreview } = useDataPreview({
    datasetId: uploadState.dataset?.id,
    autoLoad: true
  });

  // Component logic...
}
```

## 🎨 Styling & Design

- Built with **Radix UI** primitives for accessibility
- **Tailwind CSS** for responsive styling
- **Lucide React** icons for consistent iconography
- Follows existing design system patterns
- Dark mode support via CSS variables

## 🔒 Error Handling

- File validation errors with user-friendly messages
- Network error handling with retry mechanisms
- Upload timeout handling
- Backend API error parsing and display
- Progressive error recovery options

## ♿ Accessibility Features

- ARIA labels for screen readers
- Keyboard navigation support
- Focus management
- High contrast mode support
- Semantic HTML structure

## 🧪 Development Notes

### Testing the Components

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Navigate to `/data-management` to test the full workflow

3. Test with different file types and sizes

### Backend Integration

The components expect the backend to be running on `http://localhost:8000` (configurable via `NEXT_PUBLIC_API_URL`).

Ensure the following endpoints are available:
- `POST /api/v1/data/upload` - File upload
- `GET /api/v1/data/preview/{id}` - Data preview
- `GET /api/v1/data/sources` - List datasets
- `DELETE /api/v1/data/sources/{id}` - Delete dataset

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API base URL
```

## 🔄 Integration with Sidebar

The feature is integrated into the main navigation via `/data-management` route with:
- "Data Management" sidebar entry
- "New" badge to highlight the feature
- Sub-navigation for future features (connections, quality reports)

## 🚀 Future Enhancements

The current implementation provides a solid foundation for:
- Multiple data source types (databases, APIs)
- Advanced data transformation features
- Real-time collaboration on datasets
- Advanced analytics and visualization
- Data lineage tracking
- Integration with ML pipelines

---

**✅ Implementation Status**: Complete and functional
**🔗 Backend Integration**: Ready (requires backend APIs)
**📱 Responsive Design**: Fully responsive
**♿ Accessibility**: WCAG 2.1 AA compliant
**🎨 Design System**: Consistent with existing patterns