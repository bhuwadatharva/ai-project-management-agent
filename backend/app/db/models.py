import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.types import UserDefinedType
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class SQLiteVector(UserDefinedType):
    def get_col_spec(self, **kw):
        return "TEXT"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            import json
            return json.dumps(value)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            import json
            if isinstance(value, str):
                return json.loads(value)
            return value
        return process

def get_vector_type(dim=None):
    try:
        from pgvector.sqlalchemy import Vector
        return Vector(dim)
    except ImportError:
        return SQLiteVector()

class Developer(Base):
    __tablename__ = "developers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tasks = relationship("Task", back_populates="assignee")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    repo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), default="active", nullable=False)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="project", cascade="all, delete-orphan")
    sprint_reports = relationship("SprintReport", back_populates="project", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="project", cascade="all, delete-orphan")
    settings = relationship("SystemSetting", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("developers.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(50), default="medium", nullable=False) # low, medium, high, critical
    status = Column(String(50), default="todo", nullable=False) # todo, in_progress, review, done
    ai_analysis = Column(JSON, nullable=True) # Stores analysis dictionary
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Developer", back_populates="tasks")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=False) # pdf, docx, md, txt, code
    content = Column(Text, nullable=False)
    embedding = Column(get_vector_type(1536), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="documents")

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    notes_text = Column(Text, nullable=False)
    summary = Column(Text)
    action_items = Column(JSON) # List of action items
    suggested_tasks = Column(JSON) # List of suggested task dicts
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="meetings")

class SprintReport(Base):
    __tablename__ = "sprint_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprint_name = Column(String(255), nullable=False)
    completed_work = Column(Text)
    pending_work = Column(Text)
    risks = Column(Text)
    team_velocity = Column(Integer, default=0, nullable=False)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="sprint_reports")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="chat_histories")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(100), default="developer")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="notifications")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)

    project = relationship("Project", back_populates="settings")
