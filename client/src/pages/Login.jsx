import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Zap, Copy, Check } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [copiedPwd, setCopiedPwd] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'id') {
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    } else {
      setCopiedPwd(true);
      setTimeout(() => setCopiedPwd(false), 2000);
    }
  };

  return (
    <div className="auth-page" id="login-page">
      <div className="auth-card">
        <div className="auth-header">
          <h1 style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
            <Zap size={28} />
            <span>FreelanceFlow</span>
          </h1>
          <p>Welcome back! Sign in to your account.</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="form-error">{error}</div>}
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={loading} id="login-submit">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="auth-footer">
          Don't have an account? <Link to="/register">Register</Link>
        </p>

        <div className="demo-credentials" style={{ marginTop: '24px', padding: '16px', borderRadius: '8px', border: '1px dashed var(--border-color)', background: 'var(--bg-card)' }}>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '12px', textAlign: 'center', fontWeight: '500' }}>Reviewer Demo Login</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)', padding: '8px 12px', borderRadius: '4px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Username</span>
                <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>reviewer</span>
              </div>
              <button 
                onClick={() => copyToClipboard('reviewer', 'id')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: copiedId ? '#22c55e' : 'var(--text-muted)' }}
                title="Copy Username"
                type="button"
              >
                {copiedId ? <Check size={18} /> : <Copy size={18} />}
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-elevated)', padding: '8px 12px', borderRadius: '4px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Password</span>
                <span style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>demo123</span>
              </div>
              <button 
                onClick={() => copyToClipboard('demo123', 'pwd')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: copiedPwd ? '#22c55e' : 'var(--text-muted)' }}
                title="Copy Password"
                type="button"
              >
                {copiedPwd ? <Check size={18} /> : <Copy size={18} />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
