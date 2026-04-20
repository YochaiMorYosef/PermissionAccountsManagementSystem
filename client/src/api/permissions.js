export function createApi(baseUrl, token) {
  const base = baseUrl.replace(/\/$/, '');
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  async function request(path, options = {}) {
    const res = await fetch(`${base}${path}`, { ...options, headers });
    if (res.status === 204) return null;
    const body = await res.json();
    if (!res.ok) {
      throw new Error(body?.error?.message || `${res.status} ${res.statusText}`);
    }
    return body.data;
  }

  return {
    listPermissions({ limit = 50, cursor } = {}) {
      const params = new URLSearchParams({ limit });
      if (cursor) params.set('cursor', cursor);
      return request(`/permissions?${params}`);
    },

    getPermission(id) {
      return request(`/permissions/${id}`);
    },

    createPermission(data) {
      return request('/permissions', { method: 'POST', body: JSON.stringify(data) });
    },

    updatePermission(id, data) {
      return request(`/permissions/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
    },

    deletePermission(id) {
      return request(`/permissions/${id}`, { method: 'DELETE' });
    },

    getMyPermissions(accountId) {
      return request(`/permissions/me?account_id=${encodeURIComponent(accountId)}`);
    },
  };
}
