import React from 'react';

export default function AuthScreen({
  isLoginView,
  setIsLoginView,
  email,
  setEmail,
  password,
  setPassword,
  name,
  setName,
  role,
  setRole,
  authError,
  onSubmit
}) {
  return (
    <div className="auth-wrapper">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="logo-section" style={{ justifyContent: 'center' }}>
          <img src="https://img.icons8.com/nolan/96/airplane-take-off.png" className="logo-img" alt="Logo" />
          <h1 className="logo-text">DevPilot AI</h1>
        </div>
        <h2 style={{ textAlign: 'center', fontFamily: 'Space Grotesk' }}>
          {isLoginView ? 'Welcome Back' : 'Create Account'}
        </h2>
        {authError && (
          <div style={{ color: 'var(--danger)', fontSize: '0.9rem', textAlign: 'center' }}>
            {authError}
          </div>
        )}
        
        {!isLoginView && (
          <>
            <input 
              type="text" 
              placeholder="Full Name" 
              className="text-input" 
              value={name} 
              onChange={(e) => setName(e.target.value)} 
              required 
            />
            <select className="select-box" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="developer">Developer</option>
              <option value="lead_engineer">Lead Engineer</option>
              <option value="project_manager">Project Manager</option>
            </select>
          </>
        )}

        <input 
          type="email" 
          placeholder="Email Address" 
          className="text-input" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
        />
        <input 
          type="password" 
          placeholder="Password" 
          className="text-input" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
        />

        <button className="btn" type="submit">
          {isLoginView ? 'Sign In' : 'Sign Up'}
        </button>
        
        <button 
          type="button" 
          className="btn btn-secondary" 
          onClick={() => setIsLoginView(!isLoginView)}
        >
          {isLoginView ? 'Need an account? Sign Up' : 'Already have an account? Sign In'}
        </button>
      </form>
    </div>
  );
}
