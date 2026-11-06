"use client";

import { Download } from "lucide-react";
import { useState } from "react";

import { exportTransactions } from "@/lib/transaction-client-api";
import type { Category } from "@/lib/categories-api";

export function ExportTransactionsButton({
  categories,
}: {
  categories: Category[];
}) {
  const [open, setOpen] = useState(false);
  const [range, setRange] = useState<"all" | "day" | "week" | "month" | "year" | "custom">("all");
  const [date, setDate] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [type, setType] = useState<"" | "income" | "expense">("");
  const [categoryId, setCategoryId] = useState("");
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");

  function getDateRange(): { date_from?: string; date_to?: string } {
    if (range === "all") return {};
    if (range === "custom") {
      return { date_from: dateFrom || undefined, date_to: dateTo || undefined };
    }

    const selected = date ? new Date(`${date}T00:00:00`) : new Date();
    const start = new Date(selected);
    const end = new Date(selected);
    if (range === "week") {
      const day = start.getDay();
      start.setDate(start.getDate() - (day === 0 ? 6 : day - 1));
      end.setTime(start.getTime());
      end.setDate(start.getDate() + 6);
    } else if (range === "month") {
      start.setDate(1);
      end.setMonth(end.getMonth() + 1, 0);
    } else if (range === "year") {
      start.setMonth(0, 1);
      end.setMonth(11, 31);
    }
    return {
      date_from: toDateValue(start),
      date_to: toDateValue(end),
    };
  }

  async function handleExport() {
    const dateRange = getDateRange();
    if (range === "custom" && (!dateFrom || !dateTo)) {
      setError("Choose both custom start and end dates.");
      return;
    }
    if (dateRange.date_from && dateRange.date_to && dateRange.date_from > dateRange.date_to) {
      setError("The start date must be before the end date.");
      return;
    }
    setExporting(true);
    setError("");
    try {
      const blob = await exportTransactions({
        ...dateRange,
        type: type || undefined,
        category_id: categoryId || undefined,
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "transactions.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setOpen(false);
    } catch {
      setError("Unable to export transactions.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="relative">
      <button
        className="inline-flex h-11 items-center justify-center gap-2 rounded-control border border-border bg-surface px-4 text-sm font-semibold text-text hover:border-primary hover:text-primary disabled:opacity-60"
        type="button"
        onClick={() => setOpen((current) => !current)}
      >
        <Download className="size-4" aria-hidden="true" />
        Export CSV
      </button>
      {open && (
        <div className="absolute z-20 mt-2 w-80 rounded-card border border-border bg-surface p-4 text-left shadow-modal">
          <p className="font-semibold text-text">Export options</p>
          <label className="mt-4 block text-sm font-semibold text-text">
            Date range
            <select className="mt-2 h-10 w-full rounded-control border border-border px-3 font-normal" value={range} onChange={(event) => setRange(event.target.value as typeof range)}>
              <option value="all">All transactions</option>
              <option value="day">One day</option>
              <option value="week">One week</option>
              <option value="month">One month</option>
              <option value="year">One year</option>
              <option value="custom">Custom date range</option>
            </select>
          </label>
          {range !== "all" && range !== "custom" && (
            <label className="mt-3 block text-sm font-semibold text-text">
              Reference date
              <input className="mt-2 h-10 w-full rounded-control border border-border px-3 font-normal" type="date" value={date} onChange={(event) => setDate(event.target.value)} />
            </label>
          )}
          {range === "custom" && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              <label className="text-sm font-semibold text-text">From<input className="mt-2 h-10 w-full rounded-control border border-border px-2 font-normal" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /></label>
              <label className="text-sm font-semibold text-text">To<input className="mt-2 h-10 w-full rounded-control border border-border px-2 font-normal" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></label>
            </div>
          )}
          <label className="mt-3 block text-sm font-semibold text-text">
            Type
            <select className="mt-2 h-10 w-full rounded-control border border-border px-3 font-normal" value={type} onChange={(event) => setType(event.target.value as typeof type)}>
              <option value="">All types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
          </label>
          <label className="mt-3 block text-sm font-semibold text-text">
            Category
            <select className="mt-2 h-10 w-full rounded-control border border-border px-3 font-normal" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              <option value="">All categories</option>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </label>
          <button className="mt-4 h-10 w-full rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover disabled:opacity-60" type="button" onClick={() => void handleExport()} disabled={exporting}>
            {exporting ? "Exporting..." : "Download CSV"}
          </button>
        </div>
      )}
      {error && <p className="mt-2 text-xs text-expense-strong" role="alert">{error}</p>}
    </div>
  );
}

function toDateValue(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
