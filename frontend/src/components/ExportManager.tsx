import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

interface ExportManagerProps {
  className?: string;
}

interface ExportFormat {
  id: string;
  name: string;
  description: string;
  extension: string;
  icon: string;
}

const exportFormats: ExportFormat[] = [
  {
    id: 'pdf',
    name: 'PDF',
    description: 'Portable Document Format - perfect for reading and printing',
    extension: '.pdf',
    icon: '📄'
  },
  {
    id: 'epub',
    name: 'EPUB',
    description: 'E-book format compatible with most e-readers',
    extension: '.epub',
    icon: '📚'
  },
  {
    id: 'docx',
    name: 'Word Document',
    description: 'Microsoft Word document for editing',
    extension: '.docx',
    icon: '📝'
  },
  {
    id: 'markdown',
    name: 'Markdown',
    description: 'Plain text format for developers',
    extension: '.md',
    icon: '📋'
  },
  {
    id: 'html',
    name: 'HTML',
    description: 'Web page format for online viewing',
    extension: '.html',
    icon: '🌐'
  }
];

export const ExportManager: React.FC<ExportManagerProps> = ({ className = '' }) => {
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['pdf']);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState<Record<string, number>>({});
  const [exportResults, setExportResults] = useState<Record<string, { success: boolean; url?: string; error?: string }>>({});
  const [bookTitle, setBookTitle] = useState<string>('');

  const handleFormatToggle = (formatId: string) => {
    setSelectedFormats(prev => 
      prev.includes(formatId) 
        ? prev.filter(id => id !== formatId)
        : [...prev, formatId]
    );
  };

  const simulateExport = async (format: ExportFormat) => {
    const steps = [
      'Preparing content...',
      'Formatting text...',
      'Generating structure...',
      'Creating final file...',
      'Optimizing output...'
    ];

    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
      setExportProgress(prev => ({
        ...prev,
        [format.id]: Math.round(((i + 1) / steps.length) * 100)
      }));
    }

    // Simulate success/failure
    const success = Math.random() > 0.1; // 90% success rate
    
    if (success) {
      const fileName = `${bookTitle || 'generated-book'}${format.extension}`;
      const mockUrl = `/downloads/${fileName}`;
      
      setExportResults(prev => ({
        ...prev,
        [format.id]: { success: true, url: mockUrl }
      }));
    } else {
      setExportResults(prev => ({
        ...prev,
        [format.id]: { 
          success: false, 
          error: `Failed to export to ${format.name}. Please try again.` 
        }
      }));
    }
  };

  const handleExport = async () => {
    if (selectedFormats.length === 0) {
      alert('Please select at least one export format.');
      return;
    }

    setIsExporting(true);
    setExportProgress({});
    setExportResults({});

    try {
      // Export each format concurrently
      const exportPromises = selectedFormats.map(formatId => {
        const format = exportFormats.find(f => f.id === formatId)!;
        return simulateExport(format);
      });

      await Promise.all(exportPromises);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDownload = (url: string, filename: string) => {
    // In a real implementation, this would trigger an actual download
    alert(`Download would start for: ${filename}\nURL: ${url}`);
  };

  const getStatusIcon = (formatId: string) => {
    if (exportResults[formatId]) {
      return exportResults[formatId].success ? '✅' : '❌';
    }
    if (isExporting && selectedFormats.includes(formatId)) {
      return '🔄';
    }
    return '⏳';
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Export & Download</h2>
        <div className="text-sm text-gray-500">
          Select formats and export your generated book
        </div>
      </div>

      {/* Book Title Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Book Title (for filename)
        </label>
        <input
          type="text"
          value={bookTitle}
          onChange={(e) => setBookTitle(e.target.value)}
          placeholder="Enter book title..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isExporting}
        />
      </div>

      {/* Format Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Select Export Formats</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {exportFormats.map((format) => (
            <div
              key={format.id}
              className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                selectedFormats.includes(format.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              } ${isExporting ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => !isExporting && handleFormatToggle(format.id)}
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{format.icon}</div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-800">{format.name}</h4>
                    <div className="text-lg">{getStatusIcon(format.id)}</div>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{format.description}</p>
                  <div className="text-xs text-gray-500 mt-2">
                    File: *{format.extension}
                  </div>
                  
                  {/* Progress Bar */}
                  {isExporting && selectedFormats.includes(format.id) && exportProgress[format.id] && (
                    <div className="mt-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${exportProgress[format.id]}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {exportProgress[format.id]}% complete
                      </div>
                    </div>
                  )}

                  {/* Export Result */}
                  {exportResults[format.id] && (
                    <div className="mt-3">
                      {exportResults[format.id].success ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownload(
                              exportResults[format.id].url!,
                              `${bookTitle || 'generated-book'}${format.extension}`
                            );
                          }}
                          className="text-sm bg-green-100 text-green-800 px-3 py-1 rounded hover:bg-green-200 transition-colors"
                        >
                          📥 Download
                        </button>
                      ) : (
                        <div className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded">
                          {exportResults[format.id].error}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Export Controls */}
      <div className="flex justify-between items-center pt-4 border-t">
        <div className="text-sm text-gray-600">
          {selectedFormats.length} format{selectedFormats.length !== 1 ? 's' : ''} selected
        </div>
        
        <div className="flex space-x-3">
          {isExporting && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Exporting...</span>
            </div>
          )}
          
          <button
            onClick={handleExport}
            disabled={isExporting || selectedFormats.length === 0}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              isExporting || selectedFormats.length === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            } text-white`}
          >
            {isExporting ? 'Exporting...' : 'Start Export'}
          </button>
        </div>
      </div>

      {/* Export Summary */}
      {Object.keys(exportResults).length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Export Summary</h4>
          <div className="space-y-2">
            {Object.entries(exportResults).map(([formatId, result]) => {
              const format = exportFormats.find(f => f.id === formatId)!;
              return (
                <div key={formatId} className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">
                    {format.icon} {format.name}
                  </span>
                  <span className={result.success ? 'text-green-600' : 'text-red-600'}>
                    {result.success ? 'Success' : 'Failed'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-800 mb-2">📋 Export Information</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• PDF: Best for reading and printing with preserved formatting</li>
          <li>• EPUB: Compatible with Kindle, Apple Books, and other e-readers</li>
          <li>• Word: Editable format for further customization</li>
          <li>• Markdown: Developer-friendly plain text format</li>
          <li>• HTML: Web-ready format for online publishing</li>
        </ul>
      </div>
    </div>
  );
};

export default ExportManager;