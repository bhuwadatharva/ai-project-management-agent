import React, { useState, useEffect } from 'react';

export default function MeetingsTab({
  meetingTitle,
  setMeetingTitle,
  meetingNotes,
  setMeetingNotes,
  onParseMeeting,
  loadingMeeting,
  meetingResult,
  onAddMeetingSuggestedTask,
  developers,
  
  sprintName,
  setSprintName,
  sprintVelocity,
  setSprintVelocity,
  completedWork,
  setCompletedWork,
  pendingWork,
  setPendingWork,
  sprintRisks,
  setSprintRisks,
  onGenerateSprintReport,
  loadingSprint,
  sprintResult
}) {
  const [taskAssignees, setTaskAssignees] = useState({});

  // Initialize selected assignees from meeting results when they arrive
  useEffect(() => {
    if (meetingResult && meetingResult.suggested_tasks) {
      const initial = {};
      meetingResult.suggested_tasks.forEach((sug, idx) => {
        initial[idx] = sug.assigned_to || "";
      });
      setTaskAssignees(initial);
    }
  }, [meetingResult]);

  return (
    <div className="board-grid">
      {/* Meeting summaries */}
      <div className="form-card">
        <h3 className="section-title" style={{ margin: 0 }}>Extract Meeting Action Items</h3>
        <input 
          type="text" 
          className="text-input" 
          value={meetingTitle}
          onChange={(e) => setMeetingTitle(e.target.value)}
        />
        <textarea 
          className="text-area" 
          value={meetingNotes}
          onChange={(e) => setMeetingNotes(e.target.value)}
          rows={8}
        />
        <button className="btn" onClick={onParseMeeting} disabled={loadingMeeting}>
          {loadingMeeting ? 'Parsing notes...' : 'Parse Transcript'}
        </button>

        {meetingResult && (
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <strong style={{ color: 'var(--primary)' }}>Summary:</strong>
              <p style={{ fontSize: '0.9rem', marginTop: '0.25rem', lineHeight: 1.5 }}>{meetingResult.summary}</p>
            </div>
            <div>
              <strong style={{ color: 'var(--accent-pink)' }}>Action Items:</strong>
              <ul style={{ paddingLeft: '1.2rem', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                {meetingResult.action_items?.map((item, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong style={{ color: 'var(--success)' }}>Suggested Database Tasks:</strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.25rem' }}>
                {meetingResult.suggested_tasks?.map((sug, idx) => {
                  const suggestedDev = developers.find(d => d.id === sug.assigned_to);
                  
                  return (
                    <div key={idx} style={{ padding: '0.75rem', backgroundColor: 'var(--bg-main)', border: '1px solid var(--border-color)', borderRadius: '8px', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{sug.title}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sug.description}</div>
                        </div>
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem', marginTop: '0.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Assignee:</span>
                          <select 
                            className="select-box" 
                            style={{ width: 'auto', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                            value={taskAssignees[idx] || ""}
                            onChange={(e) => setTaskAssignees({ ...taskAssignees, [idx]: e.target.value })}
                          >
                            <option value="">Unassigned</option>
                            {developers.map(d => (
                              <option key={d.id} value={d.id}>{d.name}</option>
                            ))}
                          </select>
                          {sug.assignee && !sug.assigned_to && (
                            <span style={{ fontSize: '0.7rem', color: 'var(--warning)' }}>
                              (AI suggested: "{sug.assignee}" but not registered)
                            </span>
                          )}
                          {sug.assigned_to && (
                            <span style={{ fontSize: '0.7rem', color: 'var(--success)' }}>
                              (AI matched: {suggestedDev?.name})
                            </span>
                          )}
                        </div>
                        
                        <button 
                          className="btn" 
                          style={{ width: 'auto', padding: '0.35rem 0.75rem', fontSize: '0.75rem' }} 
                          onClick={() => onAddMeetingSuggestedTask({ ...sug, assigned_to: taskAssignees[idx] })}
                        >
                          Add Task
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sprint summaries */}
      <div className="form-card">
        <h3 className="section-title" style={{ margin: 0 }}>Compile Sprint Report Summaries</h3>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sprint Name</label>
            <input type="text" className="text-input" value={sprintName} onChange={(e) => setSprintName(e.target.value)} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Sprint Velocity</label>
            <input type="number" className="text-input" value={sprintVelocity} onChange={(e) => setSprintVelocity(e.target.value)} />
          </div>
        </div>

        <div>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Completed Work Details</label>
          <textarea className="text-area" value={completedWork} onChange={(e) => setCompletedWork(e.target.value)} rows={3} />
        </div>
        <div>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Pending Work Details</label>
          <textarea className="text-area" value={pendingWork} onChange={(e) => setPendingWork(e.target.value)} rows={3} />
        </div>
        <div>
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Highlighted Risks</label>
          <textarea className="text-area" value={sprintRisks} onChange={(e) => setSprintRisks(e.target.value)} rows={3} />
        </div>

        <button className="btn" onClick={onGenerateSprintReport} disabled={loadingSprint}>
          {loadingSprint ? 'Generating...' : 'Generate Sprint Summary Report'}
        </button>

        {sprintResult && (
          <div style={{ marginTop: '1rem', backgroundColor: 'var(--bg-main)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ color: 'var(--success)', fontFamily: 'Space Grotesk', marginBottom: '0.5rem' }}>Strategic AI Recommendations</h4>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
              {sprintResult.recommendations}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
