import { ApiError, type TokenResponse } from "../types/api";
import {
  clearTokens,
  getAccessToken,
  getStoredRefreshToken,
  setAccessToken,
  setStoredRefreshToken,
} from "./tokenStore";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface RequestOptions extends Omit<RequestInit, "body"> {
  /** Attach the current access token as a Bearer header. Default true. */
  auth?: boolean;
  body?: Record<string, unknown>;
  /** Internal: prevents an infinite loop when retrying after a refresh. */
  _isRetry?: boolean;
}

async function rawRequest(path: string, options: RequestOptions): Promise<Response> {
  const { auth = true, body, _isRetry, headers, ...rest } = options;
  const finalHeaders = new Headers(headers);
  finalHeaders.set("Content-Type", "application/json");

  if (auth) {
    const token = getAccessToken();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });
}

async function parseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : String(item)))
        .join(" ");
    }
  }
  if (body && typeof body === "object" && "message" in body) {
    return String((body as { message: unknown }).message);
  }
  return fallback;
}

// Concurrent 401s (e.g. two requests firing at once) must share a single
// refresh attempt — otherwise the second refresh call would present an
// already-rotated token and trip the backend's reuse-detection (Fase 3),
// revoking every session as if it were a real attack.
let refreshInFlight: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const response = await rawRequest("/api/v1/auth/refresh", {
        method: "POST",
        auth: false,
        body: { refresh_token: refreshToken },
      });
      if (!response.ok) {
        clearTokens();
        return false;
      }
      const data = (await parseBody(response)) as TokenResponse;
      setAccessToken(data.access_token);
      setStoredRefreshToken(data.refresh_token);
      return true;
    })().finally(() => {
      refreshInFlight = null;
    });
  }

  return refreshInFlight;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await rawRequest(path, options);

  if (response.status === 401 && options.auth !== false && !options._isRetry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawRequest(path, { ...options, _isRetry: true });
    }
  }

  const parsed = await parseBody(response);

  if (!response.ok) {
    throw new ApiError(response.status, extractErrorMessage(parsed, response.statusText));
  }

  return parsed as T;
}
