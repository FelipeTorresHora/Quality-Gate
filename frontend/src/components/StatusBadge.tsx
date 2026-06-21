type StatusBadgeProps = {
  value: string | null;
};

export default function StatusBadge({ value }: StatusBadgeProps) {
  const normalized = value ?? "none";
  return <span className={`status-badge status-${normalized}`}>{normalized}</span>;
}
