import { serverApiRequest } from "@/lib/server-api";

export type Budget = {
  id: number;
  year: number;
  month: number;
  category_id: number | null;
  category_name: string | null;
  amount: string;
  spent: string;
  remaining: string;
  percentage_used: string;
  alert_threshold: number | null;
  is_exceeded: boolean;
  created_at: string;
  updated_at: string;
};

export function getBudgets(year: number, month: number): Promise<Budget[]> {
  return serverApiRequest<Budget[]>(
    `/api/v1/budgets?year=${year}&month=${month}`,
  );
}
