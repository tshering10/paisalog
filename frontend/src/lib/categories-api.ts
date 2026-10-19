import { serverApiRequest } from "@/lib/server-api";

export type Category = {
  id: number;
  name: string;
  type: "income" | "expense";
  user_id: number | null;
  created_at: string;
};

export function getCategories(): Promise<Category[]> {
  return serverApiRequest<Category[]>("/api/v1/categories");
}
