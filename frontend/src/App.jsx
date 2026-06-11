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
    const params = new URLSearchParams(window.location.search);
    const t = params.get("token");
    if (t) {
      localStorage.setItem("token", t);
      setToken(t);
      window.history.replaceState({}, "", "/");
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
      setMessages((prev) => [...prev, { role: "bot", content: res.data.response }]);
      setAwaitingConfirmation(res.data.awaiting_confirmation);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === "string" ? detail : err.response?.status === 404 ? "API route not found — is the backend running on port 8000?" : "Backend not connected yet.";
      setMessages((prev) => [...prev, { role: "bot", content: msg }]);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",width:"100vw",background:"#0a0a0a",margin:0,padding:0,overflow:"hidden"}}>
        <div style={{background:"#111111",padding:"48px",borderRadius:"12px",textAlign:"center",border:"1px solid #222222",maxWidth:"400px"}}>
          <h1 style={{color:"#F5C518",marginBottom:"8px",fontSize:"28px",fontWeight:"700"}}>Project Assistant</h1>
          <p style={{color:"#888888",marginBottom:"32px",fontSize:"14px"}}>AI-powered project management</p>
          <button
            onClick={() => window.location.href = `${API}/auth/login`}
            style={{background:"#F5C518",color:"#000000",border:"none",padding:"14px 32px",borderRadius:"8px",fontSize:"16px",cursor:"pointer",fontWeight:"600",transition:"background 0.2s",width:"100%"}}
            onMouseEnter={(e) => e.target.style.background = "#d4a800"}
            onMouseLeave={(e) => e.target.style.background = "#F5C518"}
          >
            Login with Zoho
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{display:"flex",flexDirection:"column",height:"100vh",width:"100vw",background:"#0a0a0a",fontFamily:"'Inter', 'Segoe UI', sans-serif",margin:0,padding:0,overflow:"hidden"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"20px 24px",background:"#111111",borderBottom:"1px solid #333333",boxShadow:"0 2px 4px rgba(245, 197, 24, 0.05)",flexShrink:0}}>
        <span style={{color:"#F5C518",fontSize:"20px",fontWeight:"600"}}>Project Assistant</span>
        <button onClick={() => { localStorage.removeItem("token"); setToken(null); }} style={{background:"transparent",color:"#F5C518",border:"1px solid #F5C518",padding:"8px 16px",borderRadius:"6px",cursor:"pointer",fontSize:"13px",fontWeight:"500",transition:"all 0.2s"}} onMouseEnter={(e) => {e.target.style.background="rgba(245, 197, 24, 0.1)"; e.target.style.borderColor="#d4a800"}} onMouseLeave={(e) => {e.target.style.background="transparent"; e.target.style.borderColor="#F5C518"}}>Logout</button>
      </div>
      <div style={{flex:1,overflowY:"auto",padding:"20px 24px",display:"flex",flexDirection:"column",gap:"12px",width:"100%"}}>
        {messages.length === 0 && <div style={{color:"#666666",textAlign:"center",marginTop:"40px",fontSize:"14px"}}>Hello! How can I assist you with your projects today?</div>}
        {messages.map((msg, i) => (
          <div key={i} style={{maxWidth:"70%",padding:"12px 16px",borderRadius:"12px",alignSelf:msg.role==="user"?"flex-end":"flex-start",background:msg.role==="user"?"#F5C518":"#1a1a1a",color:msg.role==="user"?"#000000":"#ffffff",border:msg.role==="user"?"none":"1px solid #333333",boxShadow:"0 1px 3px rgba(245, 197, 24, 0.08)"}}>
            {msg.content}
          </div>
        ))}
        {loading && <div style={{maxWidth:"70%",padding:"12px 16px",borderRadius:"12px",background:"#1a1a1a",color:"#888888"}}>Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      {awaitingConfirmation ? (
        <div style={{display:"flex",alignItems:"center",gap:"12px",padding:"16px 24px",background:"#111111",borderTop:"1px solid #333333",flexShrink:0}}>
          <p style={{color:"#ffffff",margin:0,fontSize:"14px"}}>Confirm this action?</p>
          <button onClick={() => sendMessage("yes")} style={{background:"#F5C518",color:"#000000",border:"none",padding:"10px 20px",borderRadius:"8px",cursor:"pointer",fontWeight:"600",transition:"background 0.2s"}} onMouseEnter={(e) => e.target.style.background="#d4a800"} onMouseLeave={(e) => e.target.style.background="#F5C518"}>Confirm</button>
          <button onClick={() => { sendMessage("no"); setAwaitingConfirmation(false); }} style={{background:"#333333",color:"#ffffff",border:"1px solid #555555",padding:"10px 20px",borderRadius:"8px",cursor:"pointer",fontWeight:"600",transition:"all 0.2s"}} onMouseEnter={(e) => {e.target.style.background="#444444"}} onMouseLeave={(e) => {e.target.style.background="#333333"}}>Cancel</button>
        </div>
      ) : (
        <div style={{display:"flex",gap:"12px",padding:"16px 24px",background:"#111111",borderTop:"1px solid #333333",flexShrink:0,width:"100%",boxSizing:"border-box"}}>
          <input
            style={{flex:1,padding:"12px 16px",borderRadius:"8px",border:"1px solid #333333",background:"#1a1a1a",color:"#ffffff",fontSize:"14px",outline:"none",transition:"all 0.2s"}}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key==="Enter" && sendMessage(input)}
            onFocus={(e) => {e.target.style.borderColor="#F5C518"; e.target.style.boxShadow="0 0 0 3px rgba(245, 197, 24, 0.1)"}}
            onBlur={(e) => {e.target.style.borderColor="#333333"; e.target.style.boxShadow="none"}}
            placeholder="Ask about your projects or tasks..."
            disabled={loading}
          />
          <button onClick={() => sendMessage(input)} disabled={loading} style={{background:"#F5C518",color:"#000000",border:"none",padding:"12px 24px",borderRadius:"8px",cursor:"pointer",fontSize:"14px",fontWeight:"600",transition:"all 0.2s",opacity:loading ? 0.6 : 1}} onMouseEnter={(e) => !loading && (e.target.style.background="#d4a800")} onMouseLeave={(e) => !loading && (e.target.style.background="#F5C518")}>Send</button>
        </div>
      )}
    </div>
  );
}