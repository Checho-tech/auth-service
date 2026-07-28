import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { Button } from "./Button";
import { Pill } from "./Pill";
import "./AppShell.css";

function navClass({ isActive }: { isActive: boolean }) {
  return ["shell-nav-link", isActive ? "shell-nav-link-active" : ""].filter(Boolean).join(" ");
}

export function AppShell({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const { user, logout, isAdminOrManager } = useAuth();

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <div className="shell-wordmark">
          <span className="shell-wordmark-mark" aria-hidden="true" />
          Auth Service
        </div>

        <nav className="shell-nav">
          <span className="eyebrow shell-nav-heading">Account</span>
          <NavLink to="/dashboard" className={navClass}>
            Profile
          </NavLink>

          {isAdminOrManager ? (
            <>
              <span className="eyebrow shell-nav-heading">Admin</span>
              <NavLink to="/admin/users" className={navClass}>
                Users
              </NavLink>
              <NavLink to="/admin/audit-log" className={navClass}>
                Audit log
              </NavLink>
            </>
          ) : null}
        </nav>

        <div className="shell-user">
          <div className="shell-user-info">
            <span className="shell-user-email" title={user?.email}>
              {user?.email}
            </span>
            <div className="shell-user-roles">
              {user?.roles.map((role) => (
                <Pill key={role} tone="accent">
                  {role}
                </Pill>
              ))}
            </div>
          </div>
          <Button variant="ghost" onClick={() => void logout()}>
            Sign out
          </Button>
        </div>
      </aside>

      <main className="shell-main">
        <header className="shell-header">
          <div>
            <h1>{title}</h1>
            {description ? <p className="shell-header-description">{description}</p> : null}
          </div>
          {actions ? <div className="shell-header-actions">{actions}</div> : null}
        </header>
        <div className="shell-content">{children}</div>
      </main>
    </div>
  );
}
