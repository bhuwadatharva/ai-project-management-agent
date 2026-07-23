# DevPilot AI – AI Engineering Project Manager

DevPilot AI is a production-quality engineering project manager co-pilot. It leverages a **LangGraph multi-agent workflow** to perform repository search, source-code analysis, document-based RAG, task planning, code recommendations, automated testing checklists, meeting transcripts action-item parsing, and sprint summaries recommendations.

The front-end has been completely migrated from Streamlit to a modern, premium **React + Vite** SPA.

---

## 1. Project Architecture

The architecture consists of a FastAPI REST server backend and a React (Vite) client frontend.

```mermaid
graph TD
    User([User Request]) --> Supervisor[Supervisor Agent]
    Supervisor -->|Plan & Estimates| Planner[Planner Agent]
    Supervisor -->|Query Git Codebase| Repo[Repository Agent]
    Supervisor -->|Query Knowledge Docs| RAG[RAG Agent]
    Supervisor -->|Draft Code & Tests| Coding[Coding Assistant]
    Supervisor -->|Audit Code & Plans| Reviewer[Reviewer Agent]
    Supervisor -->|Sprint Metrics / Actions| PM[Project Manager Agent]
    
    Planner --> Supervisor
    Repo --> Supervisor
    RAG --> Supervisor
    Coding --> Supervisor
    Reviewer --> Supervisor
    PM --> Supervisor
    
    Supervisor -->|Task Complete| Finish([Compile Final Response])
```

1. **Supervisor Agent**: The orchestrator. Routes to nodes based on user intent and completes execution (`FINISH`).
2. **Planner Agent**: Generates task roadmaps, estimates, and suggested folder structures.
3. **Repository Agent**: Performs vector-based similarity searches on index codebase chunks.
4. **RAG Agent**: Retrieves context from uploaded documentation.
5. **Coding Assistant**: Generates code implementations and test suites.
6. **Reviewer Agent**: Audits generated code for safety, security, and quality.
7. **Project Manager Agent**: Handles tasks updates, meeting transcripts, and sprint summaries.

---

## 2. Environment Variables Guide

Copy `.env.example` to `.env` and configure the following variables:

```bash
# LLM Provider Keys
OPENAI_API_KEY=your-openai-api-key        # Required for OpenAI models
GOOGLE_API_KEY=your-google-api-key        # Required for Gemini models

# Database Config
DATABASE_URL=sqlite:///./devpilot.db      # Fallback to local SQLite if left blank
# For Supabase/PostgreSQL, configure:
# DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Supabase (Optional)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# GitHub Token
GITHUB_TOKEN=github_pat_...               # Optional, for private repository cloning

# Model Configurations
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
```

---

## 3. Database Schema Guide

The database schema supports both SQLite (fallback mode) and PostgreSQL/Supabase (active mode). Enable the `vector` extension in PostgreSQL to enable pgvector.

### Table Definitions
1. **`users`**: Manages secure user registry.
2. **`developers`**: Stores team members' roles and names.
3. **`projects`**: Manages project workspaces.
4. **`tasks`**: Tracks status, priorities, and generated AI architecture analyses.
5. **`documents`**: Ingests document and codebase text chunks with vector embeddings.
6. **`meetings`**: Captures summaries and extracted action items.
7. **`sprint_reports`**: Compiles metrics and recommendations.
8. **`chat_history`**: Persists conversation context.
9. **`notifications`**: Holds unread notifications.
10. **`system_settings`**: Stores configuration key-value pairs.

SQL initialization commands are available in [db_schema.sql](file:///d:/Website/aiagentprac/db_schema.sql).

---

## 4. Installation & Run Guide

### Installation
1. Clone the repository.
2. Make sure Python 3.12+ and Node.js are installed.
3. Install backend dependencies using python/pip:
   ```bash
   pip install -r backend/pyproject.toml # or use uv
   ```
4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running Locally
1. **Verify setup**:
   ```bash
   python verify_setup.py
   ```
2. **Start Backend**:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   * REST Swagger docs are live at `https://ai-project-management-agent-7y2e.onrender.com/docs`.
3. **Start React Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   * Frontend will open at `http://localhost:5173`.

---

## 5. API Documentation

### Authentication
* `POST /api/auth/signup` - Registers a new user.
* `POST /api/auth/login` - Signs in a user and returns a token.
* `POST /api/auth/logout` - Logs out a user session.

### Tasks
* `GET /api/tasks?project_id={id}` - Retrieve tasks.
* `POST /api/tasks` - Create a task and dynamically run AI analysis.
* `PUT /api/tasks/{task_id}` - Update status or priority.
* `DELETE /api/tasks/{task_id}` - Delete a task.

### Repository Search & Upload
* `POST /api/repository/index` - Clone and index git repository.
* `GET /api/repository/query` - Semantic code vector search.
* `POST /api/kb/upload` - Upload PDF, Docx, MD, or TXT documents.

### Chat & Copilot
* `POST /api/chat` - Route chat query through LangGraph workflow.

### Sprints & Meetings
* `POST /api/meetings` - Extract action items from notes.
* `POST /api/sprint/report` - Generate sprint recommendations.

### Notifications & Settings
* `GET /api/notifications` - Retrieve unread notifications.
* `PUT /api/notifications/{id}/read` - Mark notification as read.
* `POST /api/settings` - Create or update project key-value settings.

---

## 6. Testing & Deployment Guide

### Testing
* Run `python verify_setup.py` to run automated connection and graph compilation tests.
* Build the React frontend with `npm run build` to ensure there are no compilation warnings or errors.

### Deployment
* **Database**: Set up a PostgreSQL database on Supabase. Copy `db_schema.sql` into the SQL Editor, execute it, and update `DATABASE_URL` in your env.
* **Backend**: Deploy the FastAPI server to Render, Heroku, or AWS ECS. Configure env vars.
* **Frontend**: Deploy the React build outputs to Vercel, Netlify, or AWS S3.

---

## 7. Known Issues & Fallbacks
* **No external LLM key**: If no `GOOGLE_API_KEY` or `OPENAI_API_KEY` is configured, the application falls back to a deterministic Mock LLM. The AI agents will mock responses based on query intents.
* **Supabase database unavailable**: The system automatically redirects queries to the local SQLite database (`devpilot.db`) to ensure the application remains fully functional offline.

---

## 8. Final Feature Checklist
- [x] JWT Token Verification & User Auth
- [x] Multi-Agent Orchestrator (LangGraph)
- [x] Vector Database Search & Chunk Fallbacks
- [x] Project Backlog Task CRUD
- [x] Meeting action items extraction
- [x] Sprint velocity recommendations
- [x] File Upload & PDF/DOCX Parsing
- [x] Real-time Notifications & Settings
