import React from 'react';
import { Sparkles } from 'lucide-react';

export default function ChatTab({
  chatThread,
  setChatThread,
  chatMessages,
  loadingChat,
  chatBottomRef,
  chatInput,
  setChatInput,
  onSendChatMessage,
  chatTrace
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <label style={{ fontSize: '0.9rem', fontWeight: 600 }}>Conversation Thread ID:</label>
        <input 
          type="text" 
          className="text-input" 
          style={{ width: 'auto' }}
          value={chatThread} 
          onChange={(e) => setChatThread(e.target.value)} 
        />
      </div>

      <div className="chat-window">
        <div className="chat-history">
          {chatMessages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <div style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.25rem', color: msg.role === 'user' ? '#fff' : 'var(--primary)' }}>
                {msg.role === 'user' ? 'You' : 'AI Assistant'}
              </div>
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            </div>
          ))}
          {loadingChat && (
            <div className="chat-message assistant">
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <Sparkles size={14} className="animate-spin" /> Supervisor routing and agents analyzing query...
              </div>
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        <form className="chat-input-area" onSubmit={onSendChatMessage}>
          <input 
            type="text" 
            className="text-input" 
            placeholder="Ask Co-Pilot about files, plans, tasks..." 
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={loadingChat}
          />
          <button className="btn" type="submit" style={{ width: 'auto', padding: '0.75rem 1.5rem' }} disabled={loadingChat}>
            Send
          </button>
        </form>
      </div>

      {chatTrace.length > 0 && (
        <div className="visited-trace">
          Agent Path Trace: {chatTrace.join(' ➔ ')}
        </div>
      )}
    </div>
  );
}
