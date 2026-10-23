"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { ArrowLeft, ArrowRight, Eye, EyeOff, KeyRound } from "lucide-react";

import { ApiError } from "@/lib/api";
import { changePassword } from "@/lib/auth-api";

export default function ChangePasswordPage() {
  const [values, setValues] = useState({
    current_password: "",
    new_password: "",
    confirm_new_password: "",
  });
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);
    try {
      await changePassword(values);
      setValues({ current_password: "", new_password: "", confirm_new_password: "" });
      setSuccess("Your password was changed. Please log in again to continue.");
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError && caughtError.status === 400
          ? "Your current password is incorrect."
          : caughtError instanceof ApiError
            ? caughtError.message
            : "We could not connect to PaisaLog. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <BackLink />
      <Heading icon={<KeyRound className="size-6" />} title="Change password" description="Update your password to keep your PaisaLog account secure." />
      {error && <Alert message={error} tone="error" />}
      {success && <Alert message={success} tone="success" />}
      <form className="mt-8 max-w-md space-y-5 rounded-card border border-border bg-surface p-6 shadow-card" onSubmit={handleSubmit}>
        {Object.entries(values).map(([field, value]) => {
          const label = field === "current_password" ? "Current password" : field === "new_password" ? "New password" : "Confirm new password";
          return (
            <label className="block" key={field}>
              <span className="mb-2 block text-xs font-medium text-text-muted">{label}</span>
              <div className="relative">
                <input className="h-11 w-full rounded-control border border-border bg-surface px-3 pr-11 text-base outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" type={visible[field] ? "text" : "password"} value={value} onChange={(event) => setValues((current) => ({ ...current, [field]: event.target.value }))} autoComplete={field === "current_password" ? "current-password" : "new-password"} minLength={8} required />
                <button className="absolute inset-y-0 right-0 inline-flex w-11 items-center justify-center text-text-muted" type="button" aria-label={visible[field] ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`} onClick={() => setVisible((current) => ({ ...current, [field]: !current[field] }))}>
                  {visible[field] ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
                </button>
              </div>
            </label>
          );
        })}
        <button className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white hover:bg-primary-hover disabled:opacity-60" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Changing password..." : "Change password"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>
    </div>
  );
}

function BackLink() {
  return <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/settings/security"><ArrowLeft className="size-4" aria-hidden="true" />Security settings</Link>;
}

function Heading({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return <><div className="mt-6 flex items-center gap-3"><div className="rounded-control bg-primary/10 p-3 text-primary">{icon}</div><div><p className="text-sm font-semibold text-primary">Account security</p><h1 className="font-heading text-3xl font-bold text-text">{title}</h1></div></div><p className="mt-4 text-sm leading-6 text-text-muted">{description}</p></>;
}

function Alert({ message, tone }: { message: string; tone: "error" | "success" }) {
  return <div className={`mt-6 rounded-control px-4 py-3 text-sm ${tone === "error" ? "bg-expense-tint text-expense-strong" : "bg-income-tint text-income-strong"}`} role={tone === "error" ? "alert" : "status"}>{message}</div>;
}
