# PaperAI - Research Paper Analysis Platform

PaperAI is an intelligent research paper analysis platform that uses AI and Graph RAG (Retrieval-Augmented Generation) to help researchers discover, understand, and interact with academic literature.

## 🚀 Features

- **Smart Search**: Search millions of papers from arXiv with intelligent search algorithms
- **PDF Analysis**: Read papers with text selection and highlighting capabilities
- **AI Assistant**: Chat with AI about research papers and get context-aware answers
- **Graph Knowledge Base**: Papers stored in Neo4j graph database with vector embeddings
- **Hybrid Retrieval**: Combines vector search and graph traversal for better results
- **Real-time Streaming**: WebSocket support for streaming AI responses

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with Neo4j, Redis, and Celery workers
- **Frontend**: React with Tailwind CSS and shadcn/ui components
- **Database**: Neo4j (graph database) for paper metadata and relationships
- **Task Queue**: Celery with Redis broker
- **AI**: Google Gemini API for embeddings and LLM
- **Storage**: Local PDF storage

## 📋 Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** and npm/yarn
- **Docker & Docker Compose** (for databases)
- **Gemini API Key** from [Google AI Studio](https://ai.google.dev/)

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Papz.AI
```

### 2. Start Infrastructure Services

Start Neo4j, Redis, and PostgreSQL using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- **Neo4j**: Available at `http://localhost:7474` (Web UI) and `bolt://localhost:7687`
- **Redis**: Available at `redis://localhost:6379`
- **PostgreSQL**: Available at `postgresql://localhost:5432`

### 3. Backend Setup

Navigate to the backend directory and set up the Python environment:

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file and configure it
# Copy the example file or edit directly
# You need to set your GEMINI_API_KEY
```

Edit `backend/.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd ../frontend

# Install dependencies
yarn install
# or
npm install

# The .env file should already be created
# Ensure REACT_APP_BACKEND_URL=http://localhost:8000
```

### 5. Run the Application

**Terminal 1 - Backend Server:**
```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker (for paper ingestion):**
```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

**Terminal 3 - Frontend:**
```bash
cd frontend
yarn start
# or
npm start
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📚 Usage

### Searching for Papers

1. Use the search bar to find papers from arXiv
2. Browse search results
3. Click on a paper to view it

### Ingesting Papers

Before you can chat with a paper, you need to ingest it:

1. Select a paper from search results
2. The system will automatically download the PDF
3. Text is extracted, chunked, and embedded
4. Data is stored in Neo4j graph database

### Chatting with Papers

1. After ingestion, open the paper viewer
2. Select text in the PDF for context
3. Ask questions in the chat interface
4. Get AI-generated answers based on the paper content

## 🔧 Configuration

### Backend Environment Variables (`backend/.env`)

```env
# Gemini API (Required)
GEMINI_API_KEY=your_api_key_here

# Neo4j (Already configured for Docker)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=paperai123

# Redis
REDIS_URL=redis://localhost:6379/0

# MongoDB (Optional, for user data)
MONGO_URL=mongodb://localhost:27017/
DB_NAME=paperai

# Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_DIMENSION=768
```

### Frontend Environment Variables (`frontend/.env`)

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

## 🧪 Testing the API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Search Papers
```bash
curl -X POST "http://localhost:8000/api/papers/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "transformer neural network",
    "max_results": 5
  }'
```

### Ingest Papers
```bash
curl -X POST "http://localhost:8000/api/ingest/papers" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_ids": ["2103.14030"],
    "source": "arxiv"
  }'
```

### Chat with Paper
```bash
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "2103.14030",
    "query": "What is the main contribution?",
    "chat_history": []
  }'
```

## 📁 Project Structure

```
Papz.AI/
├── backend/
│   ├── agents/           # AI agents (discovery, retrieval, etc.)
│   ├── models/           # Data models and schemas
│   ├── services/         # Core services (Neo4j, embeddings)
│   ├── workers/          # Celery tasks
│   ├── config.py         # Configuration
│   ├── server.py         # FastAPI server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── store/         # State management
│   └── package.json
├── storage/
│   └── pdfs/             # Downloaded PDFs
├── docker-compose.yml    # Infrastructure services
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License

## ⚠️ Troubleshooting

### Backend won't start
- Ensure all environment variables are set
- Check that Neo4j and Redis are running: `docker-compose ps`
- Verify Gemini API key is valid

### Frontend can't connect to backend
- Check that backend is running on port 8000
- Verify `REACT_APP_BACKEND_URL` in `frontend/.env`
- Check browser console for CORS errors

### Paper ingestion fails
- Ensure Celery worker is running
- Check Redis connection
- Verify PDF storage path exists
- Check logs for detailed errors

### Neo4j connection issues
- Ensure Neo4j container is running
- Check credentials match in `.env`
- Try accessing Neo4j browser at `http://localhost:7474`

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ for the research community**
