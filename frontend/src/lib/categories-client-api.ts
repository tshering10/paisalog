import { apiRequest } from "@/lib/api";
import type { Category } from "@/lib/categories-api";

export type CategoryInput = {
  name: string;
  type: "income" | "expense";
};

export function createCategory(input: CategoryInput): Promise<Category> {
  return apiRequest<Category>("/api/v1/categories", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateCategory(id: number, name: string): Promise<Category> {
  return apiRequest<Category>(`/api/v1/categories/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function deleteCategory(id: number): Promise<void> {
  return apiRequest<void>(`/api/v1/categories/${id}`, { method: "DELETE" });
}
