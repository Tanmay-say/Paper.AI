import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const paperAPI = {
  searchPapers: async (query, maxResults = 10) => {
    const response = await api.post('/papers/search', {
      query,
      max_results: maxResults,
      source: 'arxiv'
    });
    return response.data;
  },
  
  getPaper: async (paperId) => {
    const response = await api.get(`/papers/${paperId}`);
    return response.data;
  },
  
  getPaperPDF: (paperId) => {
    return `${API_BASE}/papers/${paperId}/pdf`;
  },
};

export const chatAPI = {
  sendQuery: async (paperId, query, selectedText = null, chatHistory = []) => {
    const response = await api.post('/chat/query', {
      paper_id: paperId,
      query,
      selected_text: selectedText,
      chat_history: chatHistory
    });
    return response.data;
  },
  
  createWebSocket: () => {
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    return new WebSocket(`${wsUrl}/api/ws/chat`);
  },
};

export const ingestionAPI = {
  ingestPapers: async (paperIds) => {
    const response = await api.post('/ingest/papers', {
      paper_ids: paperIds,
      source: 'arxiv'
    });
    return response.data;
  },
  
  getIngestionStatus: async (jobId) => {
    const response = await api.get(`/ingest/status/${jobId}`);
    return response.data;
  },
};

export default api;