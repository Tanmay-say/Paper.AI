import { create } from 'zustand';

const usePaperStore = create((set) => ({
  // Search state
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  
  // Selected paper
  selectedPaper: null,
  selectedPaperId: null,
  
  // Chat state
  messages: [],
  isLoading: false,
  selectedText: null,
  
  // Actions
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSearchResults: (results) => set({ searchResults: results }),
  setIsSearching: (isSearching) => set({ isSearching }),
  
  setSelectedPaper: (paper) => set({ 
    selectedPaper: paper,
    selectedPaperId: paper?.paper_id || null,
    messages: [],
    selectedText: null
  }),
  
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  
  setIsLoading: (isLoading) => set({ isLoading }),
  
  setSelectedText: (text) => set({ selectedText: text }),
  
  clearMessages: () => set({ messages: [] }),
}));

export default usePaperStore;