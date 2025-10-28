import google.generativeai as genai
from typing import List, Dict, Any
import logging
from config import settings
from models.schemas import RetrievedContext, ChatMessage

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Agent to generate answers using LLM and retrieved context"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
        logger.info("AnswerGenerator initialized")
    
    def _format_context(self, contexts: List[RetrievedContext]) -> str:
        """Format retrieved contexts for the LLM"""
        formatted = []
        for i, ctx in enumerate(contexts, 1):
            formatted.append(f"[Context {i}]\nPaper ID: {ctx.paper_id}\n{ctx.text}\n")
        return "\n".join(formatted)
    
    def _format_chat_history(self, chat_history: List[ChatMessage]) -> str:
        """Format chat history for context"""
        if not chat_history:
            return ""
        
        formatted = ["\nPrevious conversation:"]
        for msg in chat_history[-5:]:  # Last 5 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
    
    async def generate_answer(
        self,
        query: str,
        contexts: List[RetrievedContext],
        selected_text: str = None,
        chat_history: List[ChatMessage] = None
    ) -> str:
        """Generate an answer using the LLM"""
        
        context_text = self._format_context(contexts)
        history_text = self._format_chat_history(chat_history or [])
        selected_context = f"\n\nSelected Text:\n{selected_text}" if selected_text else ""
        
        prompt = f"""
You are an AI assistant specialized in research paper analysis. Your goal is to provide accurate, insightful answers based on the research paper content.

Retrieved Context:
{context_text}
{history_text}{selected_context}

User Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. Be specific and cite relevant information from the context
3. If the selected text is provided, focus your answer on that specific portion
4. If the context doesn't contain enough information, acknowledge this
5. Provide clear, well-structured answers
6. Use academic language appropriate for research discussion

Answer:
"""
        
        try:
            response = self.model.generate_content(prompt)
            answer = response.text.strip()
            logger.info(f"Generated answer for query: {query[:50]}...")
            return answer
        
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "I apologize, but I encountered an error while generating the answer. Please try again."
    
    async def generate_streaming_answer(
        self,
        query: str,
        contexts: List[RetrievedContext],
        selected_text: str = None,
        chat_history: List[ChatMessage] = None
    ):
        """Generate an answer with streaming response"""
        
        context_text = self._format_context(contexts)
        history_text = self._format_chat_history(chat_history or [])
        selected_context = f"\n\nSelected Text:\n{selected_text}" if selected_text else ""
        
        prompt = f"""
You are an AI assistant specialized in research paper analysis. Your goal is to provide accurate, insightful answers based on the research paper content.

Retrieved Context:
{context_text}
{history_text}{selected_context}

User Question: {query}

Instructions:
1. Answer based primarily on the provided context
2. Be specific and cite relevant information from the context
3. If the selected text is provided, focus your answer on that specific portion
4. If the context doesn't contain enough information, acknowledge this
5. Provide clear, well-structured answers
6. Use academic language appropriate for research discussion

Answer:
"""
        
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as e:
            logger.error(f"Error in streaming answer: {e}")
            yield "I apologize, but I encountered an error while generating the answer."


answer_generator = AnswerGenerator()