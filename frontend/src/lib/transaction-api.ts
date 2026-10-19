import { serverApiRequest } from "@/lib/server-api";

export type Transaction = {
  id: number;
  category_id: number;
  type: "income" | "expense";
  amount: string;
  transaction_date: string;
  description: string | null;
  category: {
    id: number;
    name: string;
    type: "income" | "expense";
  };
};

export type TransactionFilters = {
  type?: "income" | "expense";
  category_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
};

export type TransactionPage = {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
};

export function getTransactions(
  filters: TransactionFilters = {},
): Promise<TransactionPage> {
  const query = new URLSearchParams();

  if (filters.type) query.set("type", filters.type);
  if (filters.category_id) query.set("category_id", filters.category_id);
  if (filters.date_from) query.set("date_from", filters.date_from);
  if (filters.date_to) query.set("date_to", filters.date_to);
  query.set("page", String(filters.page ?? 1));
  query.set("page_size", String(filters.page_size ?? 10));

  return serverApiRequest<TransactionPage>(
    `/api/v1/transactions?${query.toString()}`,
  );
}
