"use client";

import { useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api";
import type { Category } from "@/lib/categories-api";
import {
  createCategory,
  deleteCategory,
  updateCategory,
} from "@/lib/categories-client-api";

export function CategoryManager({ categories }: { categories: Category[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [type, setType] = useState<"income" | "expense">("expense");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function addCategory(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Category name is required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createCategory({ name: name.trim(), type });
      setName("");
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to add category.");
    } finally {
      setSaving(false);
    }
  }

  async function saveRename(id: number) {
    if (!editingName.trim()) {
      setError("Category name is required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await updateCategory(id, editingName.trim());
      setEditingId(null);
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to rename category.");
    } finally {
      setSaving(false);
    }
  }

  async function removeCategory(category: Category) {
    if (!window.confirm(`Delete ${category.name}?`)) return;
    setSaving(true);
    setError("");
    try {
      await deleteCategory(category.id);
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to delete category.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <form className="rounded-card bg-surface p-5 shadow-card" onSubmit={addCategory}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 text-sm font-semibold text-text">
            New category
            <input
              className="mt-2 h-11 w-full rounded-control border border-border px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="e.g. Subscriptions"
            />
          </label>
          <label className="text-sm font-semibold text-text">
            Type
            <select
              className="mt-2 h-11 rounded-control border border-border px-3 font-normal focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              value={type}
              onChange={(event) => setType(event.target.value as "income" | "expense")}
            >
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </label>
          <button className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover disabled:opacity-60" disabled={saving} type="submit">
            <Plus className="size-4" aria-hidden="true" /> Add
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-expense-strong" role="alert">{error}</p>}
      </form>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <CategorySection
          title="Expense categories"
          type="expense"
          categories={categories}
          editingId={editingId}
          editingName={editingName}
          saving={saving}
          onEdit={(category) => {
            setEditingId(category.id);
            setEditingName(category.name);
          }}
          onEditName={setEditingName}
          onSave={saveRename}
          onCancel={() => setEditingId(null)}
          onDelete={removeCategory}
        />
        <CategorySection
          title="Income categories"
          type="income"
          categories={categories}
          editingId={editingId}
          editingName={editingName}
          saving={saving}
          onEdit={(category) => {
            setEditingId(category.id);
            setEditingName(category.name);
          }}
          onEditName={setEditingName}
          onSave={saveRename}
          onCancel={() => setEditingId(null)}
          onDelete={removeCategory}
        />
      </div>
    </>
  );
}

function CategorySection({
  title,
  type,
  categories,
  editingId,
  editingName,
  saving,
  onEdit,
  onEditName,
  onSave,
  onCancel,
  onDelete,
}: {
  title: string;
  type: "income" | "expense";
  categories: Category[];
  editingId: number | null;
  editingName: string;
  saving: boolean;
  onEdit: (category: Category) => void;
  onEditName: (value: string) => void;
  onSave: (id: number) => void;
  onCancel: () => void;
  onDelete: (category: Category) => void;
}) {
  const items = categories.filter((category) => category.type === type);
  return (
    <section>
      <h2 className="font-heading text-xl font-bold text-text">{title}</h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {items.map((category) => (
          <div className="rounded-card bg-surface p-4 shadow-card" key={category.id}>
            {editingId === category.id ? (
              <div className="flex gap-2">
                <input className="h-10 min-w-0 flex-1 rounded-control border border-border px-3 text-sm focus:border-primary focus:outline-none" value={editingName} onChange={(event) => onEditName(event.target.value)} />
                <button className="text-sm font-semibold text-primary" type="button" disabled={saving} onClick={() => onSave(category.id)}>Save</button>
                <button className="text-sm text-text-muted" type="button" onClick={onCancel}>Cancel</button>
              </div>
            ) : (
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-text">{category.name}</p>
                  {category.user_id === null && <span className="mt-1 inline-block rounded-full bg-primary-tint px-2 py-0.5 text-xs font-medium text-primary">Default</span>}
                </div>
                {category.user_id !== null && (
                  <div className="flex items-center gap-2">
                    <button className="text-text-muted hover:text-primary" type="button" aria-label={`Rename ${category.name}`} onClick={() => onEdit(category)}><Pencil className="size-4" aria-hidden="true" /></button>
                    <button className="text-text-muted hover:text-expense-strong" type="button" aria-label={`Delete ${category.name}`} onClick={() => onDelete(category)}><Trash2 className="size-4" aria-hidden="true" /></button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      {items.length === 0 && <p className="mt-4 text-sm text-text-muted">No categories in this group.</p>}
    </section>
  );
}
