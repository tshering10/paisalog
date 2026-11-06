import Link from "next/link";
import { io } from "next/cache";
import { ArrowLeft, ArrowRight, CalendarDays } from "lucide-react";
import { Suspense } from "react";

import { BudgetManager } from "@/components/budgets/budget-manager";
import { getCategories } from "@/lib/categories-api";
import { getBudgets } from "@/lib/budgets-api";
import { formatMonth } from "@/lib/format";

type BudgetsPageProps = {
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

export default async function BudgetsPage({ searchParams }: BudgetsPageProps) {
  return (
    <div>
      <Link className="text-sm font-semibold text-primary hover:text-primary-hover" href="/dashboard">
        Back to dashboard
      </Link>
      <Suspense fallback={<BudgetPageSkeleton />}>
        <BudgetPageContent searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function BudgetPageContent({ searchParams }: BudgetsPageProps) {
  await io();
  const { year, month } = parseMonth((await searchParams).month);
  const [budgets, categories] = await Promise.all([
    getBudgets(year, month),
    getCategories(),
  ]);

  return (
    <div>
      <div className="mt-6 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-primary">Plan your spending</p>
          <h1 className="mt-1 font-heading text-3xl font-bold text-text">Monthly budgets</h1>
          <p className="mt-2 text-sm text-text-muted">Set limits and keep an eye on your spending.</p>
        </div>
        <div className="inline-flex h-11 items-center gap-1 self-start rounded-control border border-border bg-surface px-2 text-sm font-semibold text-text sm:self-auto">
          <Link className="inline-flex size-9 items-center justify-center rounded-lg hover:bg-background" href={`/settings/budgets?month=${shiftMonth(year, month, -1)}`} aria-label="Previous month">
            <ArrowLeft className="size-4" aria-hidden="true" />
          </Link>
          <span className="inline-flex min-w-32 items-center justify-center gap-2">
            <CalendarDays className="size-4 text-text-muted" aria-hidden="true" />
            {formatMonth(year, month)}
          </span>
          <Link className="inline-flex size-9 items-center justify-center rounded-lg hover:bg-background" href={`/settings/budgets?month=${shiftMonth(year, month, 1)}`} aria-label="Next month">
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
      <div className="mt-8">
        <BudgetManager budgets={budgets} categories={categories} year={year} month={month} />
      </div>
    </div>
  );
}

function BudgetPageSkeleton() {
  return (
    <div className="mt-8 space-y-4" aria-label="Loading budgets">
      <div className="h-24 animate-pulse rounded-card bg-surface shadow-card" />
      <div className="h-40 animate-pulse rounded-card bg-surface shadow-card" />
    </div>
  );
}
