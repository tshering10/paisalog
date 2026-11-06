import Link from "next/link";
import { io } from "next/cache";
import { ArrowLeft, ArrowRight, CalendarDays, Plus } from "lucide-react";

import { getCategories } from "@/lib/categories-api";
import { getBudgets } from "@/lib/budgets-api";
import {
  getExpensesByCategory,
  getMonthlySummary,
  getMonthlyComparison,
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
  const [summary, expenses, trend, comparison, recentTransactions, categories, budgets] = await Promise.all([
    getMonthlySummary(year, month),
    getExpensesByCategory(year, month),
    getMonthlyTrend(year, month),
    getMonthlyComparison(year, month),
    getRecentTransactions(),
    getCategories(),
    getBudgets(year, month),
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
          <MetricCard
            label="Average daily spending"
            value={formatMoney(summary.average_daily_expenses)}
            tone="expense"
          />
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

      <section className="mt-5 rounded-card bg-surface p-6 shadow-card">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="font-heading text-lg font-bold text-text">Monthly budgets</h2>
            <p className="mt-1 text-sm text-text-muted">Track your limits for {formatMonth(year, month)}.</p>
          </div>
          <Link className="text-sm font-semibold text-primary hover:text-primary-hover" href={`/settings/budgets?month=${year}-${String(month).padStart(2, "0")}`}>
            Manage budgets
          </Link>
        </div>
        {budgets.length > 0 ? (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {budgets.map((budget) => {
              const percentage = Math.min(Number(budget.percentage_used), 100);
              return (
                <div key={budget.id}>
                  <div className="flex justify-between gap-3 text-sm">
                    <span className="font-semibold text-text">{budget.category_name ?? "Total spending"}</span>
                    <span className={`money ${budget.is_exceeded ? "font-semibold text-expense-strong" : "text-text-muted"}`}>
                      {formatMoney(budget.spent)} / {formatMoney(budget.amount)}
                    </span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-background">
                    <div className={`h-full rounded-full ${budget.is_exceeded || (budget.alert_threshold ?? 0) >= 90 ? "bg-warning" : "bg-primary"}`} style={{ width: `${percentage}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="mt-5 text-sm text-text-muted">No budgets set for this month.</p>
        )}
      </section>

      <section className="mt-5 rounded-card bg-surface p-6 shadow-card">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <h2 className="font-heading text-lg font-bold text-text">Monthly spending comparison</h2>
            <p className="mt-1 text-sm text-text-muted">
              Compared with {formatMonth(comparison.previous_year, comparison.previous_month)}.
            </p>
          </div>
            <div className="text-left sm:text-right">
              <p className={`money font-heading text-xl font-bold ${comparisonChangeTone(comparison.absolute_change)}`}>
                {formatChange(comparison.absolute_change)}
            </p>
            <p className="text-xs text-text-muted">
              {comparison.percentage_change === null
                ? "No previous spending"
                  : `${formatChange(comparison.percentage_change)} change`}
            </p>
          </div>
        </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <ComparisonMetric
              label={formatMonth(year, month)}
              value={formatMoney(comparison.current_expenses)}
            />
            <ComparisonMetric
              label={formatMonth(comparison.previous_year, comparison.previous_month)}
              value={formatMoney(comparison.previous_expenses)}
            />
          </div>
          {comparison.categories.length > 0 && (
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {comparison.categories.map((category) => (
                <div className="border-t border-border pt-3 text-sm" key={category.category_id}>
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold text-text">{category.category_name}</span>
                    <span className={`money ${comparisonChangeTone(category.absolute_change)}`}>
                      {formatChange(category.absolute_change)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-text-muted">
                    {formatMoney(category.current_expenses)} this month vs{" "}
                    {formatMoney(category.previous_expenses)} previous month
                    {category.percentage_change === null
                      ? ""
                      : ` (${formatChange(category.percentage_change)})`}
                  </p>
                </div>
              ))}
            </div>
        )}
      </section>

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

function formatChange(value: string): string {
  const amount = Number(value);
  return `${amount > 0 ? "+" : ""}${formatMoney(value)}`;
}

function comparisonChangeTone(value: string): string {
  return Number(value) > 0 ? "text-expense-strong" : "text-income-strong";
}

function ComparisonMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-control bg-background px-4 py-3">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="money mt-1 font-heading text-lg font-bold text-text">{value}</p>
    </div>
  );
}
