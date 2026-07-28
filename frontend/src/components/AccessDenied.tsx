import { Alert } from "./Alert";

export function AccessDenied({ permission }: { permission: string }) {
  return (
    <Alert tone="danger">
      You don't have the <code className="mono">{permission}</code> permission required to view
      this section. Ask an Admin to grant it via Users → Roles.
    </Alert>
  );
}
