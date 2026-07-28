import type { ReactNode } from "react";
import "./AuthLayout.css";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="auth-layout">
      <div className="auth-layout-inner">
        <div className="auth-wordmark">
          <span className="auth-wordmark-mark" aria-hidden="true" />
          Auth Service
        </div>
        <div className="auth-card">
          <div className="auth-card-header">
            <h1>{title}</h1>
            {subtitle ? <p className="auth-card-subtitle">{subtitle}</p> : null}
          </div>
          {children}
        </div>
        {footer ? <div className="auth-footer">{footer}</div> : null}
      </div>
    </div>
  );
}
