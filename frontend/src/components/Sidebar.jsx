import React from 'react';
import { Plus, Users, Settings, Bell, LogOut, Check } from 'lucide-react';

export default function Sidebar({
  projects,
  selectedProjectId,
  setSelectedProjectId,
  newProjName,
  setNewProjName,
  newProjDesc,
  setNewProjDesc,
  newProjRepo,
  setNewProjRepo,
  onCreateProject,
  
  newDevName,
  setNewDevName,
  newDevEmail,
  setNewDevEmail,
  newDevRole,
  setNewDevRole,
  onRegisterDev,
  
  newSettingKey,
  setNewSettingKey,
  newSettingValue,
  setNewSettingValue,
  onUpdateSetting,
  settings,
  
  notifications,
  onReadNotification,
  user,
  onLogout,
  setRepoUrl
}) {
  return (
    <aside className="sidebar">
      <div className="logo-section">
        <img src="https://img.icons8.com/nolan/96/airplane-take-off.png" className="logo-img" alt="Logo" />
        <h1 className="logo-text">DevPilot AI</h1>
      </div>

      <div className="sidebar-section">
        <label className="sidebar-label">Active Workspace Project</label>
        <select 
          className="select-box" 
          value={selectedProjectId} 
          onChange={(e) => {
            setSelectedProjectId(e.target.value);
            const p = projects.find(proj => proj.id === e.target.value);
            setRepoUrl(p?.repo_url || '');
          }}
        >
          {projects.length > 0 ? (
            projects.map(proj => (
              <option key={proj.id} value={proj.id}>{proj.name}</option>
            ))
          ) : (
            <option value="">No Projects Available</option>
          )}
        </select>
      </div>

      {/* Create Project Expander */}
      <details className="form-card" style={{ padding: '0.75rem', cursor: 'pointer' }}>
        <summary style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Plus size={16} /> Create New Project
        </summary>
        <form style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} onSubmit={onCreateProject}>
          <input 
            type="text" 
            placeholder="Project Name" 
            className="text-input" 
            value={newProjName}
            onChange={(e) => setNewProjName(e.target.value)}
            required 
          />
          <textarea 
            placeholder="Description" 
            className="text-area" 
            value={newProjDesc}
            onChange={(e) => setNewProjDesc(e.target.value)}
          />
          <input 
            type="text" 
            placeholder="Git URL / Path" 
            className="text-input" 
            value={newProjRepo}
            onChange={(e) => setNewProjRepo(e.target.value)}
          />
          <button className="btn" type="submit">Create Workspace</button>
        </form>
      </details>

      {/* Register Team Developer Expander */}
      <details className="form-card" style={{ padding: '0.75rem', cursor: 'pointer' }}>
        <summary style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={16} /> Register Team Developer
        </summary>
        <form style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} onSubmit={onRegisterDev}>
          <input 
            type="text" 
            placeholder="Developer Name" 
            className="text-input" 
            value={newDevName}
            onChange={(e) => setNewDevName(e.target.value)}
            required 
          />
          <input 
            type="email" 
            placeholder="Developer Email" 
            className="text-input" 
            value={newDevEmail}
            onChange={(e) => setNewDevEmail(e.target.value)}
            required 
          />
          <select className="select-box" value={newDevRole} onChange={(e) => setNewDevRole(e.target.value)}>
            <option value="Frontend Developer">Frontend Developer</option>
            <option value="Backend Developer">Backend Developer</option>
            <option value="DevOps Engineer">DevOps Engineer</option>
            <option value="QA Tester">QA Tester</option>
            <option value="Architect">Architect</option>
          </select>
          <button className="btn" type="submit">Register Member</button>
        </form>
      </details>

      {/* Settings Expander */}
      <details className="form-card" style={{ padding: '0.75rem', cursor: 'pointer' }}>
        <summary style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Settings size={16} /> Configure System Settings
        </summary>
        <form style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }} onSubmit={onUpdateSetting}>
          <input 
            type="text" 
            placeholder="Setting Key" 
            className="text-input" 
            value={newSettingKey}
            onChange={(e) => setNewSettingKey(e.target.value)}
            required 
          />
          <input 
            type="text" 
            placeholder="Setting Value" 
            className="text-input" 
            value={newSettingValue}
            onChange={(e) => setNewSettingValue(e.target.value)}
            required 
          />
          <button className="btn" type="submit">Save Setting</button>
        </form>
        {settings.length > 0 && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {settings.map(s => (
              <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.25rem' }}>
                <span style={{ color: 'var(--text-muted)' }}>{s.key}:</span>
                <span>{s.value}</span>
              </div>
            ))}
          </div>
        )}
      </details>

      {/* Notifications Panel */}
      <div className="sidebar-section">
        <label className="sidebar-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Bell size={14} /> Notifications Box
        </label>
        <div className="notifications-panel">
          {notifications.length > 0 ? (
            notifications.map(n => (
              <div key={n.id} className={`notification-item ${n.is_read === 0 ? 'notification-unread' : ''}`}>
                <div>
                  <div style={{ fontWeight: 600 }}>{n.title}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{n.message}</div>
                </div>
                {n.is_read === 0 && (
                  <button 
                    style={{ background: 'none', border: 'none', color: 'var(--success)', cursor: 'pointer' }}
                    onClick={() => onReadNotification(n.id)}
                  >
                    <Check size={14} />
                  </button>
                )}
              </div>
            ))
          ) : (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '1rem' }}>
              No notifications
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'var(--primary)', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>
            {user?.name ? user.name[0].toUpperCase() : 'U'}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{user?.name || 'Developer User'}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.role || 'Lead Engineer'}</div>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={onLogout} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </aside>
  );
}
