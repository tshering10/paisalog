"use client";

import { DataError } from "@/components/layout/data-error";

export default function TransactionsError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <DataError
      title="We couldn't load your transactions"
      message="The transaction list is temporarily unavailable. Check your connection and try again."
      reset={reset}
    />
  );
}
