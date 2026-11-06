import { serverApiRequest } from "@/lib/server-api";
import type { Transaction, TransactionPage } from "@/lib/transaction-api";

export type MonthlySummary = {
  year: number;
  month: number;
  income: string;
  expenses: string;
  net: string;
  transaction_count: number;
  average_daily_expenses: string;
};

export type ExpenseCategoryBreakdown = {
  category_id: number;
  category_name: string;
  amount: string;
  percentage: string;
};

export type ExpenseByCategoryResponse = {
  year: number;
  month: number;
  total_expenses: string;
  categories: ExpenseCategoryBreakdown[];
};

export type MonthlyTrendItem = {
  year: number;
  month: number;
  income: string;
  expenses: string;
  net: string;
};

export type MonthlyTrendResponse = {
  months: MonthlyTrendItem[];
};

export type CategorySpendingComparison = {
  category_id: number;
  category_name: string;
  current_expenses: string;
  previous_expenses: string;
  absolute_change: string;
  percentage_change: string | null;
};

export type MonthlySpendingComparison = {
  year: number;
  month: number;
  previous_year: number;
  previous_month: number;
  current_expenses: string;
  previous_expenses: string;
  absolute_change: string;
  percentage_change: string | null;
  categories: CategorySpendingComparison[];
};

function periodQuery(year: number, month: number): string {
  return `year=${year}&month=${month}`;
}

export function getMonthlySummary(
  year: number,
  month: number,
): Promise<MonthlySummary> {
  return serverApiRequest<MonthlySummary>(
    `/api/v1/analytics/summary?${periodQuery(year, month)}`,
  );
}

export function getExpensesByCategory(
  year: number,
  month: number,
): Promise<ExpenseByCategoryResponse> {
  return serverApiRequest<ExpenseByCategoryResponse>(
    `/api/v1/analytics/expenses-by-category?${periodQuery(year, month)}`,
  );
}

export function getMonthlyTrend(
  year: number,
  month: number,
  months = 6,
): Promise<MonthlyTrendResponse> {
  return serverApiRequest<MonthlyTrendResponse>(
    `/api/v1/analytics/monthly-trend?${periodQuery(year, month)}&months=${months}`,
  );
}

export function getMonthlyComparison(
  year: number,
  month: number,
): Promise<MonthlySpendingComparison> {
  return serverApiRequest<MonthlySpendingComparison>(
    `/api/v1/analytics/monthly-comparison?${periodQuery(year, month)}`,
  );
}

export function getRecentTransactions(): Promise<TransactionPage> {
  return serverApiRequest<TransactionPage>(
    "/api/v1/transactions?page=1&page_size=5",
  );
}

export type { Transaction };
