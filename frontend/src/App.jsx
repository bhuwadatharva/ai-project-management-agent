import React, { useState, useEffect, useRef } from 'react';
import AuthScreen from './components/AuthScreen';
import Sidebar from './components/Sidebar';
import DashboardTab from './components/DashboardTab';
import TasksTab from './components/TasksTab';
import RagTab from './components/RagTab';
import ChatTab from './components/ChatTab';
import MeetingsTab from './components/MeetingsTab';

const API_URL = 'https://ai-project-management-agent-7y2e.onrender.com/api';

export default function App() {
  // Auth State
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));
  const [isLoginView, setIsLoginView] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('developer');
  const [authError, setAuthError] = useState('');

  // Project Workspaces State
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [newProjName, setNewProjName] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');
  const [newProjRepo, setNewProjRepo] = useState('');

  // Developers State
  const [developers, setDevelopers] = useState([]);
  const [newDevName, setNewDevName] = useState('');
  const [newDevEmail, setNewDevEmail] = useState('');
  const [newDevRole, setNewDevRole] = useState('Backend Developer');

  // Notifications State
  const [notifications, setNotifications] = useState([]);

  // System Settings State
  const [settings, setSettings] = useState([]);
  const [newSettingKey, setNewSettingKey] = useState('');
  const [newSettingValue, setNewSettingValue] = useState('');

  // Tasks State
  const [tasks, setTasks] = useState([]);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDesc, setNewTaskDesc] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('medium');
  const [newTaskAssignee, setNewTaskAssignee] = useState('');
  const [expandedTaskId, setExpandedTaskId] = useState(null);

  // Active Tab State
  const [activeTab, setActiveTab] = useState('dashboard');

  // Suggestions State
  const [aiSuggestions, setAiSuggestions] = useState('');
  const [suggestionsTrace, setSuggestionsTrace] = useState([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Repository & RAG State
  const [repoUrl, setRepoUrl] = useState('');
  const [repoSearchQuery, setRepoSearchQuery] = useState('');
  const [repoSearchResults, setRepoSearchResults] = useState([]);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(false);

  // Chat Co-Pilot State
  const [chatThread, setChatThread] = useState('default_dev_session');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [loadingChat, setLoadingChat] = useState(false);
  const [chatTrace, setChatTrace] = useState([]);

  // Meetings State
  const [meetingTitle, setMeetingTitle] = useState('Weekly Sync & Authentication Roadmap');
  const [meetingNotes, setMeetingNotes] = useState(
    "Athar suggested we should implement JWT-based auth next week.\nWe need to configure PyJWT, and build register/login endpoints.\nReviewer should perform security analysis of the secret keys.\nAthar is assigned to implement the auth utils.\nLet's complete it by Thursday."
  );
  const [meetingResult, setMeetingResult] = useState(null);
  const [loadingMeeting, setLoadingMeeting] = useState(false);

  // Sprint Report State
  const [sprintName, setSprintName] = useState('Sprint 1 - Foundations');
  const [completedWork, setCompletedWork] = useState('Core FastAPI endpoints built and database schemas mapped out.');
  const [pendingWork, setPendingWork] = useState('Knowledge Base PDF uploads and Streamlit UI testing.');
  const [sprintRisks, setSprintRisks] = useState('Google Gemini / OpenAI rate limits during vector creation.');
  const [sprintVelocity, setSprintVelocity] = useState(12);
  const [sprintResult, setSprintResult] = useState(null);
  const [loadingSprint, setLoadingSprint] = useState(false);

  // Auto-scroller for chat
  const chatBottomRef = useRef(null);

  // General Fetch Wrapper
  const fetchAPI = async (path, options = {}) => {
    const url = `${API_URL}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers
    };

    try {
      const res = await fetch(url, { ...options, headers });
      if (res.status === 401) {
        handleLogout();
        return null;
      }
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Error ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`API Call failed to ${path}:`, err);
      alert(err.message || 'Connection error');
      return null;
    }
  };

  // Load initial configurations
  useEffect(() => {
    if (token) {
      loadProjects();
      loadDevelopers();
    }
  }, [token]);

  useEffect(() => {
    if (selectedProjectId) {
      loadTasks();
      loadNotifications();
      loadSettings();
    } else {
      setTasks([]);
      setNotifications([]);
      setSettings([]);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages]);

  const loadProjects = async () => {
    const data = await fetchAPI('/projects');
    if (data) {
      setProjects(data);
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id);
        setRepoUrl(data[0].repo_url || '');
      }
    }
  };

  const loadDevelopers = async () => {
    const data = await fetchAPI('/developers');
    if (data) setDevelopers(data);
  };

  const loadTasks = async () => {
    const data = await fetchAPI(`/tasks?project_id=${selectedProjectId}`);
    if (data) setTasks(data);
  };

  const loadNotifications = async () => {
    const data = await fetchAPI(`/notifications?project_id=${selectedProjectId}`);
    if (data) setNotifications(data);
  };

  const loadSettings = async () => {
    const data = await fetchAPI(`/settings?project_id=${selectedProjectId}`);
    if (data) setSettings(data);
  };

  // Authentication Handlers
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    const path = isLoginView ? '/auth/login' : '/auth/signup';
    const payload = isLoginView ? { email, password } : { email, password, name, role };

    try {
      const res = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      if (isLoginView) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        setToken(data.access_token);
        setUser(data.user);
      } else {
        alert('Account created! Please log in.');
        setIsLoginView(true);
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken('');
    setUser(null);
  };

  // Create Project Workspace
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjName) return;
    const res = await fetchAPI('/projects', {
      method: 'POST',
      body: JSON.stringify({ name: newProjName, description: newProjDesc, repo_url: newProjRepo })
    });
    if (res) {
      setNewProjName('');
      setNewProjDesc('');
      setNewProjRepo('');
      loadProjects();
      setSelectedProjectId(res.id);
    }
  };

  // Register Developer
  const handleRegisterDev = async (e) => {
    e.preventDefault();
    if (!newDevName || !newDevEmail) return;
    const res = await fetchAPI('/developers', {
      method: 'POST',
      body: JSON.stringify({ name: newDevName, email: newDevEmail, role: newDevRole })
    });
    if (res) {
      setNewDevName('');
      setNewDevEmail('');
      loadDevelopers();
    }
  };

  // Create Task
  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle) return;
    const payload = {
      title: newTaskTitle,
      description: newTaskDesc,
      project_id: selectedProjectId,
      assigned_to: newTaskAssignee || null,
      priority: newTaskPriority,
      status: 'todo'
    };

    const res = await fetchAPI('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res) {
      setNewTaskTitle('');
      setNewTaskDesc('');
      setNewTaskAssignee('');
      loadTasks();

      await fetchAPI('/notifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: selectedProjectId,
          title: 'Task Created',
          message: `New task "${res.title}" created with priority ${res.priority}`
        })
      });
      loadNotifications();
    }
  };

  const handleUpdateTaskStatus = async (taskId, status, priority, assigned_to = undefined) => {
    const payload = { status, priority };
    if (assigned_to !== undefined) {
      payload.assigned_to = assigned_to || null;
    }
    const res = await fetchAPI(`/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    if (res) {
      loadTasks();
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return;
    const res = await fetchAPI(`/tasks/${taskId}`, { method: 'DELETE' });
    if (res) loadTasks();
  };

  // Generate Suggestions
  const handleGenerateSuggestions = async () => {
    setLoadingSuggestions(true);
    const payload = {
      project_id: selectedProjectId,
      session_id: 'dashboard_analytics',
      message: 'Analyze my project status and tasks list. Give 4 strategic bullet point suggestions for improvement based on pending items.'
    };
    const res = await fetchAPI('/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res) {
      setAiSuggestions(res.response);
      setSuggestionsTrace(res.agent_visited);
    }
    setLoadingSuggestions(false);
  };

  // Settings CRUD
  const handleUpdateSetting = async (e) => {
    e.preventDefault();
    if (!newSettingKey || !newSettingValue) return;
    const res = await fetchAPI('/settings', {
      method: 'POST',
      body: JSON.stringify({ project_id: selectedProjectId, key: newSettingKey, value: newSettingValue })
    });
    if (res) {
      setNewSettingKey('');
      setNewSettingValue('');
      loadSettings();
    }
  };

  // Read notification
  const handleReadNotification = async (notifId) => {
    const res = await fetchAPI(`/notifications/${notifId}/read`, { method: 'PUT' });
    if (res) loadNotifications();
  };

  // Repository & KB Handlers
  const handleIndexRepo = async () => {
    if (!repoUrl) return;
    const res = await fetchAPI(`/repository/index?project_id=${selectedProjectId}&repo_path_or_url=${encodeURIComponent(repoUrl)}`, {
      method: 'POST'
    });
    if (res) {
      alert('Indexing has been scheduled in the background successfully.');
    }
  };

  const handleSearchCode = async (e) => {
    e.preventDefault();
    if (!repoSearchQuery) return;
    setLoadingSearch(true);
    const res = await fetchAPI(`/repository/query?project_id=${selectedProjectId}&query=${encodeURIComponent(repoSearchQuery)}`);
    if (res) {
      setRepoSearchResults(res);
    }
    setLoadingSearch(false);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadProgress(true);
    setUploadMessage('Uploading and parsing document contents...');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', selectedProjectId);

    try {
      const res = await fetch(`${API_URL}/kb/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setUploadMessage(`Success: Indexed document "${data.name}" successfully!`);
    } catch (err) {
      setUploadMessage(`Error: ${err.message}`);
    }
    setUploadProgress(false);
  };

  // Co-Pilot Chat Handlers
  const handleSendChatMessage = async (e) => {
    e.preventDefault();
    if (!chatInput) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    const inputMsg = chatInput;
    setChatInput('');
    setLoadingChat(true);

    const res = await fetchAPI('/chat', {
      method: 'POST',
      body: JSON.stringify({
        project_id: selectedProjectId,
        session_id: chatThread,
        message: inputMsg
      })
    });

    if (res) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
      setChatTrace(res.agent_visited);
    }
    setLoadingChat(false);
  };

  // Meetings Notes analysis
  const handleParseMeeting = async (e) => {
    e.preventDefault();
    setLoadingMeeting(true);
    const res = await fetchAPI('/meetings', {
      method: 'POST',
      body: JSON.stringify({
        project_id: selectedProjectId,
        title: meetingTitle,
        notes_text: meetingNotes
      })
    });
    if (res) {
      setMeetingResult(res);
    }
    setLoadingMeeting(false);
  };

  const handleAddMeetingSuggestedTask = async (sugTask) => {
    const payload = {
      title: sugTask.title,
      description: sugTask.description,
      project_id: selectedProjectId,
      assigned_to: sugTask.assigned_to || null,
      priority: sugTask.priority || 'medium',
      status: 'todo'
    };
    const res = await fetchAPI('/tasks', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res) {
      alert(`Task "${sugTask.title}" created successfully!`);
      loadTasks();
    }
  };

  // Sprint report summary
  const handleGenerateSprintReport = async (e) => {
    e.preventDefault();
    setLoadingSprint(true);
    const res = await fetchAPI('/sprint/report', {
      method: 'POST',
      body: JSON.stringify({
        project_id: selectedProjectId,
        sprint_name: sprintName,
        completed_work: completedWork,
        pending_work: pendingWork,
        risks: sprintRisks,
        team_velocity: Number(sprintVelocity)
      })
    });
    if (res) {
      setSprintResult(res);
    }
    setLoadingSprint(false);
  };

  if (!token) {
    return (
      <AuthScreen
        isLoginView={isLoginView}
        setIsLoginView={setIsLoginView}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        name={name}
        setName={setName}
        role={role}
        setRole={setRole}
        authError={authError}
        onSubmit={handleAuthSubmit}
      />
    );
  }

  const activeProject = projects.find(p => p.id === selectedProjectId);

  return (
    <div className="app-container">
      <Sidebar
        projects={projects}
        selectedProjectId={selectedProjectId}
        setSelectedProjectId={setSelectedProjectId}
        newProjName={newProjName}
        setNewProjName={setNewProjName}
        newProjDesc={newProjDesc}
        setNewProjDesc={setNewProjDesc}
        newProjRepo={newProjRepo}
        setNewProjRepo={setNewProjRepo}
        onCreateProject={handleCreateProject}

        newDevName={newDevName}
        setNewDevName={setNewDevName}
        newDevEmail={newDevEmail}
        setNewDevEmail={setNewDevEmail}
        newDevRole={newDevRole}
        setNewDevRole={setNewDevRole}
        onRegisterDev={handleRegisterDev}

        newSettingKey={newSettingKey}
        setNewSettingKey={setNewSettingKey}
        newSettingValue={newSettingValue}
        setNewSettingValue={setNewSettingValue}
        onUpdateSetting={handleUpdateSetting}
        settings={settings}

        notifications={notifications}
        onReadNotification={handleReadNotification}
        user={user}
        onLogout={handleLogout}
        setRepoUrl={setRepoUrl}
      />

      <main className="main-content">
        <header className="header-section">
          <div>
            <h1 className="main-title">DevPilot AI</h1>
            <div className="subtitle">
              AI-Powered Engineering Project Manager / Workspace: <b>{activeProject?.name || 'No Project Selected'}</b>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="tabs-container">
          <button className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            📊 Dashboard
          </button>
          <button className={`tab-btn ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>
            📋 Task Board
          </button>
          <button className={`tab-btn ${activeTab === 'rag' ? 'active' : ''}`} onClick={() => setActiveTab('rag')}>
            📁 Git & Knowledge Base
          </button>
          <button className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
            💬 Agent Co-Pilot
          </button>
          <button className={`tab-btn ${activeTab === 'meetings' ? 'active' : ''}`} onClick={() => setActiveTab('meetings')}>
            📝 Sprints & Meetings
          </button>
        </nav>

        {/* Tab Components */}
        {activeTab === 'dashboard' && (
          <DashboardTab
            tasks={tasks}
            loadingSuggestions={loadingSuggestions}
            onGenerateSuggestions={handleGenerateSuggestions}
            aiSuggestions={aiSuggestions}
            suggestionsTrace={suggestionsTrace}
          />
        )}

        {activeTab === 'tasks' && (
          <TasksTab
            newTaskTitle={newTaskTitle}
            setNewTaskTitle={setNewTaskTitle}
            newTaskDesc={newTaskDesc}
            setNewTaskDesc={setNewTaskDesc}
            newTaskPriority={newTaskPriority}
            setNewTaskPriority={setNewTaskPriority}
            newTaskAssignee={newTaskAssignee}
            setNewTaskAssignee={setNewTaskAssignee}
            developers={developers}
            onCreateTask={handleCreateTask}
            tasks={tasks}
            expandedTaskId={expandedTaskId}
            setExpandedTaskId={setExpandedTaskId}
            onUpdateTaskStatus={handleUpdateTaskStatus}
            onDeleteTask={handleDeleteTask}
          />
        )}

        {activeTab === 'rag' && (
          <RagTab
            repoUrl={repoUrl}
            setRepoUrl={setRepoUrl}
            onIndexRepo={handleIndexRepo}
            repoSearchQuery={repoSearchQuery}
            setRepoSearchQuery={setRepoSearchQuery}
            onSearchCode={handleSearchCode}
            loadingSearch={loadingSearch}
            repoSearchResults={repoSearchResults}
            onFileUpload={handleFileUpload}
            uploadProgress={uploadProgress}
            uploadMessage={uploadMessage}
          />
        )}

        {activeTab === 'chat' && (
          <ChatTab
            chatThread={chatThread}
            setChatThread={setChatThread}
            chatMessages={chatMessages}
            loadingChat={loadingChat}
            chatBottomRef={chatBottomRef}
            chatInput={chatInput}
            setChatInput={setChatInput}
            onSendChatMessage={handleSendChatMessage}
            chatTrace={chatTrace}
          />
        )}

        {activeTab === 'meetings' && (
          <MeetingsTab
            meetingTitle={meetingTitle}
            setMeetingTitle={setMeetingTitle}
            meetingNotes={meetingNotes}
            setMeetingNotes={setMeetingNotes}
            onParseMeeting={handleParseMeeting}
            loadingMeeting={loadingMeeting}
            meetingResult={meetingResult}
            onAddMeetingSuggestedTask={handleAddMeetingSuggestedTask}
            developers={developers}

            sprintName={sprintName}
            setSprintName={setSprintName}
            sprintVelocity={sprintVelocity}
            setSprintVelocity={setSprintVelocity}
            completedWork={completedWork}
            setCompletedWork={setCompletedWork}
            pendingWork={pendingWork}
            setPendingWork={setPendingWork}
            sprintRisks={sprintRisks}
            setSprintRisks={setSprintRisks}
            onGenerateSprintReport={handleGenerateSprintReport}
            loadingSprint={loadingSprint}
            sprintResult={sprintResult}
          />
        )}
      </main>
    </div>
  );
}
