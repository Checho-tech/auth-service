import type { ReactNode } from "react";
import "./Alert.css";

type Tone = "success" | "danger" | "neutral";

export function Alert({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <div className={`alert alert-${tone}`} role={tone === "danger" ? "alert" : "status"}>
      {children}
    </div>
  );
}
