import { createContext } from "react";
import type { UserProfile } from "../types/api";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export interface AuthContextValue {
  user: UserProfile | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  /** Best-effort UI gate only — the backend re-checks every permission on
   * every request (Fase 4), so this never needs to be perfectly precise;
   * it just decides whether the Admin section is worth showing at all. */
  isAdminOrManager: boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
