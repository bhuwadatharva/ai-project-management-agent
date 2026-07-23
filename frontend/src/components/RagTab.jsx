import React from 'react';
import { Upload } from 'lucide-react';

export default function RagTab({
  repoUrl,
  setRepoUrl,
  onIndexRepo,
  
  repoSearchQuery,
  setRepoSearchQuery,
  onSearchCode,
  loadingSearch,
  repoSearchResults,
  
  onFileUpload,
  uploadProgress,
  uploadMessage
}) {
  return (
    <div className="board-grid">
      <div className="form-card">
        <h3 className="section-title" style={{ margin: 0 }}>Index Git Repository</h3>
        <input 
          type="text" 
          className="text-input" 
          placeholder="Git URL or Local Folder Path" 
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
        />
        <button className="btn" onClick={onIndexRepo}>Connect & Index Repository</button>

        <hr style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '1rem 0' }} />

        <h3 className="section-title" style={{ margin: 0 }}>Semantic Code & File Search</h3>
        <form onSubmit={onSearchCode} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input 
            type="text" 
            className="text-input" 
            placeholder="Query (e.g. Where to check JWT tokens?)" 
            value={repoSearchQuery}
            onChange={(e) => setRepoSearchQuery(e.target.value)}
          />
          <button className="btn" type="submit" disabled={loadingSearch}>
            {loadingSearch ? 'Searching...' : 'Search Code'}
          </button>
        </form>

        {repoSearchResults.length > 0 && (
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {repoSearchResults.map((result, idx) => (
              <div key={idx} style={{ padding: '0.75rem', backgroundColor: 'var(--bg-main)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--primary)', marginBottom: '0.25rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>📄 {result.file}</span>
                  <span>Score: {result.similarity.toFixed(2)}</span>
                </div>
                <pre style={{ fontSize: '0.75rem', overflowX: 'auto', background: '#070a13', padding: '0.5rem', borderRadius: '4px' }}>
                  {result.content_preview}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="form-card">
        <h3 className="section-title" style={{ margin: 0 }}>Upload Knowledge Base Materials</h3>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Supported formats: PDF, DOCX, Markdown, TXT</span>
        
        <div style={{ border: '2px dashed var(--border-color)', borderRadius: '12px', padding: '2rem', textAlign: 'center', cursor: 'pointer', position: 'relative' }}>
          <input 
            type="file" 
            accept=".pdf,.docx,.md,.txt" 
            onChange={onFileUpload} 
            style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer' }}
          />
          <Upload size={32} style={{ color: 'var(--primary)', marginBottom: '0.75rem' }} />
          <div>Drag file here or click to choose from system</div>
        </div>

        {uploadProgress && <div style={{ color: 'var(--primary)', fontSize: '0.9rem' }}>{uploadMessage}</div>}
        {!uploadProgress && uploadMessage && (
          <div style={{ color: uploadMessage.startsWith('Error') ? 'var(--danger)' : 'var(--success)', fontSize: '0.9rem' }}>
            {uploadMessage}
          </div>
        )}
      </div>
    </div>
  );
}
