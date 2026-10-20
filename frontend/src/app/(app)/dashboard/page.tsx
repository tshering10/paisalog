import Link from "next/link";
import { io } from "next/cache";
import { ArrowLeft, ArrowRight, CalendarDays, Plus } from "lucide-react";

import { getCategories } from "@/lib/categories-api";
import {
  getExpensesByCategory,
  getMonthlySummary,
  getMonthlyTrend,
  getRecentTransactions,
} from "@/lib/analytics-api";
import { ExpenseDonutChart, MonthlyTrendChart } from "@/components/dashboard/dashboard-charts";
import { RecentTransactions } from "@/components/dashboard/recent-transactions";
import { TransactionFormModal } from "@/components/transactions/transaction-form-modal";
import { formatMoney, formatMonth } from "@/lib/format";

type DashboardPageProps = {
  searchParams: Promise<{ month?: string }>;
};

function parseMonth(value: string | undefined): { year: number; month: number } {
  const match = value?.match(/^(\d{4})-(\d{2})$/);
  const year = match ? Number(match[1]) : NaN;
  const month = match ? Number(match[2]) : NaN;

  if (Number.isInteger(year) && Number.isInteger(month) && month >= 1 && month <= 12) {
    return { year, month };
  }

  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1 };
}

function shiftMonth(year: number, month: number, offset: number): string {
  const date = new Date(year, month - 1 + offset, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export default async function DashboardPage({
  searchParams,
}: DashboardPageProps) {
  await io();
  const { year, month } = parseMonth((await searchParams).month);
  const [summary, expenses, trend, recentTransactions, categories] = await Promise.all([
    getMonthlySummary(year, month),
    getExpensesByCategory(year, month),
    getMonthlyTrend(year, month),
    getRecentTransactions(),
    getCategories(),
  ]);

  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold text-primary">Your overview</p>
          <h1 className="mt-1 font-heading text-3xl font-bold text-text">
            Dashboard
          </h1>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="inline-flex h-11 items-center gap-1 rounded-control border border-border bg-surface px-2 text-sm font-semibold text-text">
            <Link
              className="inline-flex size-9 items-center justify-center rounded-lg hover:bg-background focus-visible:outline-2 focus-visible:outline-primary"
              href={`/dashboard?month=${shiftMonth(year, month, -1)}`}
              aria-label="Previous month"
            >
              <ArrowLeft className="size-4" aria-hidden="true" />
            </Link>
            <span className="inline-flex min-w-32 items-center justify-center gap-2">
              <CalendarDays className="size-4 text-text-muted" aria-hidden="true" />
              {formatMonth(year, month)}
            </span>
            <Link
              className="inline-flex size-9 items-center justify-center rounded-lg hover:bg-background focus-visible:outline-2 focus-visible:outline-primary"
              href={`/dashboard?month=${shiftMonth(year, month, 1)}`}
              aria-label="Next month"
            >
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
          </div>
          <TransactionFormModal
            categories={categories}
            trigger={
              <button
                className="inline-flex h-11 items-center gap-2 rounded-control bg-primary px-4 text-sm font-semibold text-white shadow-hero transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                type="button"
              >
                <Plus className="size-4" aria-hidden="true" />
                Add transaction
              </button>
            }
          />
        </div>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <section className="rounded-modal bg-hero p-6 text-white shadow-hero sm:p-8">
          <p className="text-sm text-white/80">Net this month</p>
          <p className="money mt-2 font-heading text-4xl font-extrabold">
            {formatMoney(summary.net)}
          </p>
          <p className="mt-3 text-sm text-indigo-100">
            {summary.transaction_count === 0
              ? "No transactions recorded for this month."
              : `${summary.transaction_count} transaction${summary.transaction_count === 1 ? "" : "s"} recorded this month.`}
          </p>
        </section>

        <div className="grid grid-cols-2 gap-5 lg:grid-cols-1">
          <MetricCard label="Income" value={formatMoney(summary.income)} tone="income" />
          <MetricCard label="Expenses" value={formatMoney(summary.expenses)} tone="expense" />
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <section className="rounded-card bg-surface p-6 shadow-card">
          <h2 className="font-heading text-lg font-bold text-text">Expenses by category</h2>
          <ExpenseDonutChart categories={expenses.categories} />
        </section>

        <section className="rounded-card bg-surface p-6 shadow-card">
          <h2 className="font-heading text-lg font-bold text-text">Income vs expenses</h2>
          <MonthlyTrendChart months={trend.months} />
        </section>
      </div>

      <RecentTransactions transactions={recentTransactions.items} />
    </div>
  );
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "income" | "expense";
}) {
  return (
    <section className="rounded-card bg-surface p-5 shadow-card">
      <p className="text-sm text-text-muted">{label}</p>
      <p
        className={`money mt-2 font-heading text-xl font-bold ${
          tone === "income" ? "text-income-strong" : "text-expense-strong"
        }`}
      >
        {value}
      </p>
    </section>
  );
}
