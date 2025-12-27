let cachedAuthorized = null;
let cachedAt = 0;
const STATUS_CACHE_TTL_MS = 10_000;

export const getAuthStatus = async (options = {}) => {
  const force = options.force === true;
  const now = Date.now();
  if (!force && cachedAuthorized !== null && now - cachedAt < STATUS_CACHE_TTL_MS) {
    return cachedAuthorized;
  }

  try {
    const res = await fetch('/api/auth/status', { credentials: 'same-origin' });
    const data = await res.json().catch(() => ({}));
    cachedAuthorized = Boolean(res.ok && data && data.authorized);
  } catch {
    cachedAuthorized = false;
  } finally {
    cachedAt = now;
  }

  return cachedAuthorized;
};

export const login = async (password) => {
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({ password }),
    });

    if (res.ok) {
      cachedAuthorized = true;
      cachedAt = Date.now();
      return { ok: true };
    }

    const data = await res.json().catch(() => ({}));
    return { ok: false, error: data?.detail || 'Login failed.' };
  } catch {
    return { ok: false, error: 'Network error.' };
  }
};

export const logout = async () => {
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  } catch {
    // ignore
  } finally {
    cachedAuthorized = false;
    cachedAt = Date.now();
  }
};

export const clearAuthCache = () => {
  cachedAuthorized = null;
  cachedAt = 0;
};
