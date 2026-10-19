import Link from "next/link";
import { ArrowDownLeft, ArrowUpRight } from "lucide-react";

import type { Transaction } from "@/lib/transaction-api";
import { formatMoney } from "@/lib/format";

export function RecentTransactions({ transactions }: { transactions: Transaction[] }) {
  return (
    <section className="mt-5 rounded-card bg-surface p-6 shadow-card">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-heading text-lg font-bold text-text">Recent transactions</h2>
        <Link className="text-sm font-semibold text-primary hover:text-primary-hover" href="/transactions">
          View all
        </Link>
      </div>
      {transactions.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">No transactions recorded yet.</p>
      ) : (
        <ul className="mt-4 divide-y divide-border">
          {transactions.map((transaction) => {
            const isIncome = transaction.type === "income";
            return (
              <li className="flex items-center gap-3 py-4" key={transaction.id}>
                <span
                  className={`flex size-10 shrink-0 items-center justify-center rounded-full ${
                    isIncome ? "bg-income-tint text-income-strong" : "bg-expense-tint text-expense-strong"
                  }`}
                >
                  {isIncome ? (
                    <ArrowDownLeft className="size-5" aria-hidden="true" />
                  ) : (
                    <ArrowUpRight className="size-5" aria-hidden="true" />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-text">
                    {transaction.description || transaction.category.name}
                  </p>
                  <p className="mt-1 text-xs text-text-muted">{transaction.category.name}</p>
                </div>
                <p className={`money text-sm font-semibold ${isIncome ? "text-income-strong" : "text-expense-strong"}`}>
                  {isIncome ? "+" : "-"}{formatMoney(transaction.amount)}
                </p>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
