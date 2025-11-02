# HackTutor

HackTutor is an end-to-end AI tutoring platform that combines a FastAPI backend, a React front end, and a retrieval-augmented content pipeline to generate lessons, diagrams, images, audio narration, and even rendered videos on demand. The project integrates Google Gemini models for text and media generation, enriches lessons with a hybrid Whoosh + Qdrant retriever, and surfaces the experience through a Material UI-powered single-page app. 【F:BackEnd/main.py†L1-L482】【F:FrontEnd/src/App.jsx†L1-L25】

## Architecture

| Layer | Description |
| ----- | ----------- |
| Front end | React + Vite application with Material UI components for onboarding, chat, and lesson playback.  |
| API | FastAPI service orchestrating authentication, chat sessions, lesson generation, asset rendering, and video authoring.  |
| Retrieval | Hybrid retriever that blends BM25 (Whoosh) and dense embeddings (Qdrant + Sentence Transformers) with Maximal Marginal Relevance diversification.  |
| Media services | Gemini-backed generators plus local utilities for gTTS audio, Mermaid diagrams, and MoviePy video assembly. |
| Data layer | SQLAlchemy models persisted via the `DB_URL` connection string; chat artifacts are cached to disk for replay.  |

[![System architecture diagram](https://i.ibb.co/JjntKQdx/Untitled-Diagram-drawio-3.png)](https://ibb.co/1GZQL6ns)

### Repository layout

```
Hacktutor/
├── BackEnd/
│   ├── main.py                # FastAPI application entrypoint
│   ├── auth.py                # JWT auth utilities
│   ├── db_setup/              # SQLAlchemy models and session helpers
│   ├── gemini_api.py          # Gemini text/image helpers and sanitizers
│   ├── retrieval/             # Hybrid search + summarization
│   ├── ingest/                # Corpus ingestion for Whoosh and Qdrant
│   ├── media/                 # Mermaid rendering and image generation
│   ├── gen_video.py           # Slide video pipeline
│   └── requirements.txt       # Python dependencies
└── FrontEnd/
    ├── src/                   # React components and styles
    ├── public/
    └── package.json           # Node dependencies
```

## Key features

- **User management & persistent chat history** – JWT-protected signup, login, profile, and session APIs backed by SQLAlchemy models for users, chat sessions, and messages.
- **Retrieval-augmented lesson planning** – Conversations are normalized into task specs, expanded with hybrid search notes, and transformed into multi-segment lessons enriched with diagrams and image prompts. 
- **Asset rendering pipeline** – Mermaid diagrams are rendered to PNG, image prompts are enriched and generated in parallel, and generated files are exposed via static hosting. 
- **Video authoring** – Lesson prompts can trigger an asynchronous slide video workflow that produces narrated videos and stores progress/state per session. 
- **Responsive learner experience** – The front end provides onboarding modals, chat session management, and real-time updates for AI responses using Material UI and React Router. 

## Prerequisites

- Python 3.11+ with `pip` to install backend dependencies listed in `BackEnd/requirements.txt`. 
- Node.js 20+ (or any version supported by Vite 7) to run the React client specified in `FrontEnd/package.json`. 
- Qdrant vector database running locally on `localhost:6333` for semantic retrieval. 
- FFmpeg (required by MoviePy) if you plan to render narrated videos.
- Google Gemini API access for text, diagram, and image generation.

## Backend setup

1. **Create a virtual environment and install dependencies**
   ```bash
   cd BackEnd
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure environment variables** – create `BackEnd/.env` with values similar to:
   ```env
   API_KEY=your_google_gemini_key
   DB_URL=sqlite:///./hacktutor.db
   SECRET_KEY=change_me
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=4320
   GEMINI_TEXT_MODEL=gemini-2.0-flash
   ```
   The API key powers Gemini calls, the database URL is passed to SQLAlchemy, and JWT secrets configure token issuing. 
3. **Prepare retrieval indexes (optional but recommended)**
   - Add EPUB files to `BackEnd/data/epubs/`.
   - Ensure Qdrant is running, then build the semantic index:
     ```bash
     python ingest/build_qdrant.py
     ```
   - Build the BM25 index:
     ```bash
     python ingest/build_whoosh.py
     ```
4. **Run the API server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Static assets are written under `BackEnd/artifacts/` and exposed at `/artifacts/...` for the front end to consume. 【F:BackEnd/main.py†L39-L482】

### Core API surface

| Endpoint | Method | Purpose |
| -------- | ------ | ------- |
| `/signup`, `/login`, `/logout`, `/forget-password`, `/change-name` | POST/GET | Account lifecycle & credentials.  |
| `/profile`, `/chat/new`, `/chat/{session_id}/messages` | GET/POST | Fetch account info, open sessions, and replay saved conversations. |
| `/chat/{session_id}/message` | POST | Generate a fresh lesson response for the active session.  |
| `/chat/{session_id}/video` | POST | Launch background slide video rendering; poll the response to track progress.  |
| `/normalize`, `/helpful-notes`, `/generate` | POST | Structured RAG pipeline for lesson planning and drafting.  |
| `/gemini/gen_text`, `/gemini/gen_image`, `/gemini/gen_audio` | POST | Thin wrappers around Gemini text, image, and gTTS audio generation. |

## Frontend setup

1. **Install dependencies and configure environment**
   ```bash
   cd FrontEnd
   npm install
   ```
   Create `FrontEnd/.env` (or `.env.local`) with the backend base URL:
   ```env
   VITE_BACKEND_URL=http://localhost:8000/
   ```
   Both the router shell and feature components read this variable to call the API.
2. **Run the development server**
   ```bash
   npm run dev
   ```

### Frontend highlights

- Landing page with responsive hero, feature highlights, and auth modals for signup/login/reset flows. 
- Chat workspace featuring session sidebar management, conversation replay, and streaming AI replies. 
- Markdown + Mermaid-friendly rendering for lesson segments (see `src/components` and `MermaidRenderer.jsx`).

## Media & artifacts

- Generated lesson assets are stored in `BackEnd/artifacts/<run_id>/` with `/diagrams` and `/images` subfolders, along with accessible HTTP URLs added to the lesson payload. 
- Full-motion videos are persisted per session, and narration text is cached on the corresponding `Chat_Session`. 
- Conversation outputs are serialized as pickled lesson drafts in `BackEnd/local_data/` for quick replay. 

## Development tips

- Keep your Gemini quota usage in mind; lesson generation calls the API multiple times per request (normalize, notes, lesson, and optional repairs). 
- When running ingestion on large corpora, monitor memory usage; the scripts flush batches to Qdrant and Whoosh incrementally to avoid overflows. 
- For production deployments, swap the sample SQLite URL with Postgres or another supported backend by adjusting `DB_URL`.

## Useful commands

```bash
# Backend
uvicorn main:app --reload
python ingest/build_qdrant.py
python ingest/build_whoosh.py

# Frontend
npm run dev
npm run build
npm run lint
```

HackTutor provides a comprehensive baseline for AI-assisted tutoring experiences—use this README as a reference when extending the retrieval corpus, fine-tuning Gemini prompts, or enhancing the learner UX.
