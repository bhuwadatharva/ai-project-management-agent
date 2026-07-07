from typing import TypedDict, List, Dict, Any, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Conversations
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Context keys
    project_id: str
    session_id: str
    
    # State routing tracking
    next_agent: str
    agent_visited: List[str]
    
    # Gathered intelligence
    kb_context: List[str]
    repo_context: List[str]
    
    # Working structures
    plan: Optional[str]
    suggestions: Optional[str]
    final_response: Optional[str]
