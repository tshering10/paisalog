"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import type { Budget } from "@/lib/budgets-api";
import { createBudget, deleteBudget, updateBudget } from "@/lib/budgets-client-api";
import type { Category } from "@/lib/categories-api";
import { formatMoney } from "@/lib/format";

export function BudgetManager({
  budgets,
  categories,
  year,
  month,
}: {
  budgets: Budget[];
  categories: Category[];
  year: number;
  month: number;
}) {
  const router = useRouter();
  const expenseCategories = categories.filter((category) => category.type === "expense");
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingAmount, setEditingAmount] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function addBudget(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!amount || Number(amount) <= 0) {
      setError("Enter a budget amount greater than zero.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await createBudget({
        year,
        month,
        amount,
        ...(categoryId ? { category_id: Number(categoryId) } : {}),
      });
      setAmount("");
      setCategoryId("");
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to create budget.");
    } finally {
      setSaving(false);
    }
  }

  async function saveBudget(id: number) {
    if (!editingAmount || Number(editingAmount) <= 0) {
      setError("Enter a budget amount greater than zero.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await updateBudget(id, editingAmount);
      setEditingId(null);
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to update budget.");
    } finally {
      setSaving(false);
    }
  }

  async function removeBudget(budget: Budget) {
    if (!window.confirm(`Delete the ${budget.category_name ?? "total"} budget?`)) return;
    setSaving(true);
    setError("");
    try {
      await deleteBudget(budget.id);
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to delete budget.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <form className="rounded-card bg-surface p-5 shadow-card" onSubmit={addBudget}>
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <label className="text-sm font-semibold text-text">
            Budget type
            <select
              className="mt-2 h-11 w-full rounded-control border border-border px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              value={categoryId}
              onChange={(event) => setCategoryId(event.target.value)}
            >
              <option value="">Total monthly budget</option>
              {expenseCategories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm font-semibold text-text">
            Spending limit
            <input
              className="mt-2 h-11 w-full rounded-control border border-border px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              placeholder="1000.00"
            />
          </label>
          <button
            className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover disabled:opacity-60"
            disabled={saving}
            type="submit"
          >
            <Plus className="size-4" aria-hidden="true" /> Add budget
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-expense-strong" role="alert">{error}</p>}
      </form>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {budgets.map((budget) => (
          <BudgetCard
            key={budget.id}
            budget={budget}
            editing={editingId === budget.id}
            editingAmount={editingAmount}
            saving={saving}
            onEdit={() => {
              setEditingId(budget.id);
              setEditingAmount(budget.amount);
              setError("");
            }}
            onEditAmount={setEditingAmount}
            onSave={() => void saveBudget(budget.id)}
            onCancel={() => setEditingId(null)}
            onDelete={() => void removeBudget(budget)}
          />
        ))}
      </div>
      {budgets.length === 0 && (
        <div className="mt-6 rounded-card border border-dashed border-border p-8 text-center text-sm text-text-muted">
          No budgets set for this month yet.
        </div>
      )}
    </>
  );
}

function BudgetCard({
  budget,
  editing,
  editingAmount,
  saving,
  onEdit,
  onEditAmount,
  onSave,
  onCancel,
  onDelete,
}: {
  budget: Budget;
  editing: boolean;
  editingAmount: string;
  saving: boolean;
  onEdit: () => void;
  onEditAmount: (value: string) => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
}) {
  const percentage = Math.min(Number(budget.percentage_used), 100);
  const warning = budget.is_exceeded || (budget.alert_threshold ?? 0) >= 90;

  return (
    <article className="rounded-card bg-surface p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-text-muted">{budget.category_name ?? "Total spending"}</p>
          {editing ? (
            <div className="mt-2 flex items-center gap-2">
              <input
                className="h-9 w-32 rounded-control border border-border px-2 text-sm focus:border-primary focus:outline-none"
                type="number"
                min="0.01"
                step="0.01"
                value={editingAmount}
                onChange={(event) => onEditAmount(event.target.value)}
              />
              <button className="text-sm font-semibold text-primary" type="button" disabled={saving} onClick={onSave}>Save</button>
              <button className="text-sm text-text-muted" type="button" onClick={onCancel}>Cancel</button>
            </div>
          ) : (
            <p className="money mt-1 font-heading text-xl font-bold text-text">
              {formatMoney(budget.amount)} limit
            </p>
          )}
        </div>
        {!editing && (
          <div className="flex items-center gap-2">
            <button className="text-text-muted hover:text-primary" type="button" aria-label="Edit budget" onClick={onEdit}>
              <Pencil className="size-4" aria-hidden="true" />
            </button>
            <button className="text-text-muted hover:text-expense-strong" type="button" aria-label="Delete budget" onClick={onDelete}>
              <Trash2 className="size-4" aria-hidden="true" />
            </button>
          </div>
        )}
      </div>
      <div className="mt-5 h-2 overflow-hidden rounded-full bg-background">
        <div
          className={`h-full rounded-full ${warning ? "bg-warning" : "bg-primary"}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="mt-3 flex justify-between gap-3 text-sm">
        <span className="money text-text">{formatMoney(budget.spent)} spent</span>
        <span className={`money font-semibold ${budget.is_exceeded ? "text-expense-strong" : "text-text-muted"}`}>
          {budget.is_exceeded ? `${formatMoney(String(Math.abs(Number(budget.remaining))))} over` : `${formatMoney(budget.remaining)} left`}
        </span>
      </div>
      {budget.alert_threshold !== null && (
        <p className={`mt-3 text-xs font-semibold ${budget.is_exceeded ? "text-expense-strong" : "text-warning"}`}>
          {budget.is_exceeded ? "Budget exceeded" : `${budget.alert_threshold}% of budget used`}
        </p>
      )}
    </article>
  );
}
