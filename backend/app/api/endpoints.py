import json
import os
import re
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

from backend.app.db.session import get_db
from backend.app.db.models import Project, Task, Developer, Document, Meeting, SprintReport, ChatHistory
from backend.app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    DeveloperCreate, DeveloperResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingNotesRequest, MeetingResponse,
    SprintReportRequest, SprintReportResponse,
    ChatRequest, ChatResponse, HealthCheckResponse,
    DocumentResponse
)
from backend.app.config.settings import settings
from backend.app.rag.vector_store import add_document_to_store, similarity_search
from backend.app.utils.git_indexer import clone_and_index_repository
from backend.app.utils.doc_loader import load_document
from backend.app.agents.agent_definitions import get_llm, AIMessage
from backend.app.graph.workflow import compiled_graph

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper for AI Task Analysis
def generate_ai_task_analysis(title: str, description: str) -> Dict[str, Any]:
    llm = get_llm()
    prompt = f"""You are an expert AI Software Architect. Analyze the following task:
Title: "{title}"
Description: "{description or 'No description provided.'}"

Generate a detailed task analysis containing the following fields:
1. summary (string)
2. difficulty (string: Easy, Medium, Hard, or Expert)
3. estimated_hours (float)
4. required_technologies (list of strings)
5. suggested_folder_structure (nested dictionary of directories/files, e.g. {{"src": {{"api": ["auth.py"]}}}})
6. suggested_implementation_steps (list of strings)
7. possible_blockers (list of strings)
8. best_practices (list of strings)
9. security_considerations (list of strings)
10. testing_checklist (list of strings)

Respond ONLY with a valid JSON block containing these exact keys. Do not include markdown code block symbols like ```json or ```. Just raw JSON.
"""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate task analysis dynamically: {e}")
        return {
            "summary": description or title,
            "difficulty": "Medium",
            "estimated_hours": 4.0,
            "required_technologies": ["Python"],
            "suggested_folder_structure": {"app": ["main.py"]},
            "suggested_implementation_steps": [
                "Understand the core task logic",
                "Implement basic structure and testing",
                "Integrate with main branch"
            ],
            "possible_blockers": ["Lack of API specifications"],
            "best_practices": ["Keep code modular", "Add types"],
            "security_considerations": ["Validate inputs", "Avoid hardcoding credentials"],
            "testing_checklist": ["Run basic unit tests"]
        }

# --- Health Check ---
@router.get("/health", response_model=HealthCheckResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1") if not settings.DATABASE_URL.startswith("sqlite") else text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    llm_configured = settings.OPENAI_API_KEY is not None or settings.GOOGLE_API_KEY is not None
    
    return {
        "status": "up",
        "database": db_status,
        "llm_configured": llm_configured,
        "version": "1.0.0"
    }

from sqlalchemy import text

# --- Authentication Placeholder ---
@router.post("/auth/login")
def login_placeholder():
    return {
        "access_token": "devpilot-token-placeholder",
        "token_type": "bearer",
        "user": {"email": "admin@devpilot.ai", "role": "lead_engineer"}
    }

# --- Projects ---
@router.get("/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(
        name=project.name,
        description=project.description,
        repo_url=project.repo_url,
        status=project.status
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

# --- Developers ---
@router.get("/developers", response_model=List[DeveloperResponse])
def get_developers(db: Session = Depends(get_db)):
    return db.query(Developer).all()

@router.post("/developers", response_model=DeveloperResponse)
def create_developer(dev: DeveloperCreate, db: Session = Depends(get_db)):
    db_dev = Developer(name=dev.name, email=dev.email, role=dev.role)
    db.add(db_dev)
    db.commit()
    db.refresh(db_dev)
    return db_dev

# --- Tasks ---
@router.get("/tasks", response_model=List[TaskResponse])
def get_tasks(project_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    return query.all()

@router.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate AI analysis
    ai_analysis = generate_ai_task_analysis(task.title, task.description)

    db_task = Task(
        title=task.title,
        description=task.description,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        priority=task.priority,
        status=task.status,
        ai_analysis=ai_analysis
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    for var, value in vars(task_update).items():
        if value is not None:
            setattr(db_task, var, value)
            
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": f"Task {task_id} successfully deleted"}

# --- Repository Indexing & Queries ---
@router.post("/repository/index")
def index_repo(project_id: str, repo_path_or_url: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Save path/url in project
    project.repo_url = repo_path_or_url
    db.commit()

    # Index in background to avoid client timeout
    def index_task():
        db_session = SessionLocal()
        try:
            clone_and_index_repository(db_session, project_id, repo_path_or_url)
        finally:
            db_session.close()

    background_tasks.add_task(index_task)
    return {"status": "indexing_scheduled", "message": f"Indexing started in the background for project {project_id}."}

@router.get("/repository/query")
def query_repo(project_id: str, query: str, db: Session = Depends(get_db)):
    results = similarity_search(db, project_id, query, limit=5)
    return [{"file": r[0]["file_path"], "name": r[0]["name"], "similarity": r[1], "content_preview": r[0]["content"][:300]} for r in results]

# --- Knowledge Base Uplink ---
@router.post("/kb/upload", response_model=DocumentResponse)
async def upload_kb_document(
    project_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Write temporarily to load content
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        content = load_document(file_path)
        file_ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
        
        # Save to DB Vector Store
        add_document_to_store(
            db=db,
            project_id=project_id,
            name=file.filename,
            file_path=file.filename,
            file_type=file_ext,
            content=content
        )
        
        # Return a metadata DB model row reference
        doc_record = db.query(Document).filter(Document.project_id == project_id, Document.file_path == file.filename).first()
        return doc_record
        
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# --- Co-Pilot Chat Orchestrator (LangGraph Multi-Agent Trigger) ---
@router.post("/chat", response_model=ChatResponse)
def start_copilot_chat(chat_req: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == chat_req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Retrieve past chat history from DB
    past_chats = db.query(ChatHistory).filter(
        ChatHistory.project_id == chat_req.project_id,
        ChatHistory.session_id == chat_req.session_id
    ).order_by(ChatHistory.created_at.asc()).all()
    
    # Format messages for LangGraph input
    messages = []
    for past_chat in past_chats:
        if past_chat.role == "user":
            messages.append(HumanMessage(content=past_chat.content))
        elif past_chat.role == "assistant":
            messages.append(AIMessage(content=past_chat.content))
            
    # Add new user message
    messages.append(HumanMessage(content=chat_req.message))
    
    # Initialize graph state
    initial_state = {
        "messages": messages,
        "project_id": chat_req.project_id,
        "session_id": chat_req.session_id,
        "next_agent": "supervisor",
        "agent_visited": [],
        "kb_context": [],
        "repo_context": [],
        "plan": None,
        "suggestions": None,
        "final_response": None
    }
    
    try:
        # Execute workflow
        final_state = compiled_graph.invoke(initial_state)
        response_text = final_state.get("final_response") or "The query was processed, but no final response text was compiled."
        
        # Save user and assistant messages in chat history database
        db_user_msg = ChatHistory(
            project_id=chat_req.project_id,
            session_id=chat_req.session_id,
            role="user",
            content=chat_req.message
        )
        db_assistant_msg = ChatHistory(
            project_id=chat_req.project_id,
            session_id=chat_req.session_id,
            role="assistant",
            content=response_text
        )
        db.add(db_user_msg)
        db.add(db_assistant_msg)
        db.commit()
        
        return {
            "response": response_text,
            "agent_visited": final_state.get("agent_visited", [])
        }
    except Exception as e:
        logger.error(f"LangGraph execution failure: {e}")
        raise HTTPException(status_code=500, detail=f"AI Agent workflow encountered an error: {str(e)}")

# --- Meeting Notes Analysis ---
@router.post("/meetings", response_model=MeetingResponse)
def analyze_meeting_notes(req: MeetingNotesRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    llm = get_llm()
    prompt = f"""You are the Project Manager Agent. Please analyze the following meeting notes and summarize them.
Title: "{req.title}"
Notes content:
"{req.notes_text}"

Return a JSON block containing the following exact keys:
1. summary (string summary of meeting)
2. action_items (list of strings representing individual action items)
3. suggested_tasks (list of dictionaries representing tasks that should be created, each with "title", "description", "priority" keys)

Respond ONLY with valid JSON. No markdown code blocks.
"""
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        content = res.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
        data = json.loads(content)
    except Exception as e:
        logger.error(f"Failed to analyze meeting notes: {e}")
        data = {
            "summary": "Meeting notes captured.",
            "action_items": ["Review captured transcript manually."],
            "suggested_tasks": []
        }

    db_meeting = Meeting(
        project_id=req.project_id,
        title=req.title,
        notes_text=req.notes_text,
        summary=data.get("summary"),
        action_items=data.get("action_items"),
        suggested_tasks=data.get("suggested_tasks")
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

# --- Sprint Report Summarizer ---
@router.post("/sprint/report", response_model=SprintReportResponse)
def generate_sprint_report(req: SprintReportRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    tasks = db.query(Task).filter(Task.project_id == req.project_id).all()
    todo_tasks = [t.title for t in tasks if t.status == "todo"]
    in_progress_tasks = [t.title for t in tasks if t.status == "in_progress"]
    review_tasks = [t.title for t in tasks if t.status == "review"]
    done_tasks = [t.title for t in tasks if t.status == "done"]
    
    llm = get_llm()
    prompt = f"""You are the Project Manager Agent. Make recommendations for the current sprint.
Project Name: {project.name}
Sprint Name: {req.sprint_name}

Tasks Status Dashboard:
- Completed Tasks: {done_tasks}
- Under Review: {review_tasks}
- In Progress: {in_progress_tasks}
- Backlog/Todo: {todo_tasks}

Completed Work description provided by user: "{req.completed_work or 'None'}"
Pending Work description provided by user: "{req.pending_work or 'None'}"
Risks highlighted by user: "{req.risks or 'None'}"
Velocity: {req.team_velocity} Story Points

Synthesize strategic AI recommendations, sprint risks, and suggestions to speed up delivery. Keep recommendations bulleted.
"""
    
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        recommendations = res.content
    except Exception as e:
        logger.error(f"Sprint reports LLM summary failed: {e}")
        recommendations = "Ensure resources are balanced and backlogs are updated."
        
    db_report = SprintReport(
        project_id=req.project_id,
        sprint_name=req.sprint_name,
        completed_work=req.completed_work,
        pending_work=req.pending_work,
        risks=req.risks,
        team_velocity=req.team_velocity,
        recommendations=recommendations
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report
