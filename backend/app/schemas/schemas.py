from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Developer Schemas
class DeveloperBase(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = None

class DeveloperCreate(DeveloperBase):
    pass

class DeveloperResponse(DeveloperBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    status: str = "active"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repo_url: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Task AI Analysis Schemas
class TaskAIAnalysis(BaseModel):
    summary: str
    difficulty: str
    estimated_hours: float
    required_technologies: List[str]
    suggested_folder_structure: Dict[str, Any]
    suggested_implementation_steps: List[str]
    possible_blockers: List[str]
    best_practices: List[str]
    security_considerations: List[str]
    testing_checklist: List[str]

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: str
    assigned_to: Optional[str] = None
    priority: str = "medium"
    status: str = "todo"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    ai_analysis: Optional[Dict[str, Any]] = None

class TaskResponse(TaskBase):
    id: str
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    assignee: Optional[DeveloperResponse] = None

    class Config:
        from_attributes = True

# Document / RAG Schemas
class DocumentBase(BaseModel):
    project_id: str
    name: str
    file_path: Optional[str] = None
    file_type: str
    content: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Meeting Notes Schemas
class MeetingNotesRequest(BaseModel):
    project_id: str
    title: str
    notes_text: str

class MeetingResponse(BaseModel):
    id: str
    project_id: str
    title: str
    date: datetime
    notes_text: str
    summary: Optional[str] = None
    action_items: Optional[List[str]] = None
    suggested_tasks: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Sprint Report Schemas
class SprintReportRequest(BaseModel):
    project_id: str
    sprint_name: str
    completed_work: Optional[str] = None
    pending_work: Optional[str] = None
    risks: Optional[str] = None
    team_velocity: int = 0

class SprintReportResponse(SprintReportRequest):
    id: str
    recommendations: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Schemas
class ChatRequest(BaseModel):
    project_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    agent_visited: List[str]

# Health Check Schema
class HealthCheckResponse(BaseModel):
    status: str
    database: str
    llm_configured: bool
    version: str
