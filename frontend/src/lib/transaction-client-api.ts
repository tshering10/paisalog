import { apiRequest } from "@/lib/api";
import type { Transaction } from "@/lib/transaction-api";
import type { TransactionFilters } from "@/lib/transaction-api";

export type TransactionInput = {
  category_id: number;
  type: "income" | "expense";
  amount: string;
  transaction_date: string;
  description: string | null;
};

export function createTransaction(input: TransactionInput): Promise<Transaction> {
  return apiRequest<Transaction>("/api/v1/transactions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateTransaction(
  id: number,
  input: TransactionInput,
): Promise<Transaction> {
  return apiRequest<Transaction>(`/api/v1/transactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteTransaction(id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/transactions/${id}`, { method: "DELETE" });
}

export async function exportTransactions(
  filters: Pick<TransactionFilters, "type" | "category_id" | "date_from" | "date_to">,
): Promise<Blob> {
  const query = new URLSearchParams();
  if (filters.type) query.set("type", filters.type);
  if (filters.category_id) query.set("category_id", filters.category_id);
  if (filters.date_from) query.set("date_from", filters.date_from);
  if (filters.date_to) query.set("date_to", filters.date_to);

  const response = await fetch(`/api/v1/transactions/export.csv?${query}`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Unable to export transactions.");
  }
  return response.blob();
}
