import React from 'react';
import { Sparkles, ChevronDown, ChevronUp, Trash2 } from 'lucide-react';

export default function TasksTab({
  newTaskTitle,
  setNewTaskTitle,
  newTaskDesc,
  setNewTaskDesc,
  newTaskPriority,
  setNewTaskPriority,
  newTaskAssignee,
  setNewTaskAssignee,
  developers,
  onCreateTask,
  
  tasks,
  expandedTaskId,
  setExpandedTaskId,
  onUpdateTaskStatus,
  onDeleteTask
}) {
  return (
    <div className="board-grid">
      {/* Create Task Card */}
      <form className="form-card" onSubmit={onCreateTask}>
        <h3 className="section-title" style={{ margin: 0 }}>Create New Task</h3>
        <input 
          type="text" 
          placeholder="Task Title (e.g. Implement OAuth Flow)" 
          className="text-input" 
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          required 
        />
        <textarea 
          placeholder="Task Description" 
          className="text-area" 
          value={newTaskDesc}
          onChange={(e) => setNewTaskDesc(e.target.value)}
          rows={4}
        />
        <select className="select-box" value={newTaskPriority} onChange={(e) => setNewTaskPriority(e.target.value)}>
          <option value="low">Low Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="high">High Priority</option>
          <option value="critical">Critical Priority</option>
        </select>
        <select className="select-box" value={newTaskAssignee} onChange={(e) => setNewTaskAssignee(e.target.value)}>
          <option value="">Unassigned</option>
          {developers.map(d => (
            <option key={d.id} value={d.id}>{d.name} ({d.role})</option>
          ))}
        </select>
        <button className="btn" type="submit">Create Task & Run AI Analysis</button>
      </form>

      {/* Task list and expander */}
      <div className="tasks-container">
        <h3 className="section-title" style={{ margin: 0 }}>Tasks List and AI Architecture Analysis</h3>
        {tasks.length > 0 ? (
          tasks.map(task => {
            const isExpanded = expandedTaskId === task.id;
            const dev = developers.find(d => d.id === task.assigned_to);
            
            return (
              <div key={task.id} className="task-expander">
                <div className="task-header" onClick={() => setExpandedTaskId(isExpanded ? null : task.id)}>
                  <div className="task-title-group">
                    <span style={{ fontSize: '1.2rem' }}>
                      {task.priority === 'critical' ? '🔴' : task.priority === 'high' ? '🟡' : task.priority === 'medium' ? '🟢' : '🔵'}
                    </span>
                    <span className={`badge ${task.status === 'in_progress' ? 'progress' : task.status}`}>
                      {task.status}
                    </span>
                    <strong style={{ fontSize: '1rem' }}>{task.title}</strong>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Assignee: {dev ? dev.name : 'Unassigned'}
                    </span>
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="task-details">
                    <p style={{ lineHeight: 1.5 }}>
                      <strong>Description:</strong> {task.description || 'No description provided.'}
                    </p>

                    {task.ai_analysis && (
                      <div className="ai-analysis-block">
                        <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontFamily: 'Space Grotesk' }}>
                          <Sparkles size={16} style={{ color: 'var(--primary)' }} /> AI Architecture Analysis
                        </h4>
                        <div style={{ fontSize: '0.9rem' }}>
                          <strong>Estimated Time:</strong> {task.ai_analysis.estimated_hours || 4} hours | <strong>Difficulty:</strong> {task.ai_analysis.difficulty || 'Medium'}
                        </div>
                        <div style={{ fontSize: '0.9rem' }}>
                          <strong>Required Tech:</strong> {task.ai_analysis.required_technologies?.join(', ') || 'None'}
                        </div>
                        
                        <div className="grid-2col" style={{ marginTop: '0.5rem' }}>
                          <div>
                            <strong style={{ fontSize: '0.85rem' }}>Implementation Steps:</strong>
                            <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                              {task.ai_analysis.suggested_implementation_steps?.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <strong style={{ fontSize: '0.85rem' }}>Folder Structure:</strong>
                            <pre style={{ background: 'var(--bg-main)', padding: '0.5rem', borderRadius: '6px', fontSize: '0.8rem', marginTop: '0.25rem', overflowX: 'auto' }}>
                              {JSON.stringify(task.ai_analysis.suggested_folder_structure, null, 2)}
                            </pre>
                          </div>
                        </div>

                        <div className="grid-2col" style={{ marginTop: '0.5rem' }}>
                          <div>
                            <strong style={{ fontSize: '0.85rem', color: 'var(--danger)' }}>Security Considerations:</strong>
                            <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                              {task.ai_analysis.security_considerations?.map((sec, idx) => (
                                <li key={idx}>{sec}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <strong style={{ fontSize: '0.85rem', color: 'var(--success)' }}>Testing Checklist:</strong>
                            <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                              {task.ai_analysis.testing_checklist?.map((test, idx) => (
                                <li key={idx}>{test}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginTop: '0.5rem' }}>
                      <select 
                        className="select-box" 
                        style={{ width: 'auto' }}
                        value={task.status} 
                        onChange={(e) => onUpdateTaskStatus(task.id, e.target.value, task.priority)}
                      >
                        <option value="todo">Todo</option>
                        <option value="in_progress">In Progress</option>
                        <option value="review">Review</option>
                        <option value="done">Done</option>
                      </select>
                      <select 
                        className="select-box" 
                        style={{ width: 'auto' }}
                        value={task.priority} 
                        onChange={(e) => onUpdateTaskStatus(task.id, task.status, e.target.value)}
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>

                      <select 
                        className="select-box" 
                        style={{ width: 'auto' }}
                        value={task.assigned_to || ''} 
                        onChange={(e) => onUpdateTaskStatus(task.id, task.status, task.priority, e.target.value)}
                      >
                        <option value="">Unassigned</option>
                        {developers.map(d => (
                          <option key={d.id} value={d.id}>{d.name} ({d.role})</option>
                        ))}
                      </select>

                      <button 
                        className="btn btn-secondary" 
                        style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--danger)' }} 
                        onClick={() => onDeleteTask(task.id)}
                      >
                        <Trash2 size={14} /> Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>
            No tasks created yet.
          </div>
        )}
      </div>
    </div>
  );
}
