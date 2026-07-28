import type { ReactNode } from "react";
import "./Pill.css";

type Tone = "neutral" | "accent" | "success" | "warning" | "danger";

export function Pill({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}
