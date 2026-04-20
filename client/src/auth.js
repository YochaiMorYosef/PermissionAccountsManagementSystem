export const BASE_URL = import.meta.env.VITE_BASE_URL;

const SECRET = 'secret';

export const IDENTITIES = {
  admin: { tenant_id: 'tenant-01', sub: 'user-020', role: 'admin' },
  user:  { tenant_id: 'tenant-01', sub: 'user-020', role: 'user'  },
};

function b64url(input) {
  const str = typeof input === 'string' ? input : JSON.stringify(input);
  return btoa(unescape(encodeURIComponent(str)))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

async function signHS256(payload) {
  const header  = b64url({ alg: 'HS256', typ: 'JWT' });
  const body    = b64url(payload);
  const message = `${header}.${body}`;

  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(SECRET),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(message));
  const sigB64 = btoa(String.fromCharCode(...new Uint8Array(sig)))
    .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');

  return `${message}.${sigB64}`;
}

export async function generateTokens() {
  const [admin, user] = await Promise.all([
    signHS256(IDENTITIES.admin),
    signHS256(IDENTITIES.user),
  ]);
  return { admin, user };
}
