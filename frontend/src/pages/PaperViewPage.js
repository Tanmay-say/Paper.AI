import React from 'react';
import { ArrowLeft, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import PDFViewer from '@/components/PDFViewer';
import ChatInterface from '@/components/ChatInterface';
import usePaperStore from '@/store/paperStore';
import { paperAPI } from '@/services/api';

const PaperViewPage = () => {
  const navigate = useNavigate();
  const { selectedPaper, selectedPaperId } = usePaperStore();

  if (!selectedPaper) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <BookOpen size={64} className="text-gray-400 mx-auto" />
          <p className="text-gray-600">No paper selected</p>
          <Button onClick={() => navigate('/')}>Go Back</Button>
        </div>
      </div>
    );
  }

  const pdfUrl = paperAPI.getPaperPDF(selectedPaperId);

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div className="flex items-center gap-4">
          <Button
            data-testid="back-button"
            onClick={() => navigate('/')}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <ArrowLeft size={16} />
            Back to Search
          </Button>
          
          <div className="flex-1">
            <h1 className="font-semibold text-lg text-gray-900 line-clamp-1">
              {selectedPaper.title}
            </h1>
            <p className="text-sm text-gray-600">
              {selectedPaper.authors.join(', ')} • {selectedPaper.year}
            </p>
          </div>
        </div>
      </header>

      {/* Main Content: PDF + Chat */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 min-h-0">
          {/* PDF Viewer */}
          <div className="h-full min-h-0">
            <PDFViewer pdfUrl={pdfUrl} />
          </div>

          {/* Chat Interface */}
          <div className="h-full min-h-0">
            <ChatInterface />
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaperViewPage;