import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import MessageBubble from './MessageBubble'
import './ChatWindow.css'

function ChatWindow({ token, onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef(null)

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (messageText = input) => {
    if (!messageText.trim()) return

    const userMessage = { type: 'user', content: messageText }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post(
        `${API_BASE}/chat`,
        {
          user_message: messageText,
          session_id: sessionId,
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      const botMessage = {
        type: 'bot',
        content: response.data.response,
      }
      setMessages(prev => [...prev, botMessage])
      setAwaitingConfirmation(response.data.awaiting_confirmation)
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        type: 'bot',
        content: 'Sorry, I encountered an error. Please try again.',
        isError: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = () => {
    sendMessage('yes')
  }

  const handleCancel = () => {
    sendMessage('no')
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Project Assistant</h1>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {loading && (
          <div className="message bot-message">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        {awaitingConfirmation ? (
          <div className="confirmation-buttons">
            <button 
              onClick={handleConfirm} 
              className="confirm-btn"
              disabled={loading}
            >
              Confirm
            </button>
            <button 
              onClick={handleCancel} 
              className="cancel-btn"
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me about your projects, tasks, or team..."
              disabled={loading}
              className="chat-input"
            />
            <button 
              type="submit" 
              disabled={loading || !input.trim()}
              className="send-btn"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default ChatWindow
