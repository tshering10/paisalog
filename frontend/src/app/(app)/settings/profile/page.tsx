"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, UserRound } from "lucide-react";

import { ApiError } from "@/lib/api";
import { getCurrentUser, updateProfile } from "@/lib/auth-api";

export default function ProfileSettingsPage() {
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((user) => setFullName(user.full_name))
      .catch(() => setError("We could not load your profile. Please try again."));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    try {
      const user = await updateProfile({ full_name: fullName });
      setFullName(user.full_name);
      setSuccess("Your profile has been updated.");
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not connect to PaisaLog. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <Link
        className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover"
        href="/dashboard"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to dashboard
      </Link>

      <div className="mt-6 flex items-center gap-3">
        <div className="rounded-control bg-primary/10 p-3 text-primary">
          <UserRound className="size-6" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-primary">Account settings</p>
          <h1 className="font-heading text-3xl font-bold text-text">Your profile</h1>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-text-muted">
        Update the name displayed throughout PaisaLog. Email changes will be
        available after email verification is added.
      </p>

      {error && (
        <div className="mt-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="mt-6 rounded-control bg-income-tint px-4 py-3 text-sm text-income-strong" role="status">
          {success}
        </div>
      )}

      <form
        className="mt-8 max-w-md space-y-5 rounded-card border border-border bg-surface p-6 shadow-card"
        onSubmit={handleSubmit}
      >
        <label className="block">
          <span className="mb-2 block text-xs font-medium text-text-muted">
            Full name
          </span>
          <input
            className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Your full name"
            autoComplete="name"
            minLength={1}
            maxLength={150}
            required
          />
        </label>
        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Saving..." : "Save profile"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>
    </div>
  );
}
