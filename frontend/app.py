import streamlit as st
import httpx
import json
import os
from typing import Dict, Any, List

# API Server URL
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

# Configure Page
st.set_page_config(
    page_title="DevPilot AI - Engineering Project Manager",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Dark Mode)
st.markdown("""
<style>
    /* Premium font and styling */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #9ca3af;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* KPI Card styling */
    .metric-card {
        background-color: #1e1b4b;
        border: 1px solid #312e81;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f43f5e;
        margin-bottom: 0.2rem;
    }
    .metric-val-green {
        font-size: 2.2rem;
        font-weight: 700;
        color: #10b981;
        margin-bottom: 0.2rem;
    }
    .metric-val-purple {
        font-size: 2.2rem;
        font-weight: 700;
        color: #8b5cf6;
        margin-bottom: 0.2rem;
    }
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9ca3af;
    }
    
    /* Code segment display */
    .code-box {
        background-color: #0f172a;
        color: #f1f5f9;
        font-family: 'Courier New', Courier, monospace;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #334155;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to query backend REST client
def make_request(method: str, path: str, **kwargs) -> Any:
    url = f"{API_URL}{path}"
    try:
        with httpx.Client(timeout=60.0) as client:
            if method == "GET":
                response = client.get(url, **kwargs)
            elif method == "POST":
                response = client.post(url, **kwargs)
            elif method == "PUT":
                response = client.put(url, **kwargs)
            elif method == "DELETE":
                response = client.delete(url, **kwargs)
            else:
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                st.sidebar.error(f"Error {response.status_code}: {response.text}")
                return None
    except Exception as e:
        st.sidebar.error(f"Failed to connect to backend: {e}")
        return None

# --- SIDEBAR: Project Selector & Setup ---
st.sidebar.image("https://img.icons8.com/nolan/96/airplane-take-off.png", width=64)
st.sidebar.markdown("### DevPilot AI Control Panel")

# Load existing projects
projects = make_request("GET", "/projects") or []

if not projects:
    # Setup mock/starter project
    st.sidebar.info("Creating a default starter project...")
    starter = make_request("POST", "/projects", json={"name": "Auth Integration MVP", "description": "JWT-based authentication flow"})
    if starter:
        projects = [starter]

project_names = {p["name"]: p["id"] for p in projects}
selected_proj_name = st.sidebar.selectbox("Active Workspace Project", list(project_names.keys()) if project_names else ["No Projects Available"])

# Global session project ID
active_project_id = project_names.get(selected_proj_name)

# Create new project modal
with st.sidebar.expander("➕ Create New Project"):
    new_name = st.text_input("Project Name")
    new_desc = st.text_area("Description")
    new_repo = st.text_input("Git URL or Local Folder Path (Optional)")
    if st.button("Initialize Project"):
        if new_name:
            payload = {"name": new_name, "description": new_desc, "repo_url": new_repo}
            new_proj = make_request("POST", "/projects", json=payload)
            if new_proj:
                st.success(f"Project '{new_name}' created!")
                st.rerun()
        else:
            st.error("Project Name is required.")

# Manage Developers
with st.sidebar.expander("👥 Register Team Developer"):
    dev_name = st.text_input("Developer Name")
    dev_email = st.text_input("Developer Email")
    dev_role = st.selectbox("Role", ["Frontend Developer", "Backend Developer", "DevOps Engineer", "QA Tester", "Architect"])
    if st.button("Add Team Member"):
        if dev_name and dev_email:
            payload = {"name": dev_name, "email": dev_email, "role": dev_role}
            new_dev = make_request("POST", "/developers", json=payload)
            if new_dev:
                st.success(f"Registered {dev_name}!")
                st.rerun()

# Load developers
developers = make_request("GET", "/developers") or []
dev_names = {d["name"]: d["id"] for d in developers}

# --- HEADER SECTION ---
st.markdown(f"<div class='main-title'>DevPilot AI</div>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>AI-Powered Engineering Project Manager / Workspace: <b>{selected_proj_name}</b></div>", unsafe_allow_html=True)

if not active_project_id:
    st.warning("Please create or select an active project in the sidebar to load details.")
    st.stop()

# Load tasks for selected project
tasks = make_request("GET", f"/tasks?project_id={active_project_id}") or []

# Create Tabs
tabs = st.tabs(["📊 Dashboard", "📋 Task Board", "📁 Git & Knowledge Base", "💬 Agent Co-Pilot", "📝 Sprints & Meetings"])

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.markdown("### Project Dashboard Overview")
    
    # Calculate stats
    total_t = len(tasks)
    todo_t = sum(1 for t in tasks if t["status"] == "todo")
    prog_t = sum(1 for t in tasks if t["status"] == "in_progress")
    rev_t = sum(1 for t in tasks if t["status"] == "review")
    done_t = sum(1 for t in tasks if t["status"] == "done")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{total_t}</div>
            <div class="metric-label">Total Backlog Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val-purple">{prog_t} / {rev_t}</div>
            <div class="metric-label">In Progress / Review</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val-green">{done_t}</div>
            <div class="metric-label">Completed Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-val">{todo_t}</div>
            <div class="metric-label">Pending Backlog</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    st.markdown("### AI Suggestions & General Recommendations")
    # Call Supervisor/PM to get automated suggestions for the general project layout
    if st.button("Generate AI Project Suggestions"):
        with st.spinner("AI Agents analyzing project status..."):
            chat_payload = {
                "project_id": active_project_id,
                "session_id": "dashboard_analytics",
                "message": "Analyze my project status and tasks list. Give 4 strategic bullet point suggestions for improvement based on pending items."
            }
            res = make_request("POST", "/chat", json=chat_payload)
            if res:
                st.info(res["response"])
                st.caption(f"Visited Trace: {' ➔ '.join(res['agent_visited'])}")

# --- TAB 2: TASK BOARD & CRUD ---
with tabs[1]:
    st.markdown("### Task backlog Management")
    
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("#### Create New Task")
        t_title = st.text_input("Task Title", placeholder="e.g. Implement OAuth Flow")
        t_desc = st.text_area("Task Description")
        t_priority = st.selectbox("Priority", ["low", "medium", "high", "critical"], index=1)
        
        assigned_name = st.selectbox("Assignee", ["Unassigned"] + list(dev_names.keys()))
        t_assignee_id = dev_names.get(assigned_name)
        
        if st.button("Create Task & Run AI Analysis"):
            if t_title:
                payload = {
                    "title": t_title,
                    "description": t_desc,
                    "project_id": active_project_id,
                    "assigned_to": t_assignee_id,
                    "priority": t_priority,
                    "status": "todo"
                }
                with st.spinner("Analyzing requirements & compiling folder patterns with AI..."):
                    new_task = make_request("POST", "/tasks", json=payload)
                    if new_task:
                        st.success(f"Task '{t_title}' created successfully!")
                        st.rerun()
            else:
                st.error("Task Title is required")
                
    with col_right:
        st.markdown("#### Task Backlog and AI Analysis Outputs")
        if not tasks:
            st.warning("No tasks created yet.")
        else:
            for task in tasks:
                assignee_display = task['assignee']['name'] if task.get('assignee') else "Unassigned"
                priority_color = {
                    "low": "🔵", "medium": "🟢", "high": "🟡", "critical": "🔴"
                }.get(task["priority"], "⚪")
                
                with st.expander(f"{priority_color} [{task['status'].upper()}] {task['title']} — Assignee: {assignee_display}"):
                    st.markdown(f"**Description:** {task['description'] or 'No description provided.'}")
                    
                    # AI Analysis display
                    analysis = task.get("ai_analysis")
                    if analysis:
                        st.markdown("#### 🤖 AI Architecture Analysis")
                        st.markdown(f"**Estimated Time:** {analysis.get('estimated_hours', 4)} hours | **Difficulty:** {analysis.get('difficulty', 'Medium')}")
                        st.markdown(f"**Required Tech:** {', '.join(analysis.get('required_technologies', []))}")
                        
                        col_an1, col_an2 = st.columns(2)
                        with col_an1:
                            st.markdown("**Roadmap / Steps:**")
                            for step in analysis.get("suggested_implementation_steps", []):
                                st.markdown(f"- {step}")
                                
                            st.markdown("**Suggested Folder Structure:**")
                            st.json(analysis.get("suggested_folder_structure", {}))
                            
                        with col_an2:
                            st.markdown("**Security Considerations:**")
                            for sec in analysis.get("security_considerations", []):
                                st.markdown(f"- {sec}")
                                
                            st.markdown("**Testing Checklist:**")
                            for test in analysis.get("testing_checklist", []):
                                st.markdown(f"- {test}")
                                
                    # Change Status / Priority Form
                    col_act1, col_act2, col_act3 = st.columns(3)
                    with col_act1:
                        new_status = st.selectbox(
                            "Update Status", 
                            ["todo", "in_progress", "review", "done"], 
                            index=["todo", "in_progress", "review", "done"].index(task["status"]),
                            key=f"status_{task['id']}"
                        )
                    with col_act2:
                        new_prio = st.selectbox(
                            "Update Priority",
                            ["low", "medium", "high", "critical"],
                            index=["low", "medium", "high", "critical"].index(task["priority"]),
                            key=f"prio_{task['id']}"
                        )
                    with col_act3:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Apply Changes", key=f"apply_{task['id']}"):
                            update_payload = {"status": new_status, "priority": new_prio}
                            make_request("PUT", f"/tasks/{task['id']}", json=update_payload)
                            st.rerun()
                            
                    if st.button("🗑️ Delete Task", key=f"del_{task['id']}"):
                        make_request("DELETE", f"/tasks/{task['id']}")
                        st.rerun()

# --- TAB 3: REPOS & KB ---
with tabs[2]:
    st.markdown("### Repository Indexer & Knowledge Base RAG")
    
    col_kb1, col_kb2 = st.columns(2)
    
    with col_kb1:
        st.markdown("#### Index Git Repository")
        repo_url_input = st.text_input(
            "Git URL or Local Folder Directory path", 
            placeholder="https://github.com/octocat/Spoon-Knife or D:/my-project",
            value=projects[0]["repo_url"] if projects else ""
        )
        if st.button("Connect & Index Repository"):
            if repo_url_input:
                res = make_request("POST", f"/repository/index?project_id={active_project_id}&repo_path_or_url={repo_url_input}")
                if res:
                    st.success("Indexing task scheduled in the background successfully.")
            else:
                st.error("Please enter a valid Git URL or local folder path")
                
        st.markdown("---")
        st.markdown("#### Query Repository & Code Files")
        repo_q = st.text_input("Semantic Code / File Search Query", placeholder="Where should I implement OAuth token checks?")
        if st.button("Search Code"):
            if repo_q:
                with st.spinner("Searching repository structure..."):
                    results = make_request("GET", f"/repository/query?project_id={active_project_id}&query={repo_q}")
                    if results:
                        for file_match in results:
                            st.markdown(f"📄 **File:** `{file_match['file']}` (Similarity score: {file_match['similarity']:.2f})")
                            st.code(file_match["content_preview"], language="python")
                    else:
                        st.warning("No similar code templates matched.")
            else:
                st.error("Query string is required")
                
    with col_kb2:
        st.markdown("#### Upload Knowledge Base Materials")
        st.caption("Supported formats: PDF, DOCX, Markdown, TXT")
        uploaded_file = st.file_uploader("Select document file", type=["pdf", "docx", "md", "txt"])
        
        if st.button("Upload and Embed Document"):
            if uploaded_file:
                with st.spinner(f"Reading and embedding {uploaded_file.name} using RAG..."):
                    # Use multipart form data send
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {"project_id": active_project_id}
                    
                    url = f"{API_URL}/kb/upload"
                    try:
                        with httpx.Client(timeout=60.0) as client:
                            resp = client.post(url, data=data, files=files)
                            if resp.status_code == 200:
                                st.success(f"Indexed document '{uploaded_file.name}' into vector space!")
                            else:
                                st.error(f"Upload failed: {resp.text}")
                    except Exception as upload_err:
                        st.error(f"Upload network failure: {upload_err}")
            else:
                st.error("Please choose a file to upload.")

# --- TAB 4: AGENT CO-PILOT CHAT ---
with tabs[3]:
    st.markdown("### AI Co-Pilot Agent Framework")
    st.caption("Ask questions about code, repository architecture, plans, or documents. The Supervisor routes queries intelligently.")
    
    # Store session-based chat history locally in Streamlit
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
        
    chat_session_id = st.text_input("Conversation Thread ID", value="default_dev_session")
    
    # Render chat messages
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("trace"):
                 st.caption(f"Visited Trace: {' ➔ '.join(msg['trace'])}")
                 
    # Chat Input
    user_input = st.chat_input("Ask Co-Pilot anything...")
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        
        # Trigger agent workflow
        with st.chat_message("assistant"):
            with st.spinner("Agents discussing..."):
                payload = {
                    "project_id": active_project_id,
                    "session_id": chat_session_id,
                    "message": user_input
                }
                res = make_request("POST", "/chat", json=payload)
                if res:
                    st.markdown(res["response"])
                    st.caption(f"Visited Trace: {' ➔ '.join(res['agent_visited'])}")
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": res["response"],
                        "trace": res["agent_visited"]
                    })
                else:
                    st.error("No response received from agents.")

# --- TAB 5: MEETINGS & SPRINTS ---
with tabs[4]:
    st.markdown("### Meetings Action Items & Sprint Summaries")
    
    col_mt1, col_mt2 = st.columns(2)
    
    with col_mt1:
        st.markdown("#### Extract Meeting Action Items")
        mt_title = st.text_input("Meeting Title", value="Weekly Sync & Authentication Roadmap")
        mt_notes = st.text_area(
            "Enter meeting transcript / notes text",
            value="""Athar suggested we should implement JWT-based auth next week. 
We need to configure PyJWT, and build register/login endpoints. 
Reviewer should perform security analysis of the secret keys.
Athar is assigned to implement the auth utils.
Let's complete it by Thursday.""",
            height=200
        )
        if st.button("Parse Transcript"):
            if mt_notes:
                with st.spinner("Extracting action items..."):
                    payload = {"project_id": active_project_id, "title": mt_title, "notes_text": mt_notes}
                    res = make_request("POST", "/meetings", json=payload)
                    if res:
                        st.markdown("##### 📌 Summary:")
                        st.write(res["summary"])
                        
                        st.markdown("##### 📋 Action Items:")
                        for item in res["action_items"] or []:
                            st.write(f"- {item}")
                            
                        st.markdown("##### ➕ Suggested Database Tasks:")
                        for sug_task in res["suggested_tasks"] or []:
                            st.markdown(f"- **{sug_task['title']}** (Priority: {sug_task.get('priority', 'medium')})")
                            st.write(sug_task.get("description"))
                            
                            # Simple inline button to add suggested task
                            if st.button(f"Add: '{sug_task['title']}'", key=f"sug_task_{sug_task['title'][:20]}"):
                                add_payload = {
                                    "title": sug_task["title"],
                                    "description": sug_task.get("description", ""),
                                    "project_id": active_project_id,
                                    "assigned_to": None,
                                    "priority": sug_task.get("priority", "medium"),
                                    "status": "todo"
                                }
                                make_request("POST", "/tasks", json=add_payload)
                                st.success("Task added!")
                                st.rerun()
            else:
                st.error("Please insert meeting text")
                
    with col_mt2:
        st.markdown("#### Compile Sprint Report Summaries")
        sp_name = st.text_input("Sprint Name", value="Sprint 1 - Foundations")
        sp_completed = st.text_area("Completed Work Details", value="Core FastAPI endpoints built and database schemas mapped out.")
        sp_pending = st.text_area("Pending Work Details", value="Knowledge Base PDF uploads and Streamlit UI testing.")
        sp_risks = st.text_area("Highlighted Risks", value="Google Gemini / OpenAI rate limits during vector creation.")
        sp_velocity = st.number_input("Sprint Velocity (Story Points)", value=12, min_value=0)
        
        if st.button("Generate Sprint Summary Report"):
            payload = {
                "project_id": active_project_id,
                "sprint_name": sp_name,
                "completed_work": sp_completed,
                "pending_work": sp_pending,
                "risks": sp_risks,
                "team_velocity": int(sp_velocity)
            }
            with st.spinner("AI PM generating recommendations..."):
                res = make_request("POST", "/sprint/report", json=payload)
                if res:
                    st.success("Sprint Summary Report created!")
                    st.markdown("##### 🤖 Strategic AI Recommendations:")
                    st.markdown(res["recommendations"])
