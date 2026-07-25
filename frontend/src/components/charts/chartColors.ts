// Mirrors the CSS custom properties in src/styles/app.css.
// Recharts SVG props don't reliably resolve var(--token) across all internals
// (tooltips, legends), so chart colors are duplicated here as plain hex.
export const chartColors = {
  pass: "#4ade80",
  fail: "#f87171",
  warn: "#fbbf24",
  neutral: "#8a93a6",
  accent: "#ffb224",
  border: "#232a38",
  panel: "#11151d",
  text: "#e8eaf0",
  muted: "#8a93a6"
};
