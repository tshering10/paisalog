"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useState } from "react";
import { ArrowLeft, ArrowRight, CircleDollarSign, Eye, EyeOff } from "lucide-react";

import { ApiError } from "@/lib/api";
import { confirmPasswordReset } from "@/lib/auth-api";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!token) {
      setError("This password reset link is missing its token.");
      return;
    }

    setIsSubmitting(true);
    try {
      await confirmPasswordReset({
        token,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      router.replace("/login?reset=success");
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError && caughtError.status === 400
          ? "This reset link is invalid or has expired. Please request a new one."
          : caughtError instanceof ApiError
            ? caughtError.message
            : "We could not connect to PaisaLog. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div>
      <div className="mb-10 lg:hidden">
        <div className="bg-hero -mx-6 -mt-12 px-6 py-8 text-white sm:-mx-10 sm:px-10">
          <div className="flex items-center gap-2 text-xl font-bold">
            <CircleDollarSign className="size-8 text-cyan-200" aria-hidden="true" />
            <span>PaisaLog</span>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <p className="text-sm font-semibold text-primary">Account recovery</p>
        <h1 className="mt-2 font-heading text-3xl font-bold text-text">
          Create a new password
        </h1>
        <p className="mt-3 text-sm leading-6 text-text-muted">
          Choose a strong password with at least 8 characters.
        </p>
      </div>

      {error && (
        <div className="mb-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
          {error}
        </div>
      )}

      <form className="space-y-5" onSubmit={handleSubmit}>
        <PasswordField
          label="New password"
          value={newPassword}
          onChange={setNewPassword}
          visible={showPassword}
          onToggle={() => setShowPassword((visible) => !visible)}
          autoComplete="new-password"
        />
        <PasswordField
          label="Confirm new password"
          value={confirmNewPassword}
          onChange={setConfirmNewPassword}
          visible={showConfirmation}
          onToggle={() => setShowConfirmation((visible) => !visible)}
          autoComplete="new-password"
        />
        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Updating password..." : "Update password"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>

      <Link className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/login">
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to login
      </Link>
    </div>
  );
}

function PasswordField({
  label,
  value,
  onChange,
  visible,
  onToggle,
  autoComplete,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  visible: boolean;
  onToggle: () => void;
  autoComplete: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium text-text-muted">{label}</span>
      <div className="relative">
        <input
          className="h-11 w-full rounded-control border border-border bg-surface px-3 pr-11 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
          type={visible ? "text" : "password"}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          autoComplete={autoComplete}
          minLength={8}
          required
        />
        <button
          className="absolute inset-y-0 right-0 inline-flex w-11 items-center justify-center text-text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-primary"
          type="button"
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          onClick={onToggle}
        >
          {visible ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
        </button>
      </div>
    </label>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="text-sm text-text-muted">Loading reset link...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
