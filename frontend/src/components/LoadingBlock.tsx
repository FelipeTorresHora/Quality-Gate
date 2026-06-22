type LoadingBlockProps = {
  label?: string;
};

export default function LoadingBlock({ label = "Loading" }: LoadingBlockProps) {
  return <div className="loading-block">{label}</div>;
}
