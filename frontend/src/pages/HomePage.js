import React, { useEffect } from 'react';
import { BookOpen, Sparkles, Search as SearchIcon } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import SearchResults from '@/components/SearchResults';
import usePaperStore from '@/store/paperStore';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
  const { selectedPaper } = usePaperStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (selectedPaper) {
      navigate('/paper');
    }
  }, [selectedPaper, navigate]);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-xl">
              <BookOpen className="text-white" size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                PaperAI
              </h1>
              <p className="text-sm text-gray-600">Research Paper Analysis Platform</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-12 text-center">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full text-sm font-medium">
            <Sparkles size={16} />
            Powered by AI & Graph RAG
          </div>
          
          <h2 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
            Discover & Analyze
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Research Papers
            </span>
          </h2>
          
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Search millions of papers, chat with AI about research, and get intelligent insights
            from academic literature.
          </p>
        </div>

        {/* Search Bar */}
        <div className="mt-12 flex justify-center">
          <SearchBar />
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl mx-auto">
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl border border-gray-200">
            <div className="bg-blue-100 w-12 h-12 rounded-xl flex items-center justify-center mb-4 mx-auto">
              <SearchIcon className="text-blue-600" size={24} />
            </div>
            <h3 className="font-semibold text-lg mb-2">Smart Search</h3>
            <p className="text-sm text-gray-600">Find papers from arXiv with intelligent search algorithms</p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl border border-gray-200">
            <div className="bg-indigo-100 w-12 h-12 rounded-xl flex items-center justify-center mb-4 mx-auto">
              <BookOpen className="text-indigo-600" size={24} />
            </div>
            <h3 className="font-semibold text-lg mb-2">PDF Analysis</h3>
            <p className="text-sm text-gray-600">Read papers with text selection and highlighting</p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl border border-gray-200">
            <div className="bg-purple-100 w-12 h-12 rounded-xl flex items-center justify-center mb-4 mx-auto">
              <Sparkles className="text-purple-600" size={24} />
            </div>
            <h3 className="font-semibold text-lg mb-2">AI Assistant</h3>
            <p className="text-sm text-gray-600">Ask questions and get context-aware answers</p>
          </div>
        </div>
      </section>

      {/* Search Results */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <SearchResults />
      </section>
    </div>
  );
};

export default HomePage;