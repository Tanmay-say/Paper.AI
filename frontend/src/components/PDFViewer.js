import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut, Loader2, FileText, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import usePaperStore from '@/store/paperStore';
import { ingestionAPI } from '@/services/api';
import { toast } from 'sonner';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF.js worker - use local worker file
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

const PDFViewer = ({ pdfUrl }) => {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const { setSelectedText, selectedPaperId } = usePaperStore();

  useEffect(() => {
    setError(false);
    setLoading(true);
  }, [pdfUrl]);

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(false);
  };

  const onDocumentLoadError = (error) => {
    console.error('PDF load error:', error);
    setLoading(false);
    setError(true);
  };

  const handleRetry = async () => {
    if (!selectedPaperId) return;
    
    setRetrying(true);
    toast.loading('Re-processing paper...', { id: 'retry' });
    
    try {
      await ingestionAPI.ingestPapers([selectedPaperId]);
      
      // Wait a bit for processing
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Reload the PDF
      setError(false);
      setLoading(true);
      toast.success('Please wait for the PDF to load', { id: 'retry' });
      
      // Force reload by adding timestamp to URL
      window.location.reload();
    } catch (err) {
      console.error('Retry error:', err);
      toast.error('Failed to re-process paper', { id: 'retry' });
    } finally {
      setRetrying(false);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const selectedText = selection?.toString().trim();
    if (selectedText && selectedText.length > 10) {
      setSelectedText(selectedText);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 rounded-xl overflow-hidden border border-gray-200">
      {/* Controls */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Button
            data-testid="pdf-prev-page"
            onClick={() => setPageNumber(prev => Math.max(1, prev - 1))}
            disabled={pageNumber <= 1}
            variant="outline"
            size="sm"
          >
            <ChevronLeft size={16} />
          </Button>
          <span className="text-sm text-gray-700 min-w-[100px] text-center">
            Page {pageNumber} of {numPages || '...'}
          </span>
          <Button
            data-testid="pdf-next-page"
            onClick={() => setPageNumber(prev => Math.min(numPages || 1, prev + 1))}
            disabled={pageNumber >= (numPages || 1)}
            variant="outline"
            size="sm"
          >
            <ChevronRight size={16} />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => setScale(prev => Math.max(0.5, prev - 0.1))}
            variant="outline"
            size="sm"
          >
            <ZoomOut size={16} />
          </Button>
          <span className="text-sm text-gray-700 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          <Button
            onClick={() => setScale(prev => Math.min(2.0, prev + 0.1))}
            variant="outline"
            size="sm"
          >
            <ZoomIn size={16} />
          </Button>
        </div>
      </div>

      {/* PDF Display */}
      <div 
        className="flex-1 overflow-auto p-6 flex justify-center"
        onMouseUp={handleTextSelection}
      >
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-blue-500 mx-auto" />
              <p className="text-gray-600">Loading PDF...</p>
            </div>
          </div>
        )}
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading=""
          error={
            <div className="text-center space-y-4 p-8">
              <FileText className="h-16 w-16 text-gray-400 mx-auto" />
              <div className="space-y-2">
                <p className="text-gray-600 font-medium">Failed to load PDF</p>
                <p className="text-sm text-gray-500">The paper might still be processing</p>
                <p className="text-xs text-gray-400">This usually takes 20-30 seconds</p>
              </div>
              <Button
                onClick={handleRetry}
                disabled={retrying}
                variant="outline"
                className="mt-4"
              >
                {retrying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Re-processing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Retry / Re-process
                  </>
                )}
              </Button>
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            renderTextLayer={true}
            renderAnnotationLayer={true}
            className="shadow-lg"
          />
        </Document>
      </div>
    </div>
  );
};

export default PDFViewer;