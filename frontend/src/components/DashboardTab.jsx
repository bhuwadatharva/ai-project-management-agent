import React from 'react';
import { Sparkles } from 'lucide-react';

export default function DashboardTab({
  tasks,
  loadingSuggestions,
  onGenerateSuggestions,
  aiSuggestions,
  suggestionsTrace
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <section className="metrics-grid">
        <div className="metric-card">
          <div className="metric-val">{tasks.length}</div>
          <div className="metric-label">Total Backlog Tasks</div>
        </div>
        <div className="metric-card">
          <div className="metric-val purple">
            {tasks.filter(t => t.status === 'in_progress').length} / {tasks.filter(t => t.status === 'review').length}
          </div>
          <div className="metric-label">In Progress / Review</div>
        </div>
        <div className="metric-card">
          <div className="metric-val green">{tasks.filter(t => t.status === 'done').length}</div>
          <div className="metric-label">Completed Tasks</div>
        </div>
        <div className="metric-card">
          <div className="metric-val pink">{tasks.filter(t => t.status === 'todo').length}</div>
          <div className="metric-label">Pending Backlog</div>
        </div>
      </section>

      <section className="suggestion-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} style={{ color: 'var(--accent-pink)' }} /> AI strategic suggestions
          </h3>
          <button 
            className="btn" 
            style={{ width: 'auto', padding: '0.5rem 1rem' }} 
            onClick={onGenerateSuggestions} 
            disabled={loadingSuggestions}
          >
            {loadingSuggestions ? 'Analyzing...' : 'Generate AI Project Suggestions'}
          </button>
        </div>

        {aiSuggestions ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{aiSuggestions}</div>
            {suggestionsTrace.length > 0 && (
              <div className="visited-trace">
                Visited Trace: {suggestionsTrace.join(' ➔ ')}
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Click the button to let the Supervisor and AI Agents review project status and generate tasks roadmap.
          </div>
        )}
      </section>
    </div>
  );
}
