"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api";
import { deleteTransaction } from "@/lib/transaction-client-api";

export function DeleteTransactionButton({ id }: { id: number }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    setError("");
    try {
      await deleteTransaction(id);
      setConfirming(false);
      router.refresh();
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "Unable to delete this transaction.",
      );
    } finally {
      setDeleting(false);
    }
  }

  if (!confirming) {
    return (
      <button
        className="ml-3 text-sm font-semibold text-expense-strong hover:text-expense"
        type="button"
        onClick={() => setConfirming(true)}
      >
        Delete
      </button>
    );
  }

  return (
    <span className="ml-3 inline-flex items-center gap-2">
      <button
        className="text-sm font-semibold text-expense-strong hover:text-expense disabled:opacity-50"
        type="button"
        disabled={deleting}
        onClick={handleDelete}
      >
        <Trash2 className="mr-1 inline size-3.5" aria-hidden="true" />
        {deleting ? "Deleting..." : "Confirm"}
      </button>
      <button
        className="text-sm text-text-muted hover:text-text"
        type="button"
        disabled={deleting}
        onClick={() => setConfirming(false)}
      >
        Cancel
      </button>
      {error && <span className="text-xs text-expense-strong">{error}</span>}
    </span>
  );
}
