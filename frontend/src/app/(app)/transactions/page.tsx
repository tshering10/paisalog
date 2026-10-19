import Link from "next/link";
import { ArrowDownLeft, ArrowLeft, ArrowRight, ArrowUpRight, Plus, RotateCcw } from "lucide-react";

import { getCategories } from "@/lib/categories-api";
import { TransactionFormModal } from "@/components/transactions/transaction-form-modal";
import { DeleteTransactionButton } from "@/components/transactions/delete-transaction-button";
import { formatMoney } from "@/lib/format";
import { getTransactions } from "@/lib/transaction-api";

type SearchParams = Record<string, string | string[] | undefined>;

type TransactionsPageProps = {
  searchParams: Promise<SearchParams>;
};

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function validType(value: string | undefined): "income" | "expense" | undefined {
  return value === "income" || value === "expense" ? value : undefined;
}

function pageValue(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= 1 ? parsed : 1;
}

function buildUrl(params: {
  type?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
}): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) query.set(key, String(value));
  }
  const encoded = query.toString();
  return encoded ? `/transactions?${encoded}` : "/transactions";
}

function formatTransactionDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return value;
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(year, month - 1, day));
}

export default async function TransactionsPage({
  searchParams,
}: TransactionsPageProps) {
  const params = await searchParams;
  const filters = {
    type: validType(firstValue(params.type)),
    category_id: firstValue(params.category_id),
    date_from: firstValue(params.date_from),
    date_to: firstValue(params.date_to),
    page: pageValue(firstValue(params.page)),
  };
  const [transactionPage, categories] = await Promise.all([
    getTransactions(filters),
    getCategories(),
  ]);
  const pageCount = Math.max(1, Math.ceil(transactionPage.total / transactionPage.page_size));
  const hasFilters = Boolean(
    filters.type || filters.category_id || filters.date_from || filters.date_to,
  );
  const categoryOptions = filters.type
    ? categories.filter((category) => category.type === filters.type)
    : categories;

  return (
    <div>
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold text-primary">Your activity</p>
          <h1 className="mt-1 font-heading text-3xl font-bold text-text">Transactions</h1>
          <p className="mt-2 text-sm text-text-muted">Review and filter your income and expenses.</p>
        </div>
        <TransactionFormModal
          categories={categories}
          trigger={
            <button
              className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-4 text-sm font-semibold text-white shadow-hero transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
              type="button"
            >
              <Plus className="size-4" aria-hidden="true" />
              Add transaction
            </button>
          }
        />
      </div>

      <form className="mt-8 rounded-card bg-surface p-5 shadow-card" method="get">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <label className="text-sm font-semibold text-text">
            Type
            <select
              className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              name="type"
              defaultValue={filters.type ?? ""}
            >
              <option value="">All types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </label>
          <label className="text-sm font-semibold text-text">
            Category
            <select
              className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              name="category_id"
              defaultValue={filters.category_id ?? ""}
            >
              <option value="">All categories</option>
              {categoryOptions.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-semibold text-text">
            From
            <input
              className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              name="date_from"
              type="date"
              defaultValue={filters.date_from}
            />
          </label>
          <label className="text-sm font-semibold text-text">
            To
            <input
              className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal text-text focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              name="date_to"
              type="date"
              defaultValue={filters.date_to}
            />
          </label>
          <div className="flex items-end gap-3">
            <button className="h-11 flex-1 rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-primary" type="submit">
              Apply filters
            </button>
            <Link
              className="inline-flex h-11 items-center justify-center gap-2 rounded-control border border-border px-3 text-sm font-semibold text-text-muted hover:border-primary hover:text-primary focus-visible:outline-2 focus-visible:outline-primary"
              href="/transactions"
            >
              <RotateCcw className="size-4" aria-hidden="true" />
              <span className="sr-only sm:not-sr-only">Reset</span>
            </Link>
          </div>
        </div>
      </form>

      <section className="mt-5 overflow-hidden rounded-card bg-surface shadow-card">
        <div className="overflow-x-auto">
          {transactionPage.items.length === 0 ? (
            <div className="px-6 py-16 text-center">
              <p className="font-heading text-lg font-bold text-text">
                {hasFilters ? "No transactions match these filters" : "No transactions yet"}
              </p>
              <p className="mt-2 text-sm text-text-muted">
                {hasFilters
                  ? "Try changing your filters or reset them to see all activity."
                  : "Add your first transaction to start tracking your money."}
              </p>
              {hasFilters && (
                <Link className="mt-5 inline-flex text-sm font-semibold text-primary hover:text-primary-hover" href="/transactions">
                  Reset filters
                </Link>
              )}
            </div>
          ) : (
            <table className="w-full min-w-[680px] text-left">
              <thead className="border-b border-border bg-background text-xs uppercase tracking-wide text-text-muted">
                <tr>
                  <th className="px-6 py-4 font-semibold">Transaction</th>
                  <th className="px-6 py-4 font-semibold">Category</th>
                  <th className="px-6 py-4 font-semibold">Date</th>
                  <th className="px-6 py-4 text-right font-semibold">Amount</th>
                  <th className="px-6 py-4 text-right font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {transactionPage.items.map((transaction) => {
                  const isIncome = transaction.type === "income";
                  return (
                    <tr className="text-sm" key={transaction.id}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <span className={`flex size-9 items-center justify-center rounded-full ${isIncome ? "bg-income-tint text-income-strong" : "bg-expense-tint text-expense-strong"}`}>
                            {isIncome ? <ArrowDownLeft className="size-4" aria-hidden="true" /> : <ArrowUpRight className="size-4" aria-hidden="true" />}
                          </span>
                          <span className="font-semibold text-text">{transaction.description || "No description"}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-text-muted">{transaction.category.name}</td>
                      <td className="px-6 py-4 text-text-muted">{formatTransactionDate(transaction.transaction_date)}</td>
                      <td className={`money px-6 py-4 text-right font-semibold ${isIncome ? "text-income-strong" : "text-expense-strong"}`}>
                        {isIncome ? "+" : "-"}{formatMoney(transaction.amount)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <TransactionFormModal
                          categories={categories}
                          transaction={transaction}
                          trigger={
                            <button className="text-sm font-semibold text-primary hover:text-primary-hover" type="button">
                              Edit
                            </button>
                          }
                        />
                        <DeleteTransactionButton id={transaction.id} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
        {transactionPage.items.length > 0 && (
          <div className="flex flex-col justify-between gap-3 border-t border-border px-6 py-4 text-sm text-text-muted sm:flex-row sm:items-center">
            <span>
              Showing {(transactionPage.page - 1) * transactionPage.page_size + 1} to{" "}
              {Math.min(transactionPage.page * transactionPage.page_size, transactionPage.total)} of {transactionPage.total}
            </span>
            <div className="flex items-center gap-2">
              <PaginationLink
                href={buildUrl({ ...filters, page: filters.page - 1 })}
                disabled={filters.page <= 1}
                label="Previous"
                icon={<ArrowLeft className="size-4" aria-hidden="true" />}
              />
              <span className="px-2 font-medium text-text">Page {filters.page} of {pageCount}</span>
              <PaginationLink
                href={buildUrl({ ...filters, page: filters.page + 1 })}
                disabled={filters.page >= pageCount}
                label="Next"
                icon={<ArrowRight className="size-4" aria-hidden="true" />}
              />
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function PaginationLink({
  href,
  disabled,
  label,
  icon,
}: {
  href: string;
  disabled: boolean;
  label: string;
  icon: React.ReactNode;
}) {
  if (disabled) {
    return <span className="inline-flex h-10 items-center gap-2 rounded-control border border-border px-3 text-text-muted/50" aria-disabled="true">{icon}<span className="sr-only">{label}</span></span>;
  }
  return <Link className="inline-flex h-10 items-center gap-2 rounded-control border border-border px-3 font-semibold text-text hover:border-primary hover:text-primary focus-visible:outline-2 focus-visible:outline-primary" href={href}>{icon}<span className="sr-only">{label}</span></Link>;
}
