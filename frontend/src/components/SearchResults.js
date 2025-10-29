import React, { useState } from 'react';
import { FileText, User, Calendar, ExternalLink, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import usePaperStore from '@/store/paperStore';
import { ingestionAPI, paperAPI } from '@/services/api';
import { toast } from 'sonner';

const PaperCard = ({ paper }) => {
  const { setSelectedPaper } = usePaperStore();
  const [isIngesting, setIsIngesting] = useState(false);

  const checkPaperExists = async (paperId) => {
    try {
      await paperAPI.getPaper(paperId);
      return true;
    } catch (error) {
      return false;
    }
  };

  const waitForIngestion = async (paperId, maxAttempts = 20) => {
    for (let i = 0; i < maxAttempts; i++) {
      const exists = await checkPaperExists(paperId);
      if (exists) {
        return true;
      }
      // Wait 2 seconds before checking again
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    return false;
  };

  const handleSelectPaper = async () => {
    if (isIngesting) return;
    
    setIsIngesting(true);
    
    // First check if paper already exists
    const alreadyExists = await checkPaperExists(paper.paper_id);
    
    if (alreadyExists) {
      toast.success('Paper is ready!');
      setSelectedPaper(paper);
      setIsIngesting(false);
      return;
    }

    // If not, start ingestion
    toast.loading('Processing paper... This may take 20-30 seconds', { id: 'ingest', duration: Infinity });
    
    try {
      // Trigger ingestion
      await ingestionAPI.ingestPapers([paper.paper_id]);
      
      // Wait for ingestion to complete
      toast.loading('Downloading and processing PDF...', { id: 'ingest', duration: Infinity });
      const success = await waitForIngestion(paper.paper_id);
      
      if (success) {
        toast.success('Paper is ready!', { id: 'ingest' });
        setSelectedPaper(paper);
      } else {
        toast.error('Paper processing is taking longer than expected. You can still view it, but PDF might not be available yet.', { id: 'ingest' });
        setSelectedPaper(paper);
      }
    } catch (error) {
      console.error('Ingestion error:', error);
      toast.error('Failed to process paper. You can still try viewing it.', { id: 'ingest' });
      setSelectedPaper(paper);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <Card 
      data-testid={`paper-card-${paper.paper_id}`}
      className="hover:shadow-xl transition-all duration-300 border-gray-200 bg-white/80 backdrop-blur-sm cursor-pointer group"
      onClick={!isIngesting ? handleSelectPaper : undefined}
    >
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            <div className="flex items-center gap-2">
              <FileText className="text-blue-500 flex-shrink-0" size={20} />
              <h3 className="font-semibold text-lg text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                {paper.title}
              </h3>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <User size={14} />
                <span className="line-clamp-1">{paper.authors[0]}</span>
                {paper.authors.length > 1 && (
                  <span className="text-gray-400">+{paper.authors.length - 1} more</span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Calendar size={14} />
                <span>{paper.year}</span>
              </div>
            </div>

            <p className="text-sm text-gray-700 line-clamp-3 leading-relaxed">
              {paper.abstract}
            </p>

            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {paper.source.toUpperCase()}
              </Badge>
              {paper.arxiv_id && (
                <Badge variant="outline" className="text-xs">
                  {paper.arxiv_id}
                </Badge>
              )}
            </div>
          </div>

          <Button
            data-testid={`view-paper-${paper.paper_id}`}
            onClick={(e) => {
              e.stopPropagation();
              handleSelectPaper();
            }}
            size="sm"
            disabled={isIngesting}
            className="flex-shrink-0 bg-blue-500 hover:bg-blue-600 disabled:opacity-50"
          >
            {isIngesting ? (
              <>
                <Loader2 size={16} className="mr-1 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <ExternalLink size={16} className="mr-1" />
                View
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const SearchResults = () => {
  const { searchResults, isSearching } = usePaperStore();

  if (isSearching) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center space-y-4">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
          <p className="text-gray-600">Searching papers...</p>
        </div>
      </div>
    );
  }

  if (searchResults.length === 0) {
    return null;
  }

  return (
    <div data-testid="search-results" className="w-full max-w-5xl space-y-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Found {searchResults.length} papers
      </h2>
      <div className="space-y-4">
        {searchResults.map((paper) => (
          <PaperCard key={paper.paper_id} paper={paper} />
        ))}
      </div>
    </div>
  );
};

export default SearchResults;