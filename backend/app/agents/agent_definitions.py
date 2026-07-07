import json
import re
import logging
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from backend.app.config.settings import settings
from backend.app.agents.graph_state import AgentState
from backend.app.db.session import SessionLocal
from backend.app.rag.vector_store import similarity_search

logger = logging.getLogger(__name__)

# Dynamic LLM Provider selection
def get_llm():
    if settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0.1
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Google GenAI model: {e}")

    if settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.CHAT_MODEL or "gpt-4o-mini",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.1
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI model: {e}")

    # Mock LLM for local sandbox
    class MockLLM:
        def invoke(self, messages):
            last_msg = messages[-1].content if messages else ""
            
            # Simple heuristic mock responses based on message intent
            if "jwt" in last_msg.lower():
                content = """[Simulated AI Assistant Response]
### Required Backend Files:
- `backend/app/api/auth.py` (endpoints)
- `backend/app/utils/security.py` (JWT helper)

### Suggested Libraries:
- PyJWT, passlib, bcrypt

### Step-by-Step Roadmap:
1. Create user register/login endpoints.
2. Generate JWT token with HS256 algorithm.
3. Add security schemes to verify headers.
"""
            elif "sprint" in last_msg.lower():
                content = """[Simulated Sprint Report]
### Completed Work:
- Auth backend modules completed and tested.
### Pending Work:
- Frontend UI dashboard integration.
### Velocity:
- 15 Story Points.
"""
            else:
                content = f"[Simulated response for: '{last_msg[:100]}']\n- The repository files look clean.\n- Ready to add implementation steps.\n- Best practice: Keep endpoints modular."
                
            return AIMessage(content=content)
            
    logger.warning("No Google or OpenAI API Key detected. Using mock chat client.")
    return MockLLM()

llm = get_llm()

# --- Supervisor Agent ---
def supervisor_agent(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor Agent evaluates user input and decides the next routing node.
    Returns: Updated routing destination in state['next_agent'].
    """
    logger.info("Supervisor Agent routing step.")
    
    last_message = state["messages"][-1].content if state["messages"] else ""
    history = state.get("agent_visited", [])
    
    # Retrieve current accumulated state to give LLM context on what has been done
    plan = state.get("plan")
    suggestions = state.get("suggestions")
    kb_context = state.get("kb_context", [])
    repo_context = state.get("repo_context", [])
    final_response = state.get("final_response")
    
    # Base heuristic if LLM is mock or fails structured formatting
    prompt = f"""You are the Supervisor Agent for DevPilot AI.
Given the user query, the agents already visited, and the current accumulated state of plans, suggestions, or contexts, decide which agent should run next.

Visited history: {history}
Active Plan in State: {plan or 'None'}
Active Coding Suggestions in State: {suggestions or 'None'}
Has KB Context: {'Yes' if kb_context else 'No'}
Has Repo Context: {'Yes' if repo_context else 'No'}
Active Final Response in State: {final_response or 'None'}

User query: "{last_message}"

You must respond with exactly ONE of the following routing words based on needs:
- PLANNER: If you need to plan steps, create folder structures, or outline a roadmap.
- REPO: If the user is asking about code files, directory structures, or code logic inside the project repository.
- RAG: If the user is asking about uploaded documentation files (PDF, DOCX, Markdown, TXT).
- CODING: If you need to write, refactor, explain, or generate unit tests for code.
- REVIEWER: If code/plans have been generated and you need a security and quality inspection before returning.
- PM: If the user asks for sprint velocity/reports, task CRUD status, or meeting action items extraction.
- FINISH: If the user's query is already fully answered, or the generated coding/planning outputs are ready to be returned.

Rules:
1. Do not repeat agents endlessly. If an agent has already run and solved the requirement, route to FINISH.
2. Always route to REVIEWER after CODING or PLANNER to verify findings before finishing.
3. If this is the start of a task analysis or feature implementation request, route to PLANNER first.

Response:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    res_text = response.content.strip().upper()
    
    # Parse routing keyword
    next_step = "FINISH"
    for word in ["PLANNER", "REPO", "RAG", "CODING", "REVIEWER", "PM", "FINISH"]:
        if word in res_text:
            next_step = word
            break
            
    # Guard loop repetition using case-insensitive check
    history_upper = [h.upper() for h in history]
    if next_step in history_upper:
         logger.info(f"Loop protection triggered: {next_step} already visited in {history_upper}. Routing to FINISH.")
         next_step = "FINISH"
         
    visited = list(history)
    visited.append("Supervisor")
    
    # Auto-compile final response if finishing without Reviewer
    ret_response = final_response
    if next_step == "FINISH" and not ret_response:
        parts = []
        if plan:
            parts.append(f"### Proposed Plan:\n{plan}")
        if suggestions:
            parts.append(f"### Coding Suggestions:\n{suggestions}")
        if parts:
            ret_response = "\n\n".join(parts)
        else:
            ret_response = "I have reviewed your query and completed the analysis."
    
    return {
        "next_agent": next_step,
        "agent_visited": visited,
        "final_response": ret_response
    }

# --- Planner Agent ---
def planner_agent(state: AgentState) -> Dict[str, Any]:
    """
    Planner Agent creates execution blueprints, estimated times, and structural plans.
    """
    logger.info("Planner Agent generating implementation roadmap.")
    last_message = state["messages"][-1].content if state["messages"] else ""
    
    prompt = f"""You are the Planner Agent. Create a software roadmap.
User task/request: "{last_message}"

Format your response with the following sections:
1. Task Summary
2. Difficulty & Estimated Hours
3. Required Technologies
4. Suggested Folder Structure
5. Step-by-Step Implementation Roadmap
6. Potential Blockers
"""
    
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("Planner")
    
    return {
        "plan": res.content,
        "agent_visited": visited
    }

# --- Repository Agent ---
def repository_agent(state: AgentState) -> Dict[str, Any]:
    """
    Repository Agent searches database code files and explains structure.
    """
    logger.info("Repository Agent analyzing workspace structure.")
    last_message = state["messages"][-1].content if state["messages"] else ""
    project_id = state.get("project_id")
    
    context_str = ""
    # Retrieve repository code chunks from DB
    if project_id:
        db = SessionLocal()
        try:
            similar_chunks = similarity_search(db, project_id, last_message, limit=5)
            # Filter only code files
            code_chunks = [c for c, score in similar_chunks if c.get("file_type") == "code"]
            if code_chunks:
                context_str = "\n\n".join([f"File: {c['file_path']}\nContent:\n{c['content'][:1200]}" for c in code_chunks])
        finally:
            db.close()
            
    prompt = f"""You are the Repository Agent.
Answer questions about the codebase based on the matched repository files provided.

Matching repository contents:
{context_str or "No matching codebase files found in the index."}

User Question: "{last_message}"

Provide a detailed response detailing file locations, affected APIs, and structural explanations.
"""
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("Repository")
    
    return {
        "repo_context": [context_str] if context_str else [],
        "final_response": res.content,
        "agent_visited": visited
    }

# --- RAG Agent ---
def rag_agent(state: AgentState) -> Dict[str, Any]:
    """
    RAG Agent retrieves data from uploaded knowledge base files.
    """
    logger.info("RAG Agent fetching knowledge base documents.")
    last_message = state["messages"][-1].content if state["messages"] else ""
    project_id = state.get("project_id")
    
    context_str = ""
    if project_id:
        db = SessionLocal()
        try:
            similar_chunks = similarity_search(db, project_id, last_message, limit=5)
            # Filter out non-code docs
            kb_chunks = [c for c, score in similar_chunks if c.get("file_type") != "code"]
            if kb_chunks:
                context_str = "\n\n".join([f"Doc: {c['name']} (Path: {c['file_path']})\nContent:\n{c['content'][:1200]}" for c in kb_chunks])
        finally:
            db.close()
            
    prompt = f"""You are the RAG Agent.
Answer the user's question using only the uploaded knowledge base materials provided below.

Knowledge Base Context:
{context_str or "No matching documentation found."}

User Question: "{last_message}"
"""
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("RAG")
    
    return {
        "kb_context": [context_str] if context_str else [],
        "final_response": res.content,
        "agent_visited": visited
    }

# --- Coding Assistant Agent ---
def coding_assistant_agent(state: AgentState) -> Dict[str, Any]:
    """
    Coding Assistant generates code templates, functions, unit tests, or bug fixes.
    """
    logger.info("Coding Assistant drafting source code modules.")
    last_message = state["messages"][-1].content if state["messages"] else ""
    plan = state.get("plan", "")
    repo_context = "\n".join(state.get("repo_context", []))
    
    prompt = f"""You are the Coding Assistant Agent.
Write the required code templates, implementations, or unit tests based on the user's request and context.

Active plan:
{plan}

Repository reference context:
{repo_context}

User Coding Request: "{last_message}"

Generate complete, commented code snippets matching pythonic or project standards.
"""
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("Coding")
    
    return {
        "suggestions": res.content,
        "agent_visited": visited
    }

# --- Reviewer Agent ---
def reviewer_agent(state: AgentState) -> Dict[str, Any]:
    """
    Reviewer Agent inspects plans or code templates for performance and security issues.
    """
    logger.info("Reviewer Agent conducting quality inspection.")
    plan = state.get("plan", "")
    suggestions = state.get("suggestions", "")
    
    prompt = f"""You are the Reviewer Agent.
Please review the generated implementation plan and/or coding suggestions for potential security gaps, performance bugs, and best practice improvements.

Generated Plan:
{plan}

Generated Code Suggestions:
{suggestions}

Suggest precise modifications, security upgrades, and testing recommendations.
"""
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("Reviewer")
    
    return {
        "final_response": f"### Code & Plan Review:\n{res.content}\n\n### Original Suggestions:\n{suggestions or plan}",
        "agent_visited": visited
    }

# --- Project Manager Agent ---
def project_manager_agent(state: AgentState) -> Dict[str, Any]:
    """
    Project Manager Agent handles tasks scheduling, sprints, and meeting transcript analysis.
    """
    logger.info("Project Manager Agent analyzing workflow items.")
    last_message = state["messages"][-1].content if state["messages"] else ""
    
    prompt = f"""You are the Project Manager Agent.
Analyze tasks, sprint metrics, or meeting notes based on the request.
Request: "{last_message}"

Provide a clean summary containing action items, owners, suggested task updates, or velocity recommendations.
"""
    res = llm.invoke([HumanMessage(content=prompt)])
    visited = list(state.get("agent_visited", []))
    visited.append("PM")
    
    return {
        "final_response": res.content,
        "agent_visited": visited
    }
