/**
 * Token storage, kept outside React state on purpose: plain API functions
 * (api/auth.ts, api/admin.ts) need to read/write tokens without importing
 * a React context, and the low-level client's 401-retry logic runs before
 * any component ever gets involved.
 *
 * Access token: memory only — lost on page reload by design. AuthContext
 * re-derives it on load via the stored refresh token (see initialize()).
 * Refresh token: localStorage, so a reload doesn't force a fresh login.
 *
 * Trade-off, stated plainly: a real production deployment would prefer the
 * backend set the refresh token as an httpOnly, Secure cookie instead of
 * returning it in the JSON body — that keeps it out of reach of any XSS in
 * this frontend entirely. This API returns it in the body (see Fase 3 of
 * the backend), so the frontend has no choice but to hold it in JS-visible
 * storage. Documented here and in the project README as a known trade-off.
 */

const REFRESH_TOKEN_KEY = "auth_service.refresh_token";

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setStoredRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export function clearTokens(): void {
  accessToken = null;
  setStoredRefreshToken(null);
}
