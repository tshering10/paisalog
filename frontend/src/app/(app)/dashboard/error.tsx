"use client";

import { DataError } from "@/components/layout/data-error";

export default function DashboardError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <DataError
      title="We couldn't load your dashboard"
      message="Your financial data could not be loaded. Check that the backend is running, then try again."
      reset={reset}
    />
  );
}
