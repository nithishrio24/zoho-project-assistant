import React from 'react'
import './LoginButton.css'

function LoginButton() {
  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/auth/login'
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>🚀 Zoho Project Chatbot</h1>
        <p className="subtitle">Powered by AI - Manage Your Projects Effortlessly</p>
        
        <div className="features">
          <div className="feature-item">
            <span className="feature-icon">📋</span>
            <span>View Projects & Tasks</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">✏️</span>
            <span>Create & Update Tasks</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">👥</span>
            <span>Manage Team Members</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📊</span>
            <span>Track Progress</span>
          </div>
        </div>

        <button onClick={handleLogin} className="login-btn">
          <img src="https://www.zoho.com/favicon.ico" alt="Zoho" className="zoho-icon" />
          Login with Zoho
        </button>

        <p className="privacy-notice">
          By logging in, you agree to connect your Zoho Projects account
        </p>
      </div>
    </div>
  )
}

export default LoginButton
