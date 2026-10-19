"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api";
import type { Category } from "@/lib/categories-api";
import type { Transaction } from "@/lib/transaction-api";
import {
  createTransaction,
  updateTransaction,
  type TransactionInput,
} from "@/lib/transaction-client-api";

type TransactionFormModalProps = {
  categories: Category[];
  transaction?: Transaction;
  trigger: React.ReactNode;
};

type FormErrors = Partial<Record<"amount" | "category_id" | "transaction_date", string>>;

function today(): string {
  const date = new Date();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

export function TransactionFormModal({
  categories,
  transaction,
  trigger,
}: TransactionFormModalProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<"income" | "expense">(
    transaction?.type ?? "expense",
  );
  const [amount, setAmount] = useState(transaction?.amount ?? "");
  const [categoryId, setCategoryId] = useState(
    transaction ? String(transaction.category_id) : "",
  );
  const [date, setDate] = useState(transaction?.transaction_date ?? today());
  const [description, setDescription] = useState(transaction?.description ?? "");
  const [errors, setErrors] = useState<FormErrors>({});
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const availableCategories = categories.filter((category) => category.type === type);

  function validate(): FormErrors {
    const nextErrors: FormErrors = {};
    if (!amount || Number(amount) <= 0) nextErrors.amount = "Amount must be greater than 0.";
    if (!/^\d+(\.\d{1,2})?$/.test(amount)) {
      nextErrors.amount = "Use an amount with at most 2 decimal places.";
    }
    if (!categoryId) nextErrors.category_id = "Choose a category.";
    if (!date) nextErrors.transaction_date = "Choose a date.";
    return nextErrors;
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);
    setMessage("");
    if (Object.keys(nextErrors).length > 0) return;

    const input: TransactionInput = {
      amount,
      category_id: Number(categoryId),
      type,
      transaction_date: date,
      description: description.trim() || null,
    };

    setSaving(true);
    try {
      if (transaction) {
        await updateTransaction(transaction.id, input);
      } else {
        await createTransaction(input);
      }
      setOpen(false);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        setErrors(error.fieldErrors as FormErrors);
        setMessage(error.message);
      } else {
        setMessage("Unable to save this transaction. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <span
        className="contents"
        onClick={() => {
          setMessage("");
          setErrors({});
          setOpen(true);
        }}
      >
        {trigger}
      </span>
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-sidebar/60 p-4"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <div
            className="w-full max-w-lg rounded-modal bg-surface p-6 shadow-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="transaction-modal-title"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="transaction-modal-title" className="font-heading text-xl font-bold text-text">
                  {transaction ? "Edit transaction" : "Add transaction"}
                </h2>
                <p className="mt-1 text-sm text-text-muted">Record the details of your transaction.</p>
              </div>
              <button
                className="inline-flex size-10 items-center justify-center rounded-control text-text-muted hover:bg-background hover:text-text focus-visible:outline-2 focus-visible:outline-primary"
                type="button"
                aria-label="Close transaction form"
                onClick={() => setOpen(false)}
              >
                <X className="size-5" aria-hidden="true" />
              </button>
            </div>

            {message && <p className="mt-4 rounded-control bg-expense-tint p-3 text-sm text-expense-strong" role="alert">{message}</p>}
            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <fieldset>
                <legend className="text-sm font-semibold text-text">Type</legend>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  {(["expense", "income"] as const).map((option) => (
                    <button
                      className={`h-11 rounded-control border text-sm font-semibold ${
                        type === option
                          ? option === "income"
                            ? "border-income bg-income-tint text-income-strong"
                            : "border-expense bg-expense-tint text-expense-strong"
                          : "border-border text-text-muted hover:border-primary"
                      }`}
                      key={option}
                      type="button"
                      onClick={() => {
                        setType(option);
                        setCategoryId("");
                      }}
                    >
                      {option === "income" ? "Income" : "Expense"}
                    </button>
                  ))}
                </div>
              </fieldset>
              <div className="grid gap-5 sm:grid-cols-2">
                <label className="text-sm font-semibold text-text">
                  Amount
                  <div className="mt-2 flex h-11 items-center rounded-control border border-border focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
                    <span className="px-3 text-text-muted">Rs</span>
                    <input
                      className="h-full min-w-0 flex-1 border-0 bg-transparent pr-3 font-normal outline-none"
                      inputMode="decimal"
                      value={amount}
                      onChange={(event) => setAmount(event.target.value)}
                      aria-describedby={errors.amount ? "amount-error" : undefined}
                    />
                  </div>
                  {errors.amount && <span id="amount-error" className="mt-1 block text-xs text-expense-strong">{errors.amount}</span>}
                </label>
                <label className="text-sm font-semibold text-text">
                  Date
                  <input
                    className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    type="date"
                    value={date}
                    onChange={(event) => setDate(event.target.value)}
                  />
                  {errors.transaction_date && <span className="mt-1 block text-xs text-expense-strong">{errors.transaction_date}</span>}
                </label>
              </div>
              <label className="block text-sm font-semibold text-text">
                Category
                <select
                  className="mt-2 h-11 w-full rounded-control border border-border bg-surface px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  value={categoryId}
                  onChange={(event) => setCategoryId(event.target.value)}
                >
                  <option value="">Choose a category</option>
                  {availableCategories.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
                {errors.category_id && <span className="mt-1 block text-xs text-expense-strong">{errors.category_id}</span>}
              </label>
              <label className="block text-sm font-semibold text-text">
                Description <span className="font-normal text-text-muted">(optional)</span>
                <textarea
                  className="mt-2 min-h-24 w-full resize-y rounded-control border border-border bg-surface px-3 py-2 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  maxLength={500}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                />
              </label>
              <div className="flex justify-end gap-3 border-t border-border pt-5">
                <button className="h-11 rounded-control border border-border px-4 text-sm font-semibold text-text-muted hover:border-primary hover:text-primary" type="button" onClick={() => setOpen(false)}>
                  Cancel
                </button>
                <button className="h-11 rounded-control bg-primary px-5 text-sm font-semibold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-60" type="submit" disabled={saving}>
                  {saving ? "Saving..." : transaction ? "Save changes" : "Save transaction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
