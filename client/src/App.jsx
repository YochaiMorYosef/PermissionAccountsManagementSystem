import { useState, useEffect, useMemo } from 'react';
import { createApi } from './api/permissions';
import { generateTokens, IDENTITIES, BASE_URL } from './auth';
import ManagementScreen from './components/ManagementScreen';
import UserScreen from './components/UserScreen';

export default function App() {
  const [tokens, setTokens] = useState(null);
  const [activeTab, setActiveTab] = useState('admin');

  useEffect(() => {
    generateTokens().then(setTokens);
  }, []);

  const api = useMemo(
    () => (tokens ? createApi(BASE_URL, tokens[activeTab]) : null),
    [tokens, activeTab]
  );

  const identity = IDENTITIES[activeTab];

  return (
    <div id="root">
      <header className="app-header">
        <div>
          <h1>Permissions Manager</h1>
          <div className="subtitle">{BASE_URL}</div>
        </div>
        {identity && (
          <div className="identity-pill">
            <span className={`role-badge ${activeTab}`}>{identity.role}</span>
            <div>
              <div><strong>{identity.sub}</strong></div>
              <div className="id-meta">tenant: {identity.tenant_id}</div>
            </div>
          </div>
        )}
      </header>

      <main className="main-content">
        <div className="tab-bar">
          <button
            className={`tab-btn ${activeTab === 'admin' ? 'active admin' : ''}`}
            onClick={() => setActiveTab('admin')}
          >
            <span className="tab-dot" />
            Admin
            <span className="role-badge admin" style={{ marginLeft: 4 }}>admin</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'user' ? 'active user' : ''}`}
            onClick={() => setActiveTab('user')}
          >
            <span className="tab-dot" />
            User
            <span className="role-badge user" style={{ marginLeft: 4 }}>user</span>
          </button>
        </div>

        {!api && (
          <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
            <div className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)', marginBottom: 8 }} />
            <div>Generating tokens…</div>
          </div>
        )}

        {api && activeTab === 'admin' && <ManagementScreen api={api} />}
        {api && activeTab === 'user'  && <UserScreen api={api} identity={identity} />}
      </main>
    </div>
  );
}
