import LoadingBlock from "./LoadingBlock";

export default function PageFallback({ label = "Loading page" }: { label?: string }) {
  return (
    <div className="page-stack">
      <LoadingBlock label={label} />
    </div>
  );
}
