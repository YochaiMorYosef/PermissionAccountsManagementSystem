import { useState, useEffect, useCallback } from 'react';
import PermissionForm from './PermissionForm';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

function formatSchedule(schedule) {
  if (!schedule?.length) return <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>always active</span>;
  return schedule.map((e, i) => (
    <span key={i} style={{ display: 'block', fontSize: 12, whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
      {WEEKDAYS[e.weekday]} · {e.start_time}–{e.end_time}
    </span>
  ));
}

function shortId(id = '') {
  return <span title={id}>{id.slice(0, 8)}…</span>;
}

export default function ManagementScreen({ api }) {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formMode, setFormMode] = useState(null); // null | 'create' | <permission object>

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listPermissions();
      setPermissions(data ?? []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  async function handleDelete(perm) {
    if (!window.confirm(`Delete permission ${perm.permission_id}?`)) return;
    try {
      await api.deletePermission(perm.permission_id);
      fetchAll();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleFormSubmit(payload) {
    if (formMode === 'create') {
      await api.createPermission(payload);
    } else {
      await api.updatePermission(formMode.permission_id, payload);
    }
    setFormMode(null);
    fetchAll();
  }

  return (
    <div>
      {/* Create / Edit form */}
      {formMode !== null && (
        <div className="card">
          <div className="card-title">
            {formMode === 'create' ? '+ New Permission' : `Edit · ${shortId(formMode.permission_id)}`}
          </div>
          <PermissionForm
            initial={formMode === 'create' ? null : formMode}
            onSubmit={handleFormSubmit}
            onCancel={() => setFormMode(null)}
          />
        </div>
      )}

      {/* Table card */}
      <div className="card">
        <div className="toolbar">
          <div className="card-title" style={{ marginBottom: 0 }}>
            Permissions
            <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-muted)' }}>
              ({permissions.length})
            </span>
          </div>
          <div className="toolbar-actions">
            <button className="btn btn-ghost btn-sm" onClick={fetchAll} disabled={loading}>Refresh</button>
            <button className="btn btn-primary btn-sm" onClick={() => setFormMode('create')}>+ New</button>
          </div>
        </div>

        {error && <div className="msg-error">{error}</div>}

        {loading ? (
          <div className="msg-empty">
            <span className="spinner" style={{ width: 24, height: 24, borderColor: 'var(--border)', borderTopColor: 'var(--primary)' }} />
            <div style={{ marginTop: 10 }}>Loading permissions…</div>
          </div>
        ) : permissions.length === 0 ? (
          <div className="msg-empty">
            <div className="empty-icon">🔑</div>
            No permissions found. Create one to get started.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Account</th>
                  <th>Permission</th>
                  <th>Status</th>
                  <th>Schedule</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {permissions.map((p) => (
                  <tr key={p.permission_id}>
                    <td className="id-cell">{shortId(p.permission_id)}</td>
                    <td><strong>{p.user}</strong></td>
                    <td>{p.account_id}</td>
                    <td><code>{p.permission}</code></td>
                    <td><span className={`badge badge-${p.status}`}>{p.status}</span></td>
                    <td>{formatSchedule(p.schedule)}</td>
                    <td>
                      <div className="actions">
                        <button className="btn btn-sm" onClick={() => setFormMode(p)}>Edit</button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(p)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
