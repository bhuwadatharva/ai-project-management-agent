import json
import os
import re
import uuid
import logging
import tempfile
import shutil
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

from backend.app.db.session import get_db, SessionLocal
from backend.app.db.models import Project, Task, Developer, Document, Meeting, SprintReport, ChatHistory, User, Notification, SystemSetting
from backend.app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    DeveloperCreate, DeveloperResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MeetingNotesRequest, MeetingResponse,
    SprintReportRequest, SprintReportResponse,
    ChatRequest, ChatResponse, HealthCheckResponse,
    DocumentResponse, UserCreate, UserLogin, UserResponse, TokenResponse,
    NotificationResponse, SystemSettingCreate, SystemSettingResponse
)
from backend.app.config.settings import settings
from backend.app.rag.vector_store import add_document_to_store, similarity_search
from backend.app.utils.git_indexer import clone_and_index_repository
from backend.app.utils.doc_loader import load_document
from backend.app.agents.agent_definitions import get_llm, AIMessage
from backend.app.graph.workflow import compiled_graph
from backend.app.utils.auth_helper import hash_password, verify_password, sign_jwt, decode_jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Header

security = HTTPBearer()

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

# --- Authentication Helpers & Dependency ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token or expired session")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- Authentication endpoints ---
@router.post("/auth/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    hashed = hash_password(user_in.password)
    db_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=hashed,
        role=user_in.role or "developer"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/auth/login", response_model=TokenResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    token = sign_jwt({"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/auth/logout")
def logout():
    return {"message": "Successfully logged out"}

# --- Notifications ---
@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(project_id: str, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.project_id == project_id).order_by(Notification.created_at.desc()).all()

@router.post("/notifications", response_model=NotificationResponse)
def create_notification(project_id: str, title: str, message: str, db: Session = Depends(get_db)):
    db_notif = Notification(project_id=project_id, title=title, message=message)
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif

@router.put("/notifications/{notif_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(notif_id: str, db: Session = Depends(get_db)):
    db_notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not db_notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    db_notif.is_read = 1
    db.commit()
    db.refresh(db_notif)
    return db_notif

# --- System Settings ---
@router.get("/settings", response_model=List[SystemSettingResponse])
def get_settings(project_id: str, db: Session = Depends(get_db)):
    return db.query(SystemSetting).filter(SystemSetting.project_id == project_id).all()

@router.post("/settings", response_model=SystemSettingResponse)
def update_or_create_setting(setting_in: SystemSettingCreate, db: Session = Depends(get_db)):
    existing = db.query(SystemSetting).filter(
        SystemSetting.project_id == setting_in.project_id,
        SystemSetting.key == setting_in.key
    ).first()
    
    if existing:
        existing.value = setting_in.value
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_setting = SystemSetting(
            project_id=setting_in.project_id,
            key=setting_in.key,
            value=setting_in.value
        )
        db.add(db_setting)
        db.commit()
        db.refresh(db_setting)
        return db_setting

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

def heuristic_meeting_parser(notes_text: str, developers: list) -> dict:
    sentences = re.split(r'[.!?\n]', notes_text)
    suggested_tasks = []
    action_items = []
    
    keywords = ["implement", "configure", "develop", "design", "connect", "update", "write", "build", "create", "test", "review"]
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 15:
            continue
            
        # Check if sentence has any of our action keywords
        words = sentence.lower().split()
        if any(kw in words for kw in keywords):
            # Clean title
            title = sentence
            if len(title) > 60:
                title = title[:60] + "..."
                
            priority = "High" if any(x in sentence.lower() for x in ["must", "immediately", "critical", "high", "soon"]) else "Medium"
            
            # Simple keyword matching for assignee name/role
            matched_dev_id = None
            matched_dev_name = None
            for dev in developers:
                if (dev.name.lower() in sentence.lower()) or (dev.role.lower() in sentence.lower()):
                    matched_dev_id = dev.id
                    matched_dev_name = dev.name
                    break
                    
            suggested_tasks.append({
                "title": title,
                "description": sentence,
                "priority": priority,
                "assigned_to": str(matched_dev_id) if matched_dev_id else None,
                "assignee": matched_dev_name
            })
            action_items.append(sentence)
            
    if not suggested_tasks:
        suggested_tasks = [
            {
                "title": "Review HMS progression backlog items",
                "description": "Inspect sync transcript for manual task addition.",
                "priority": "Medium",
                "assigned_to": None,
                "assignee": None
            }
        ]
        action_items = ["Review transcript manually."]
        
    return {
        "summary": "Meeting notes parsed via Heuristic Backup Engine (LLM rate-limited).",
        "action_items": action_items[:6],
        "suggested_tasks": suggested_tasks[:6]
    }

# --- Meeting Notes Analysis ---
@router.post("/meetings", response_model=MeetingResponse)
def analyze_meeting_notes(req: MeetingNotesRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Query registered developers to pass to the AI model for capability matching
    developers = db.query(Developer).all()
    devs_text = "\n".join([f"- Name: {d.name}, Role: {d.role}, Email: {d.email}" for d in developers])

    llm = get_llm()
    prompt = f"""You are the Project Manager Agent. Please analyze the following meeting notes and summarize them.
Title: "{req.title}"
Notes content:
"{req.notes_text}"

Available team developers registered in our system:
{devs_text or "No developers registered yet."}

Based on the task requirements, matching technologies, and developer roles/capabilities, suggest the most capable developer to assign each task to by placing their Name or Email in the "assignee" field. If no matching developer is found, set it to null.

Return a JSON block containing the following exact keys:
1. summary (string summary of meeting)
2. action_items (list of strings representing individual action items)
3. suggested_tasks (list of dictionaries representing tasks that should be created, each with "title", "description", "priority", and "assignee" (the name/email of the developer assigned, or null) keys)

Respond ONLY with valid JSON. No markdown code blocks.
"""
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        content = res.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n", "", content)
            content = re.sub(r"\n```$", "", content)
        data = json.loads(content)
        
        # Resolve AI-suggested assignee name/email or perform semantic matching using embeddings
        suggested_tasks = data.get("suggested_tasks", [])
        if suggested_tasks:
            # Always ensure keys are present in JSON response
            for task_dict in suggested_tasks:
                task_dict["assigned_to"] = None
                task_dict["assignee"] = None
                
            if developers:
                try:
                    # Import embedding client helper to get vector embeddings
                    from backend.app.rag.vector_store import get_embeddings_client
                    embedder = get_embeddings_client()
                    
                    # Pre-calculate embeddings for registered developers (e.g. "Name is a Role")
                    dev_texts = [f"{d.name} {d.role}" for d in developers]
                    dev_embs = embedder.embed_documents(dev_texts)
                    
                    for task_dict in suggested_tasks:
                        ai_assignee = task_dict.get("assignee")
                        matched_dev_id = None
                        
                        # 1. Direct match by name/email if specified
                        if ai_assignee:
                            ai_assignee_clean = str(ai_assignee).lower().strip()
                            for dev in developers:
                                if (ai_assignee_clean in dev.name.lower()) or (ai_assignee_clean == dev.email.lower()):
                                    matched_dev_id = dev.id
                                    break
                                    
                        # 2. Semantic match by cosine similarity using text embeddings
                        if not matched_dev_id:
                            task_text = f"{task_dict.get('title', '')} {task_dict.get('description', '')}"
                            task_emb = embedder.embed_query(task_text)
                            
                            best_sim = -1.0
                            best_dev_id = None
                            for dev_idx, dev in enumerate(developers):
                                dev_emb = dev_embs[dev_idx]
                                
                                q_vec = np.array(task_emb)
                                d_vec = np.array(dev_emb)
                                q_norm = np.linalg.norm(q_vec)
                                d_norm = np.linalg.norm(d_vec)
                                
                                if q_norm > 0 and d_norm > 0:
                                    sim = float(np.dot(q_vec, d_vec) / (q_norm * d_norm))
                                    if sim > best_sim:
                                        best_sim = sim
                                        best_dev_id = dev.id
                            
                            # Assign to closest matched developer if one was found
                            if best_sim > -1.0:
                                matched_dev_id = best_dev_id
                                
                        # Update database task structure
                        task_dict["assigned_to"] = str(matched_dev_id) if matched_dev_id else None
                        
                        # Also update/populate the 'assignee' field for the frontend view
                        matched_dev = next((d for d in developers if d.id == matched_dev_id), None)
                        task_dict["assignee"] = matched_dev.name if matched_dev else None
                except Exception as match_err:
                    logger.error(f"Semantic developer mapping failed: {match_err}")
                    # Fallback to simple name matching
                    for task_dict in suggested_tasks:
                        ai_assignee = task_dict.get("assignee")
                        matched_dev_id = None
                        if ai_assignee:
                            ai_assignee_clean = str(ai_assignee).lower().strip()
                            for dev in developers:
                                if (ai_assignee_clean in dev.name.lower()) or (ai_assignee_clean == dev.email.lower()):
                                    matched_dev_id = dev.id
                                    break
                        task_dict["assigned_to"] = str(matched_dev_id) if matched_dev_id else None
    except Exception as e:
        logger.error(f"Failed to analyze meeting notes via LLM (running offline heuristic parsing): {e}")
        data = heuristic_meeting_parser(req.notes_text, developers)

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
