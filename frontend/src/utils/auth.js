const AUTH_COOKIE_NAME = 'ydyd_auth';
const AUTH_COOKIE_VALUE = '1';

export const getCookie = (name) => {
  if (typeof document === 'undefined') return null;
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  for (const cookie of cookies) {
    const [rawKey, ...rest] = cookie.split('=');
    if (decodeURIComponent(rawKey) !== name) continue;
    return decodeURIComponent(rest.join('='));
  }
  return null;
};

export const setCookie = (name, value, options = {}) => {
  if (typeof document === 'undefined') return;
  const parts = [`${encodeURIComponent(name)}=${encodeURIComponent(value)}`];

  if (options.maxAge != null) parts.push(`Max-Age=${options.maxAge}`);
  if (options.path) parts.push(`Path=${options.path}`);
  if (options.sameSite) parts.push(`SameSite=${options.sameSite}`);
  if (options.secure) parts.push('Secure');

  document.cookie = parts.join('; ');
};

export const clearCookie = (name) => {
  setCookie(name, '', { maxAge: 0, path: '/' });
};

export const hasAuthCookie = () => getCookie(AUTH_COOKIE_NAME) === AUTH_COOKIE_VALUE;

export const setAuthCookie = () => {
  // 30 days
  setCookie(AUTH_COOKIE_NAME, AUTH_COOKIE_VALUE, {
    maxAge: 60 * 60 * 24 * 30,
    path: '/',
    sameSite: 'Lax',
  });
};

export const clearAuthCookie = () => clearCookie(AUTH_COOKIE_NAME);

