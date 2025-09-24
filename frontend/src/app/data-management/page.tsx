"use client";

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { Database, Plus, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ProtectedRoute } from '@/components/auth';
import { DataSource } from '@/lib/api/types/data-sources';

// 动态导入大型组件以优化首屏加载
const DataSourceConnection = dynamic(
  () => import('@/components/data-management/data-source-connection'),
  {
    loading: () => (
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse">Loading...</div>
      </div>
    )
  }
);

function DataManagementContent() {
  const [showConnection, setShowConnection] = useState(false);
  const [connectedSources, setConnectedSources] = useState<DataSource[]>([]);

  // Mock project ID - in a real app, this would come from routing or context
  const projectId = 1;

  const handleConnectionComplete = (dataset: DataSource) => {
    setConnectedSources(prev => [...prev, dataset]);
    setShowConnection(false);
  };

  const handleCancelConnection = () => {
    setShowConnection(false);
  };

  if (showConnection) {
    return (
      <div className="container mx-auto py-6">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={handleCancelConnection}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Data Management
          </Button>
        </div>
        <DataSourceConnection
          projectId={projectId}
          onConnectionComplete={handleConnectionComplete}
          onCancel={handleCancelConnection}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Data Management</h1>
          <p className="text-muted-foreground">
            Manage your data sources and connections for AI analysis
          </p>
        </div>
        <Button onClick={() => setShowConnection(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Connect Data Source
        </Button>
      </div>

      {/* Connected Sources */}
      {connectedSources.length > 0 ? (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Connected Data Sources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {connectedSources.map((source) => (
              <Card key={source.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center justify-between text-base">
                    <div className="flex items-center space-x-2">
                      <Database className="w-5 h-5 text-primary" />
                      <span className="truncate">{source.name}</span>
                    </div>
                    <Badge
                      variant={source.status === 'ready' ? 'default' : 'secondary'}
                    >
                      {source.status}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Type:</span>
                      <span className="font-medium">{source.type.toUpperCase()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Rows:</span>
                      <span className="font-medium">
                        {source.rows_count?.toLocaleString() || '—'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Columns:</span>
                      <span className="font-medium">{source.columns_count || '—'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Size:</span>
                      <span className="font-medium">
                        {source.file_size
                          ? `${(source.file_size / 1024 / 1024).toFixed(1)}MB`
                          : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Created:</span>
                      <span className="font-medium">
                        {new Date(source.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ) : (
        /* Empty State */
        <Card className="text-center py-12">
          <CardContent>
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto bg-muted rounded-full flex items-center justify-center">
                <Database className="w-8 h-8 text-muted-foreground" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">No Data Sources Connected</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Get started by connecting your first data source. Upload CSV, JSON, Excel, or
                  Parquet files to begin your data analysis journey.
                </p>
              </div>
              <Button onClick={() => setShowConnection(true)} size="lg">
                <Plus className="w-4 h-4 mr-2" />
                Connect Your First Data Source
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Features Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Multiple Formats</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Support for CSV, JSON, Excel, and Parquet files with automatic type detection
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Data Quality Checks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Automatic data quality analysis with missing value detection and statistics
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Large File Support</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Chunked upload for files up to 100MB with progress tracking and resume capability
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DataManagementPage() {
  return (
    <ProtectedRoute>
      <DataManagementContent />
    </ProtectedRoute>
  );
}