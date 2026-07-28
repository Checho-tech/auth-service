import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import * as authApi from "../api/auth";
import {
  clearTokens,
  getStoredRefreshToken,
  setAccessToken,
  setStoredRefreshToken,
} from "../api/tokenStore";
import type { UserProfile } from "../types/api";
import { AuthContext, type AuthStatus } from "./authContextInstance";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshProfile = useCallback(async () => {
    const profile = await authApi.getMyProfile();
    setUser(profile);
    setStatus("authenticated");
  }, []);

  useEffect(() => {
    // On load there's no access token yet (memory-only, see tokenStore) —
    // if a refresh token survived from a previous session, the first
    // authenticated call below (getMyProfile) triggers the client's
    // built-in 401-retry-with-refresh, silently restoring the session.
    const storedRefreshToken = getStoredRefreshToken();
    if (!storedRefreshToken) {
      setStatus("unauthenticated");
      return;
    }
    refreshProfile().catch(() => {
      clearTokens();
      setStatus("unauthenticated");
    });
  }, [refreshProfile]);

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email, password);
    setAccessToken(tokens.access_token);
    setStoredRefreshToken(tokens.refresh_token);
    await refreshProfile();
  }, [refreshProfile]);

  const logout = useCallback(async () => {
    const refreshToken = getStoredRefreshToken();
    clearTokens();
    setUser(null);
    setStatus("unauthenticated");
    if (refreshToken) {
      await authApi.logout(refreshToken).catch(() => {
        // Already logged out client-side regardless — a failed revoke call
        // (e.g. the token had already expired) shouldn't block the user.
      });
    }
  }, []);

  const isAdminOrManager = useMemo(
    () => Boolean(user?.roles.some((role) => role === "admin" || role === "manager")),
    [user],
  );

  const value = useMemo(
    () => ({ user, status, login, logout, refreshProfile, isAdminOrManager }),
    [user, status, login, logout, refreshProfile, isAdminOrManager],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
