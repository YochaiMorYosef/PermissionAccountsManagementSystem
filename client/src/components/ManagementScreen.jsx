import { useState, useEffect, useCallback, useRef } from 'react';
import PermissionForm from './PermissionForm';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const PAGE_SIZE = 50;

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
  const [nextCursor, setNextCursor] = useState(null);
  const [loading, setLoading] = useState(false);      // initial load
  const [loadingMore, setLoadingMore] = useState(false); // subsequent pages
  const [error, setError] = useState(null);
  const [formMode, setFormMode] = useState(null);
  const sentinelRef = useRef(null);

  // ── Fetch a page and either replace or append ──────────────────────────
  const fetchPage = useCallback(async (cursor, append) => {
    append ? setLoadingMore(true) : setLoading(true);
    setError(null);
    try {
      const { items, next_cursor } = await api.listPermissions({ limit: PAGE_SIZE, cursor });
      setPermissions(prev => append ? [...prev, ...(items ?? [])] : (items ?? []));
      setNextCursor(next_cursor ?? null);
    } catch (e) {
      setError(e.message);
    } finally {
      append ? setLoadingMore(false) : setLoading(false);
    }
  }, [api]);

  // Initial load
  useEffect(() => { fetchPage(null, false); }, [fetchPage]);

  // ── Infinite scroll via IntersectionObserver ───────────────────────────
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && nextCursor && !loadingMore) {
          fetchPage(nextCursor, true);
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [nextCursor, loadingMore, fetchPage]);

  // ── Optimistic delete ──────────────────────────────────────────────────
  async function handleDelete(perm) {
    if (!window.confirm(`Delete permission ${perm.permission_id}?`)) return;

    // Mark as Deleting immediately
    setPermissions(prev =>
      prev.map(p => p.permission_id === perm.permission_id ? { ...p, status: 'Deleting' } : p)
    );

    try {
      await api.deletePermission(perm.permission_id);
      setPermissions(prev => prev.filter(p => p.permission_id !== perm.permission_id));
    } catch (e) {
      // Revert on failure
      setPermissions(prev =>
        prev.map(p => p.permission_id === perm.permission_id ? { ...p, status: perm.status } : p)
      );
      setError(e.message);
    }
  }

  // ── Create / edit ──────────────────────────────────────────────────────
  async function handleFormSubmit(payload) {
    if (formMode === 'create') {
      const created = await api.createPermission(payload);
      setPermissions(prev => [created, ...prev]);
    } else {
      const updated = await api.updatePermission(formMode.permission_id, payload);
      setPermissions(prev =>
        prev.map(p => p.permission_id === formMode.permission_id ? updated : p)
      );
    }
    setFormMode(null);
  }

  return (
    <div>
      {/* Create / Edit form */}
      {formMode !== null && (
        <div className="card">
          <div className="card-title">
            {formMode === 'create' ? '+ New Permission' : `Edit -> ${permissions.find(p => p.permission_id === formMode.permission_id)?.user || ''}`}
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
              ({permissions.length}{nextCursor ? '+' : ''})
            </span>
          </div>
          <div className="toolbar-actions">
            <button className="btn btn-ghost btn-sm" onClick={() => fetchPage(null, false)} disabled={loading}>
              Refresh
            </button>
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
                  <tr key={p.permission_id} style={{ opacity: p.status === 'Deleting' ? 0.45 : 1, transition: 'opacity .2s' }}>
                    <td className="id-cell">{shortId(p.permission_id)}</td>
                    <td><strong>{p.user}</strong></td>
                    <td>{p.account_id}</td>
                    <td><code>{p.permission}</code></td>
                    <td><span className={`badge badge-${p.status}`}>{p.status}</span></td>
                    <td>{formatSchedule(p.schedule)}</td>
                    <td>
                      <div className="actions">
                        <button
                          className="btn btn-sm"
                          onClick={() => setFormMode(p)}
                          disabled={p.status === 'Deleting'}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => handleDelete(p)}
                          disabled={p.status === 'Deleting'}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Infinite scroll sentinel */}
            <div ref={sentinelRef} style={{ padding: '12px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              {loadingMore && (
                <>
                  <span className="spinner" style={{ borderColor: 'var(--border)', borderTopColor: 'var(--primary)', marginRight: 6 }} />
                  Loading more…
                </>
              )}
              {!loadingMore && !nextCursor && permissions.length > 0 && 'All permissions loaded'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
