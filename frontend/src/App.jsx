import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User, Link as LinkIcon, Menu, Plus, MessageSquare, Sun, Moon, Sparkles, Trash2 } from 'lucide-react';
import './index.css';

function App() {
  const [sessions, setSessions] = useState([
    {
      id: 1,
      title: "New Conversation",
      messages: []
    }
  ]);
  const [currentSessionId, setCurrentSessionId] = useState(1);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Theme management map true = dark, false = light
  const [isDarkTheme, setIsDarkTheme] = useState(true);

  const messagesEndRef = useRef(null);

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
  }, [isDarkTheme]);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const createNewChat = () => {
    const newId = Date.now();
    setSessions([{ id: newId, title: "New Conversation", messages: [] }, ...sessions]);
    setCurrentSessionId(newId);
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false);
    }
  };

  const selectSession = (id) => {
    setCurrentSessionId(id);
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false);
    }
  };

  const deleteSession = (e, id) => {
    e.stopPropagation(); // Prevent the session from being selected when clicking delete

    const updatedSessions = sessions.filter(s => s.id !== id);

    if (updatedSessions.length === 0) {
      // If we deleted the last chat, create a brand new empty one
      const newId = Date.now();
      setSessions([{ id: newId, title: "New Conversation", messages: [] }]);
      setCurrentSessionId(newId);
    } else {
      setSessions(updatedSessions);
      // If we deleted the currently active chat, jump to the first available one
      if (currentSessionId === id) {
        setCurrentSessionId(updatedSessions[0].id);
      }
    }
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input.trim();
    setInput('');

    // Auto-generate title for new chats
    let updatedSessions = [...sessions];
    const sessionIndex = updatedSessions.findIndex(s => s.id === currentSessionId);

    if (updatedSessions[sessionIndex].messages.length === 0) {
      updatedSessions[sessionIndex].title = userQuery.slice(0, 30) + (userQuery.length > 30 ? '...' : '');
    }

    const newMessages = [...updatedSessions[sessionIndex].messages, { role: 'user', content: userQuery }];
    updatedSessions[sessionIndex].messages = newMessages;
    setSessions(updatedSessions);
    setIsLoading(true);

    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          chat_history: newMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content })),
          web_content: [...newMessages].reverse().find(m => m.web_content)?.web_content || ""
        })
      });

      if (!response.ok) throw new Error(`Server Error`);

      const data = await response.json();

      const sessionIndexAfter = sessions.findIndex(s => s.id === currentSessionId);
      let newSessions = [...sessions];
      newSessions[sessionIndexAfter].messages = [
        ...newSessions[sessionIndexAfter].messages,
        { role: 'assistant', content: data.answer, web_content: data.web_content }
      ];
      setSessions(newSessions);

    } catch (err) {
      console.error(err);
      let newSessions = [...sessions];
      newSessions[sessionIndex].messages = [
        ...newSessions[sessionIndex].messages,
        { role: 'assistant', content: "Error: Failed to reach the RAG backend. Is the Python API running?" }
      ];
      setSessions(newSessions);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-layout">
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
              <button
                className="delete-chat-btn"
                onClick={(e) => deleteSession(e, session.id)}
                title="Delete Chat"
              >
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

      {/* Main Content Area */}
      <div className="main-content">
        <header className="header">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="icon-btn">
            <Menu size={20} />
          </button>
          <div className="header-title">Modular RAG</div>
        </header>

        <div className="chat-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <Sparkles size={32} color="var(--accent)" />
              </div>
              <h2>How can I help you today?</h2>
              <p>Ask a question about your VectorDB or paste a URL to analyze.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className="message-content">
                  <div className={`avatar ${msg.role}`}>
                    {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                  </div>
                  <div className="message-text">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                    {msg.role === 'assistant' && msg.web_content && msg.content.includes('HTML content of the webpage') && (
                      <div className="url-badge">
                        <LinkIcon size={14} /> Webpage loaded into Context Window
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
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <form onSubmit={handleSend} className="input-container">
            <textarea
              className="chat-input"
              placeholder="Message Modular RAG..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              rows={1}
              disabled={isLoading}
              autoFocus
            />
            <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
