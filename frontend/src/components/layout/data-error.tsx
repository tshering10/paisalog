"use client";

import Link from "next/link";
import { RefreshCw } from "lucide-react";

export function DataError({
  title,
  message,
  reset,
}: {
  title: string;
  message: string;
  reset: () => void;
}) {
  return (
    <div className="rounded-card border border-expense/20 bg-surface p-8 text-center shadow-card">
      <p className="font-heading text-lg font-bold text-text">{title}</p>
      <p className="mx-auto mt-2 max-w-lg text-sm text-text-muted">{message}</p>
      <div className="mt-5 flex flex-wrap justify-center gap-3">
        <button
          className="inline-flex h-11 items-center gap-2 rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-primary"
          type="button"
          onClick={reset}
        >
          <RefreshCw className="size-4" aria-hidden="true" />
          Try again
        </button>
        <Link
          className="inline-flex h-11 items-center rounded-control border border-border px-4 text-sm font-semibold text-text-muted hover:border-primary hover:text-primary focus-visible:outline-2 focus-visible:outline-primary"
          href="/login"
        >
          Return to login
        </Link>
      </div>
    </div>
  );
}
