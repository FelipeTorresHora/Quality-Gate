import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  action?: ReactNode;
  children?: ReactNode;
};

export default function EmptyState({ title, action, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div>
        <strong>{title}</strong>
        {children && <p>{children}</p>}
      </div>
      {action}
    </div>
  );
}
