import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import ReactMarkdown from 'react-markdown';
import usePaperStore from '@/store/paperStore';
import { chatAPI } from '@/services/api';
import { toast } from 'sonner';

const ChatInterface = () => {
  const { 
    selectedPaperId, 
    messages, 
    addMessage, 
    isLoading, 
    setIsLoading,
    selectedText,
    setSelectedText
  } = usePaperStore();
  
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (selectedText) {
      inputRef.current?.focus();
    }
  }, [selectedText]);

  const handleSend = async () => {
    if (!input.trim() || isLoading || !selectedPaperId) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    addMessage(userMessage);
    setInput('');
    setIsLoading(true);

    try {
      const chatHistory = messages.map(m => ({
        role: m.role,
        content: m.content,
        timestamp: m.timestamp
      }));

      const response = await chatAPI.sendQuery(
        selectedPaperId,
        input,
        selectedText,
        chatHistory
      );

      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources,
        timestamp: new Date().toISOString(),
      };

      addMessage(assistantMessage);
      setSelectedText(null); // Clear selected text after using it
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to get response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-xl overflow-hidden border border-gray-200">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
        <div className="flex items-center gap-2">
          <Bot size={24} />
          <div>
            <h3 className="font-semibold text-lg">Research Assistant</h3>
            <p className="text-sm text-blue-100">Ask questions about the paper</p>
          </div>
        </div>
      </div>

      {/* Selected Text Banner */}
      {selectedText && (
        <div className="p-3 bg-blue-50 border-b border-blue-200">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Sparkles size={14} className="text-blue-600" />
                <span className="text-xs font-medium text-blue-900">Selected Text</span>
              </div>
              <p className="text-sm text-gray-700 line-clamp-2 italic">"{selectedText}"</p>
            </div>
            <Button
              onClick={() => setSelectedText(null)}
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 text-gray-500 hover:text-gray-700"
            >
              <X size={16} />
            </Button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div data-testid="chat-messages" className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center">
            <div className="space-y-4">
              <Bot size={48} className="text-gray-300 mx-auto" />
              <div>
                <p className="text-gray-600 font-medium">Start a conversation</p>
                <p className="text-sm text-gray-500 mt-2">Select text in the PDF or ask any question</p>
              </div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              data-testid={`chat-message-${message.role}`}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
                  <Bot size={18} className="text-white" />
                </div>
              )}
              
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <ReactMarkdown className="text-sm leading-relaxed prose prose-sm max-w-none">
                  {message.content}
                </ReactMarkdown>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 space-y-1">
                    <p className="text-xs font-medium text-gray-500">Sources:</p>
                    {message.sources.map((source, i) => (
                      <Badge key={i} variant="outline" className="text-xs mr-1">
                        Chunk {i + 1} (score: {source.score.toFixed(2)})
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              
              {message.role === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                  <User size={18} className="text-white" />
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center">
              <Bot size={18} className="text-white" />
            </div>
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="flex gap-2">
          <Input
            ref={inputRef}
            data-testid="chat-input"
            type="text"
            placeholder="Ask about the paper..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading || !selectedPaperId}
            className="flex-1 rounded-xl"
          />
          <Button
            data-testid="chat-send-button"
            onClick={handleSend}
            disabled={isLoading || !input.trim() || !selectedPaperId}
            className="rounded-xl bg-blue-500 hover:bg-blue-600"
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;