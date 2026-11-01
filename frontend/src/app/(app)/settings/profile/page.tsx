"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Mail, UserRound } from "lucide-react";

import { ApiError } from "@/lib/api";
import { getCurrentUser, requestEmailChange, updateProfile, type User } from "@/lib/auth-api";

export default function ProfileSettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [fullName, setFullName] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);

  // Email change state
  const [newEmail, setNewEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailChangeError, setEmailChangeError] = useState("");
  const [emailChangeSuccess, setEmailChangeSuccess] = useState("");
  const [isSubmittingEmailChange, setIsSubmittingEmailChange] = useState(false);

  useEffect(() => {
    getCurrentUser()
      .then((loadedUser) => {
        setUser(loadedUser);
        setFullName(loadedUser.full_name);
      })
      .catch(() => setProfileError("We could not load your profile. Please try again."));
  }, []);

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError("");
    setProfileSuccess("");
    setIsSubmittingProfile(true);

    try {
      const updatedUser = await updateProfile({ full_name: fullName });
      setUser(updatedUser);
      setFullName(updatedUser.full_name);
      setProfileSuccess("Your profile has been updated.");
    } catch (caughtError) {
      setProfileError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not connect to PaisaLog. Please try again.",
      );
    } finally {
      setIsSubmittingProfile(false);
    }
  }

  async function handleEmailChangeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEmailChangeError("");
    setEmailChangeSuccess("");
    setIsSubmittingEmailChange(true);

    try {
      await requestEmailChange({ new_email: newEmail, password });
      setEmailChangeSuccess(
        `A confirmation link has been sent to ${newEmail}. Please click it to complete your email change.`,
      );
      setPassword("");
      setNewEmail("");
      // Refresh user to show pending_email
      const refreshedUser = await getCurrentUser();
      setUser(refreshedUser);
    } catch (caughtError) {
      setEmailChangeError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not request email change. Please try again.",
      );
    } finally {
      setIsSubmittingEmailChange(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-10">
      <div>
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
          Update your personal information and account email address.
        </p>
      </div>

      {/* Name change section */}
      <section className="rounded-card border border-border bg-surface p-6 shadow-card">
        <h2 className="text-lg font-bold text-text">Display name</h2>
        <p className="mt-1 text-sm text-text-muted">
          Update the name displayed throughout your PaisaLog workspace.
        </p>

        {profileError && (
          <div className="mt-4 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
            {profileError}
          </div>
        )}
        {profileSuccess && (
          <div className="mt-4 rounded-control bg-income-tint px-4 py-3 text-sm text-income-strong" role="status">
            {profileSuccess}
          </div>
        )}

        <form className="mt-6 space-y-5" onSubmit={handleProfileSubmit}>
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
            className="flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmittingProfile}
          >
            {isSubmittingProfile ? "Saving..." : "Save name"}
            {!isSubmittingProfile && <ArrowRight className="size-4" aria-hidden="true" />}
          </button>
        </form>
      </section>

      {/* Email change section */}
      <section className="rounded-card border border-border bg-surface p-6 shadow-card">
        <div className="flex items-center gap-3">
          <div className="rounded-control bg-primary/10 p-2 text-primary">
            <Mail className="size-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-text">Email address</h2>
            <p className="text-sm text-text-muted">
              Current email: <span className="font-semibold text-text">{user?.email}</span>
            </p>
          </div>
        </div>

        {user?.pending_email && (
          <div className="mt-4 rounded-control border border-amber-500/30 bg-amber-500/10 p-4 text-sm leading-6 text-text">
            <p className="font-semibold text-amber-800 dark:text-amber-200">
              Pending email verification
            </p>
            <p className="mt-1">
              A verification link was sent to <span className="font-semibold">{user.pending_email}</span>.
              Your current email remains active until confirmed.
            </p>
          </div>
        )}

        {emailChangeError && (
          <div className="mt-4 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
            {emailChangeError}
          </div>
        )}
        {emailChangeSuccess && (
          <div className="mt-4 rounded-control bg-income-tint px-4 py-3 text-sm text-income-strong" role="status">
            {emailChangeSuccess}
          </div>
        )}

        <form className="mt-6 space-y-5" onSubmit={handleEmailChangeSubmit}>
          <label className="block">
            <span className="mb-2 block text-xs font-medium text-text-muted">
              New email address
            </span>
            <input
              className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
              type="email"
              value={newEmail}
              onChange={(event) => setNewEmail(event.target.value)}
              placeholder="new@example.com"
              required
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-xs font-medium text-text-muted">
              Current password
            </span>
            <input
              className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter current password to confirm"
              autoComplete="current-password"
              required
            />
          </label>

          <button
            className="flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmittingEmailChange}
          >
            {isSubmittingEmailChange ? "Sending verification..." : "Change email"}
            {!isSubmittingEmailChange && <ArrowRight className="size-4" aria-hidden="true" />}
          </button>
        </form>
      </section>
    </div>
  );
}
