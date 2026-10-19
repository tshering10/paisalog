import { apiRequest } from "@/lib/api";
import type { Transaction } from "@/lib/transaction-api";

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
