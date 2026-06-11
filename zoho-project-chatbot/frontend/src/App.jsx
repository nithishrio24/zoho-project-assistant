import { useState, useEffect, useRef } from "react";
import axios from "axios";

const API = "http://localhost:8000";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const bottomRef = useRef(null);

  useEffect(() => {
    // Check if token came back from OAuth redirect
    const params = new URLSearchParams(window.location.search);
    const t = params.get("token");
    console.log("App.jsx useEffect: checking for token in URL...");
    console.log("Current URL:", window.location.href);
    console.log("Query params:", window.location.search);
    if (t) {
      console.log("✓ Token found in URL, storing in localStorage and state");
      localStorage.setItem("token", t);
      setToken(t);
      window.history.replaceState({}, "", "/");
      console.log("✓ Token stored and URL cleaned");
    } else {
      console.log("✗ No token in URL");
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(
        `${API}/chat`,
        { user_message: text, session_id: sessionId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const botMsg = { role: "bot", content: res.data.response };
      setMessages((prev) => [...prev, botMsg]);
      setAwaitingConfirmation(res.data.awaiting_confirmation);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "Error connecting to server. Is backend running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = () => {
    window.location.href = `${API}/auth/login`;
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setMessages([]);
  };

  // ---- LOGIN PAGE ----
  if (!token) {
    return (
      <div style={styles.loginPage}>
        <div style={styles.loginCard}>
          <h1 style={styles.loginTitle}>Project Assistant</h1>
          <p style={styles.loginSubtitle}>AI-powered project management</p>
          <button onClick={handleLogin} style={styles.loginBtn}>
            Login with Zoho
          </button>
        </div>
      </div>
    );
  }

  // ---- CHAT PAGE ----
  return (
    <div style={styles.chatPage}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.headerTitle}>Project Assistant</span>
        <button onClick={handleLogout} style={styles.logoutBtn}>Logout</button>
      </div>

      {/* Messages */}
      <div style={styles.messageArea}>
        {messages.length === 0 && (
          <div style={styles.placeholder}>
            Hello! How can I assist you with your projects today?
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              ...styles.bubble,
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              background: msg.role === "user" ? "#F5C518" : "#1a1a1a",
              color: msg.role === "user" ? "#000000" : "#ffffff",
              border: msg.role === "user" ? "none" : "1px solid #333333",
            }}
          >
            <span style={styles.roleLabel}>
              {msg.role === "user" ? "You" : "Bot"}
            </span>
            <p style={{ margin: 0 }}>{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div style={{ ...styles.bubble, background: "#1e1e2e", color: "#aaa" }}>
            <span style={styles.roleLabel}>Bot</span>
            <p style={{ margin: 0 }}>Thinking...</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input or Confirmation Buttons */}
      {awaitingConfirmation ? (
        <div style={styles.confirmBar}>
          <p style={{ color: "#fff", margin: 0 }}>Confirm this action?</p>
          <button
            onClick={() => sendMessage("yes")}
            style={styles.confirmBtn}
          >
            Confirm
          </button>
          <button
            onClick={() => { sendMessage("no"); setAwaitingConfirmation(false); }}
            style={styles.cancelBtn}
          >
            Cancel
          </button>
        </div>
      ) : (
        <div style={styles.inputBar}>
          <input
            style={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
            placeholder="Ask about your projects or tasks..."
            disabled={loading}
          />
          <button
            onClick={() => sendMessage(input)}
            style={styles.sendBtn}
            disabled={loading}
          >
            Send
          </button>
        </div>
      )}
    </div>
  );
}

// ---- STYLES ----
const styles = {
  loginPage: {
    display: "flex", alignItems: "center", justifyContent: "center",
    height: "100vh", background: "#0a0a0a", fontFamily: "'Inter', 'Segoe UI', sans-serif",
  },
  loginCard: {
    background: "#111111", padding: "48px", borderRadius: "12px",
    textAlign: "center", boxShadow: "0 4px 12px rgba(245,197,24,0.15)", maxWidth: "400px", border: "1px solid #333333",
  },
  loginTitle: { color: "#F5C518", fontSize: "28px", marginBottom: "8px", fontWeight: "600", margin: "0 0 8px 0" },
  loginSubtitle: { color: "#999999", marginBottom: "32px", fontSize: "14px", margin: "0 0 32px 0" },
  loginBtn: {
    background: "#F5C518", color: "#000000", border: "none",
    padding: "12px 32px", borderRadius: "8px", fontSize: "16px", fontWeight: "600",
    cursor: "pointer", transition: "all 0.2s", width: "100%",
  },
  chatPage: {
    display: "flex", flexDirection: "column", height: "100vh",
    background: "#0a0a0a", fontFamily: "'Inter', 'Segoe UI', sans-serif",
  },
  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "16px 24px", background: "#111111", borderBottom: "1px solid #333333",
  },
  headerTitle: { color: "#F5C518", fontSize: "18px", fontWeight: "600", letterSpacing: "-0.5px" },
  logoutBtn: {
    background: "transparent", color: "#F5C518", border: "1px solid #F5C518",
    padding: "8px 16px", borderRadius: "6px", cursor: "pointer", fontSize: "13px", fontWeight: "500", transition: "all 0.2s",
  },
  messageArea: {
    flex: 1, overflowY: "auto", padding: "20px 24px",
    display: "flex", flexDirection: "column", gap: "12px", background: "#0a0a0a",
  },
  placeholder: { color: "#F5C518", textAlign: "center", marginTop: "40px", fontSize: "14px", border: "1px solid #F5C518", padding: "16px", borderRadius: "8px", background: "#1a1a1a" },
  bubble: {
    maxWidth: "70%", padding: "12px 16px",
    borderRadius: "12px", display: "flex", flexDirection: "column", gap: "4px", boxShadow: "0 1px 3px rgba(245,197,24,0.1)",
  },
  roleLabel: { fontSize: "11px", color: "#999999", textTransform: "uppercase", fontWeight: "500" },
  inputBar: {
    display: "flex", gap: "12px", padding: "16px 24px",
    background: "#111111", borderTop: "1px solid #333333",
  },
  input: {
    flex: 1, padding: "12px 16px", borderRadius: "8px",
    border: "1px solid #333333", background: "#1a1a1a",
    color: "#ffffff", fontSize: "14px", outline: "none", fontFamily: "inherit",
  },
  sendBtn: {
    background: "#F5C518", color: "#000000", border: "none",
    padding: "12px 24px", borderRadius: "8px", cursor: "pointer", fontSize: "14px", fontWeight: "600", transition: "all 0.2s",
  },
  confirmBar: {
    display: "flex", alignItems: "center", gap: "12px",
    padding: "16px 24px", background: "#111111", borderTop: "1px solid #333333",
  },
  confirmBtn: {
    background: "#059669", color: "#fff", border: "none",
    padding: "10px 20px", borderRadius: "8px", cursor: "pointer", fontSize: "14px", fontWeight: "500", transition: "all 0.2s",
  },
  cancelBtn: {
    background: "#dc2626", color: "#fff", border: "none",
    padding: "10px 20px", borderRadius: "8px", cursor: "pointer", fontSize: "14px", fontWeight: "500", transition: "all 0.2s",
  },
};