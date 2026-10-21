"use client";

import { DataError } from "@/components/layout/data-error";

export default function CategoriesError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <DataError
      title="We couldn't load your categories"
      message="Categories are temporarily unavailable. Check your connection and try again."
      reset={reset}
    />
  );
}
