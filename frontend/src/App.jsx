import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Send, Bot, User, Link as LinkIcon, Menu, Plus, MessageSquare,
  Sun, Moon, Sparkles, Trash2, Database, Globe, X
} from 'lucide-react';
import './index.css';

// ── Mode definitions (auto is the silent default — not shown in picker) ────────
const AUTO_MODE = {
  key: 'auto',
  label: 'Auto',
  icon: null,
  color: 'var(--accent)',
  placeholder: 'Ask anything…',
  desc: 'AI picks the best tool automatically',
};

const MODES = {
  vector_db: {
    key: 'vector_db',
    label: 'Vector DB',
    icon: Database,
    color: '#34d399',
    placeholder: 'Ask a question about your knowledge base…',
    desc: 'Search your uploaded documents',
  },
  link_reader: {
    key: 'link_reader',
    label: 'Webpage Link',
    icon: Globe,
    color: '#60a5fa',
    placeholder: 'Paste a URL or ask about a loaded page…',
    desc: 'Scrape and analyse any webpage',
  },
};

// Safe lookup — always returns a valid mode object
const getModeInfo = (key) => MODES[key] || AUTO_MODE;

function App() {
  const [sessions, setSessions] = useState([
    { id: 1, title: 'New Conversation', messages: [] }
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(window.innerWidth > 768);
  const [isDarkTheme, setIsDarkTheme] = useState(true);

  // Mode state
  const [activeMode, setActiveMode] = useState('auto');
  const [pickerOpen, setPickerOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const pickerRef = useRef(null);

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  // Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
  }, [isDarkTheme]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }, [input]);

  // Close picker on outside click
  useEffect(() => {
    const handleClick = (e) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target)) {
        setPickerOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  const createNewChat = () => {
    const newId = Date.now();
    setSessions([{ id: newId, title: 'New Conversation', messages: [] }, ...sessions]);
    setCurrentSessionId(newId);
    if (window.innerWidth <= 768) setIsSidebarOpen(false);
  };

  const selectSession = (id) => {
    setCurrentSessionId(id);
    if (window.innerWidth <= 768) setIsSidebarOpen(false);
  };

  const deleteSession = (e, id) => {
    e.stopPropagation();
    const updated = sessions.filter(s => s.id !== id);
    if (updated.length === 0) {
      const newId = Date.now();
      setSessions([{ id: newId, title: 'New Conversation', messages: [] }]);
      setCurrentSessionId(newId);
    } else {
      setSessions(updated);
      if (currentSessionId === id) setCurrentSessionId(updated[0].id);
    }
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    let updatedSessions = [...sessions];
    const sessionIndex = updatedSessions.findIndex(s => s.id === currentSessionId);
    if (updatedSessions[sessionIndex].messages.length === 0) {
      updatedSessions[sessionIndex].title = userQuery.slice(0, 30) + (userQuery.length > 30 ? '…' : '');
    }

    // Tag user message with the mode used
    const newMessages = [
      ...updatedSessions[sessionIndex].messages,
      { role: 'user', content: userQuery, mode: activeMode }
    ];
    updatedSessions[sessionIndex].messages = newMessages;
    setSessions(updatedSessions);
    setIsLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'https://modular-rag-backend-xec0.onrender.com';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          chat_history: newMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
          web_content: [...newMessages].reverse().find(m => m.web_content)?.web_content || '',
          mode: activeMode,
        })
      });

      if (!response.ok) throw new Error('Server Error');
      const data = await response.json();

      let newSessions = [...sessions];
      const idxAfter = newSessions.findIndex(s => s.id === currentSessionId);
      newSessions[idxAfter].messages = [
        ...newSessions[idxAfter].messages,
        { role: 'assistant', content: data.answer, web_content: data.web_content }
      ];
      setSessions(newSessions);
    } catch (err) {
      console.error(err);
      let newSessions = [...sessions];
      const idx = newSessions.findIndex(s => s.id === currentSessionId);
      newSessions[idx].messages = [
        ...newSessions[idx].messages,
        { role: 'assistant', content: 'Error: Failed to reach the RAG backend. Is the Python API running?' }
      ];
      setSessions(newSessions);
    } finally {
      setIsLoading(false);
    }
  };

  // Derived from active mode — always safe, never undefined
  const activeModeDef = getModeInfo(activeMode);
  const ModeIcon = activeModeDef.icon;
  const modeColor = activeModeDef.color;

  return (
    <div className="app-layout">
      {/* Mobile overlay */}
      <div className={`sidebar-overlay ${isSidebarOpen ? 'active' : ''}`} onClick={() => setIsSidebarOpen(false)} />

      {/* Sidebar */}
      <div className={`sidebar ${!isSidebarOpen ? 'closed' : ''}`}>
        <button onClick={createNewChat} className="new-chat-btn">
          <Plus size={16} /> New Chat
        </button>

        <div className="history-list">
          {sessions.map(session => (
            <div
              key={session.id}
              className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
              onClick={() => selectSession(session.id)}
            >
              <div className="history-item-content">
                <MessageSquare size={16} />
                <span className="history-title">{session.title}</span>
              </div>
              <button className="delete-chat-btn" onClick={(e) => deleteSession(e, session.id)} title="Delete">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <button onClick={() => setIsDarkTheme(!isDarkTheme)} className="theme-toggle">
            {isDarkTheme ? <Sun size={18} /> : <Moon size={18} />}
            {isDarkTheme ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="main-content">
        <header className="header">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="icon-btn">
            <Menu size={20} />
          </button>

          {/* Centered title block */}
          <div className="header-center">
            <div className="header-title">Modular RAG</div>
            <div className="header-topic">Reinforcement Learning</div>
          </div>

          {/* Active mode badge in header — only when not auto */}
          {activeMode !== 'auto' && ModeIcon && (
            <div className="header-mode-badge" style={{ '--mode-color': modeColor }}>
              <ModeIcon size={13} />
              {activeModeDef.label}
            </div>
          )}
        </header>

        <div className="chat-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <Sparkles size={32} color="var(--accent)" />
              </div>
              <h2>Welcome to Modular RAG</h2>
              <p>Select a mode with the <strong>+</strong> button in the chat bar below, then start typing.</p>

              <div className="empty-state-guide">
                <div className="guide-card" onClick={() => { setActiveMode('vector_db'); textareaRef.current?.focus(); }}>
                  <Database className="guide-icon" size={24} style={{ color: MODES.vector_db.color }} />
                  <div className="guide-title">Query your Data</div>
                  <div className="guide-desc">Pin Vector DB mode from the + button and ask questions directly against your uploaded documents.</div>
                </div>

                <div className="guide-card" onClick={() => { setActiveMode('link_reader'); textareaRef.current?.focus(); }}>
                  <Globe className="guide-icon" size={24} style={{ color: MODES.link_reader.color }} />
                  <div className="guide-title">Analyse any Webpage</div>
                  <div className="guide-desc">Pin Webpage Link mode, paste any URL, and ask questions — I'll scrape and summarise it instantly.</div>
                </div>

                <div className="guide-card">
                  <MessageSquare className="guide-icon" size={24} style={{ color: 'var(--accent)' }} />
                  <div className="guide-title">Auto (Default)</div>
                  <div className="guide-desc">Leave the mode unpinned and the AI will automatically route each query to the best tool.</div>
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className="message-content">
                  <div className={`avatar ${msg.role === 'assistant' ? 'bot' : 'user'}`}>
                    {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                  </div>
                  <div className="message-text">
                    {/* Show mode chip on user messages */}
                    {msg.role === 'user' && msg.mode && msg.mode !== 'auto' && (
                      <div className="mode-chip" style={{ '--chip-color': MODES[msg.mode]?.color || 'var(--accent)' }}>
                        {msg.mode === 'vector_db' ? <Database size={11} /> : <Globe size={11} />}
                        {MODES[msg.mode]?.label}
                      </div>
                    )}
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    {msg.role === 'assistant' && msg.web_content && (
                      <div className="url-badge">
                        <LinkIcon size={14} /> Webpage loaded into context
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="message-row assistant">
              <div className="message-content">
                <div className="avatar bot"><Bot size={20} /></div>
                <div className="message-text">
                  <div className="typing-indicator">
                    <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Input area ─────────────────────────────────────────── */}
        <div className="input-area">
          <div className="input-wrapper">

            {/* Mode picker popup — only 2 options, no header */}
            {pickerOpen && (
              <div className="mode-picker" ref={pickerRef}>
                {Object.values(MODES).map(m => {
                  const Icon = m.icon;
                  const isSelected = activeMode === m.key;
                  return (
                    <button
                      key={m.key}
                      className={`mode-option ${isSelected ? 'selected' : ''}`}
                      style={{ '--opt-color': m.color }}
                      onClick={() => {
                        // Toggle: clicking the active one goes back to auto
                        setActiveMode(isSelected ? 'auto' : m.key);
                        setPickerOpen(false);
                        textareaRef.current?.focus();
                      }}
                    >
                      <div className="mode-option-icon"><Icon size={16} /></div>
                      <div className="mode-option-text">
                        <span className="mode-option-label">{m.label}</span>
                        <span className="mode-option-desc">{m.desc}</span>
                      </div>
                      {isSelected && <div className="mode-option-check">✓</div>}
                    </button>
                  );
                })}
              </div>
            )}

            <form onSubmit={handleSend} className="input-container">
              {/* Active mode indicator inside input */}
              {activeMode !== 'auto' && ModeIcon && (
                <div className="active-mode-chip" style={{ '--chip-color': modeColor }}>
                  <ModeIcon size={12} />
                  <span>{activeModeDef.label}</span>
                  <button type="button" onClick={() => setActiveMode('auto')} className="chip-remove" title="Reset to Auto">
                    <X size={10} />
                  </button>
                </div>
              )}

              <div className="input-row">
                {/* + button */}
                <button
                  type="button"
                  className={`plus-btn ${pickerOpen ? 'open' : ''}`}
                  onClick={() => setPickerOpen(p => !p)}
                  title="Choose mode"
                  style={{ '--mode-color': modeColor }}
                >
                  <Plus size={18} />
                </button>

                <textarea
                  ref={textareaRef}
                  className="chat-input"
                  placeholder={activeModeDef.placeholder}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
                  }}
                  rows={1}
                  disabled={isLoading}
                  autoFocus
                />

                <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
                  <Send size={18} />
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
