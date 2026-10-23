"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, UserRound } from "lucide-react";

import { ApiError } from "@/lib/api";
import { deactivateAccount, deleteAccount } from "@/lib/auth-api";

export default function AccountActionsPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function deactivate() {
    setError(""); setBusy(true);
    try { await deactivateAccount(password); router.replace("/login"); router.refresh(); }
    catch (error) { setError(error instanceof ApiError ? error.message : "We could not deactivate your account."); setBusy(false); }
  }

  async function remove() {
    if (confirmation !== "DELETE") { setError("Type DELETE to confirm permanent account deletion."); return; }
    setError(""); setBusy(true);
    try { await deleteAccount(password); router.replace("/login"); router.refresh(); }
    catch (error) { setError(error instanceof ApiError ? error.message : "We could not delete your account."); setBusy(false); }
  }

  return (
    <div className="max-w-2xl">
      <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/settings/security"><ArrowLeft className="size-4" aria-hidden="true" />Security settings</Link>
      <div className="mt-6 flex items-center gap-3"><div className="rounded-control bg-primary/10 p-3 text-primary"><UserRound className="size-6" aria-hidden="true" /></div><div><p className="text-sm font-semibold text-primary">Account security</p><h1 className="font-heading text-3xl font-bold text-text">Account actions</h1></div></div>
      <p className="mt-4 text-sm leading-6 text-text-muted">Deactivate your account temporarily or permanently remove it.</p>
      {error && <div className="mt-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">{error}</div>}
      <div className="mt-8 max-w-md rounded-card border border-border bg-surface p-6 shadow-card">
        <label className="block"><span className="mb-2 block text-xs font-medium text-text-muted">Current password</span><input className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" minLength={8} required /></label>
        <button className="mt-5 h-11 w-full rounded-control border border-warning px-5 font-semibold text-warning hover:bg-warning/10 disabled:opacity-60" type="button" onClick={() => void deactivate()} disabled={busy || password.length < 8}>Deactivate account</button>
        <p className="mt-2 text-xs leading-5 text-text-muted">Deactivation disables login while preserving your data.</p>
        <label className="mt-6 block"><span className="mb-2 block text-xs font-medium text-text-muted">Type DELETE to permanently remove your account</span><input className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none focus:border-expense-strong focus:ring-2 focus:ring-expense-strong/20" type="text" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} autoComplete="off" /></label>
        <button className="mt-5 h-11 w-full rounded-control bg-expense-strong px-5 font-semibold text-white hover:bg-expense-strong/90 disabled:opacity-60" type="button" onClick={() => void remove()} disabled={busy || password.length < 8 || confirmation !== "DELETE"}>Delete account permanently</button>
        <p className="mt-2 text-xs leading-5 text-text-muted">This permanently deletes your transactions, custom categories, sessions, and account.</p>
      </div>
    </div>
  );
}
