import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { paperAPI } from '@/services/api';
import usePaperStore from '@/store/paperStore';
import { toast } from 'sonner';

const SearchBar = () => {
  const [query, setQuery] = useState('');
  const { setSearchResults, setIsSearching, isSearching } = usePaperStore();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const results = await paperAPI.searchPapers(query, 20);
      setSearchResults(results);
      if (results.length === 0) {
        toast.info('No papers found. Try different keywords.');
      }
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Failed to search papers. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <form onSubmit={handleSearch} className="w-full max-w-3xl">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        <Input
          data-testid="search-input"
          type="text"
          placeholder="Search research papers... (e.g., 'transformer attention mechanism')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-12 pr-32 h-14 text-base bg-white/90 backdrop-blur-sm border-gray-200 focus:border-blue-400 rounded-2xl shadow-lg"
          disabled={isSearching}
        />
        <Button
          data-testid="search-button"
          type="submit"
          disabled={isSearching || !query.trim()}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-10 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700"
        >
          {isSearching ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Searching
            </>
          ) : (
            'Search'
          )}
        </Button>
      </div>
    </form>
  );
};

export default SearchBar;