import { useState, useEffect, useMemo } from 'react';
import { createApi } from './api/permissions';
import { generateTokens, IDENTITIES, BASE_URL } from './auth';
import ManagementScreen from './components/ManagementScreen';
import UserScreen from './components/UserScreen';

export default function App() {
  const [tokens, setTokens] = useState(null);
  const [identity, setIdentity] = useState('admin');       // 'admin' | 'user'
  const [activeScreen, setActiveScreen] = useState('management'); // 'management' | 'my-permissions'

  useEffect(() => { generateTokens().then(setTokens); }, []);

  function handleIdentityChange(next) {
    setIdentity(next);
    if (next === 'user') setActiveScreen('my-permissions');
  }

  const api = useMemo(
    () => (tokens ? createApi(BASE_URL, tokens[identity]) : null),
    [tokens, identity]
  );

  const currentIdentity = IDENTITIES[identity];

  return (
    <div id="root">
      <header className="app-header">
        <div>
          <h1>Permissions Manager</h1>
          <div className="subtitle">{BASE_URL}</div>
        </div>
        {currentIdentity && (
          <div className="identity-pill">
            <span className={`role-badge ${identity}`}>{currentIdentity.role}</span>
            <div>
              <div><strong>{currentIdentity.sub}</strong></div>
              <div className="id-meta">tenant: {currentIdentity.tenant_id}</div>
            </div>
          </div>
        )}
      </header>

      <main className="main-content">

        {/* ── Identity selector ── */}
        <div className="identity-selector card">
          <span className="selector-label">Demo Identity</span>
          <div className="selector-options">
            <button
              className={`selector-btn ${identity === 'admin' ? 'active admin' : ''}`}
              onClick={() => handleIdentityChange('admin')}
            >
              <span className={`role-badge admin`}>admin</span>
              Admin
            </button>
            <button
              className={`selector-btn ${identity === 'user' ? 'active user' : ''}`}
              onClick={() => handleIdentityChange('user')}
            >
              <span className={`role-badge user`}>user</span>
              Regular User
            </button>
          </div>
        </div>

        {/* ── Tabs (admin only) ── */}
        {identity === 'admin' && (
          <div className="tab-bar">
            <button
              className={`tab-btn ${activeScreen === 'management' ? 'active' : ''}`}
              onClick={() => setActiveScreen('management')}
            >
              Management
            </button>
            <button
              className={`tab-btn ${activeScreen === 'my-permissions' ? 'active' : ''}`}
              onClick={() => setActiveScreen('my-permissions')}
            >
              My Active Permissions
            </button>
          </div>
        )}

        {/* ── Screens ── */}
        {!api && (
          <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
            Generating tokens…
          </div>
        )}

        {api && identity === 'admin' && activeScreen === 'management' && (
          <ManagementScreen api={api} />
        )}
        {api && (identity === 'user' || activeScreen === 'my-permissions') && (
          <UserScreen api={api} identity={currentIdentity} />
        )}

      </main>
    </div>
  );
}
