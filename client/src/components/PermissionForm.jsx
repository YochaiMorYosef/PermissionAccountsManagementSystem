import { useState } from 'react';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const emptyEntry = () => ({ weekday: 0, start_time: '09:00', end_time: '17:00' });

export default function PermissionForm({ initial = null, onSubmit, onCancel }) {
  const isEdit = Boolean(initial);

  const [user, setUser] = useState(initial?.user ?? '');
  const [accountId, setAccountId] = useState(initial?.account_id ?? '');
  const [permission, setPermission] = useState(initial?.permission ?? '');
  const [entries, setEntries] = useState(initial?.schedule ?? []);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function addEntry() { setEntries((prev) => [...prev, emptyEntry()]); }
  function removeEntry(i) { setEntries((prev) => prev.filter((_, idx) => idx !== i)); }
  function updateEntry(i, field, value) {
    setEntries((prev) =>
      prev.map((e, idx) =>
        idx === i ? { ...e, [field]: field === 'weekday' ? Number(value) : value } : e
      )
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const payload = {
      user,
      account_id: accountId,
      permission,
      schedule: entries.length ? entries : null,
    };
    if (!isEdit && !entries.length) delete payload.schedule;
    try {
      await onSubmit(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="msg-error">{error}</div>}

      <div className="form-grid">
        <div className="form-field">
          <label>User *</label>
          <input required value={user} onChange={(e) => setUser(e.target.value)} placeholder="alice" />
        </div>
        <div className="form-field">
          <label>Account ID *</label>
          <input required value={accountId} onChange={(e) => setAccountId(e.target.value)} placeholder="account-123" />
        </div>
        <div className="form-field">
          <label>Permission *</label>
          <input required value={permission} onChange={(e) => setPermission(e.target.value)} placeholder="read" />
        </div>
      </div>

      <div className="schedule-section">
        <div className="schedule-label">
          <span>Schedule <span style={{ fontWeight: 400 }}>(leave empty for always-active)</span></span>
          <button type="button" className="btn btn-sm btn-ghost" onClick={addEntry}>+ Add time window</button>
        </div>

        {entries.map((entry, i) => (
          <div className="schedule-entry" key={i}>
            <span>Day</span>
            <select value={entry.weekday} onChange={(e) => updateEntry(i, 'weekday', e.target.value)}>
              {WEEKDAYS.map((d, idx) => <option key={idx} value={idx}>{d}</option>)}
            </select>
            <span>Start</span>
            <input
              type="text"
              pattern="\d{2}:\d{2}"
              placeholder="09:00"
              value={entry.start_time}
              onChange={(e) => updateEntry(i, 'start_time', e.target.value)}
            />
            <span>End</span>
            <input
              type="text"
              pattern="\d{2}:\d{2}"
              placeholder="17:00"
              value={entry.end_time}
              onChange={(e) => updateEntry(i, 'end_time', e.target.value)}
            />
            <button type="button" className="btn btn-sm btn-danger" onClick={() => removeEntry(i)}>✕</button>
          </div>
        ))}
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? <><span className="spinner" />{isEdit ? 'Saving…' : 'Creating…'}</> : isEdit ? 'Save changes' : 'Create permission'}
        </button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
