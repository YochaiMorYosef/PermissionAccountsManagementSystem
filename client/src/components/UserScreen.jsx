import { useState } from 'react';

export default function UserScreen({ api, identity }) {
  const [accountId, setAccountId] = useState('');
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFetch(e) {
    e.preventDefault();
    const trimmed = accountId.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    setPermissions(null);
    try {
      const data = await api.getMyPermissions(trimmed);
      setPermissions(data ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="card">
        <div className="card-title">My Active Permissions</div>

        <div className="info-bar">
          Fetching permissions for
          <strong>{identity.sub}</strong>
          on tenant
          <strong>{identity.tenant_id}</strong>
          — only <span className={`badge badge-Active`}>Active</span> permissions
          matching the current time window are returned.
        </div>

        <form onSubmit={handleFetch}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <div className="form-field" style={{ flex: 1, maxWidth: 360 }}>
              <label>Account ID *</label>
              <input
                required
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                placeholder="e.g. account-123"
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <><span className="spinner" />Loading…</> : 'Fetch'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="card">
          <div className="msg-error">{error}</div>
        </div>
      )}

      {permissions !== null && !error && (
        <div className="card">
          <div className="card-title">
            Active permissions on <code>{accountId}</code>
          </div>

          {permissions.length === 0 ? (
            <div className="msg-empty">
              <div className="empty-icon">🔒</div>
              No active permissions found for this account.
            </div>
          ) : (
            <ul className="perm-list">
              {permissions.map((p, i) => (
                <li key={i}>
                  <span>✓</span> {p}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
