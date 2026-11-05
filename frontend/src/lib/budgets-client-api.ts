import { apiRequest } from "@/lib/api";
import type { Budget } from "@/lib/budgets-api";

export type BudgetInput = {
  year: number;
  month: number;
  category_id?: number;
  amount: string;
};

export function createBudget(input: BudgetInput): Promise<Budget> {
  return apiRequest<Budget>("/api/v1/budgets", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateBudget(id: number, amount: string): Promise<Budget> {
  return apiRequest<Budget>(`/api/v1/budgets/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ amount }),
  });
}

export function deleteBudget(id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/budgets/${id}`, { method: "DELETE" });
}
