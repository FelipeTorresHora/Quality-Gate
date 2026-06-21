import { ApiError } from "../api/client";

type ErrorMessageProps = {
  error: unknown;
};

export default function ErrorMessage({ error }: ErrorMessageProps) {
  if (!error) {
    return null;
  }
  const message = error instanceof ApiError ? error.detail.message : String(error);
  return <div className="error-banner">{message}</div>;
}
