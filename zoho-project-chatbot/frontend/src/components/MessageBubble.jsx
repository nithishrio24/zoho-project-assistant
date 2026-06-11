import React from 'react'
import './MessageBubble.css'

function MessageBubble({ message }) {
  const { type, content, isError } = message

  return (
    <div className={`message ${type}-message ${isError ? 'error' : ''}`}>
      <div className="message-content">
        {content}
      </div>
    </div>
  )
}

export default MessageBubble
