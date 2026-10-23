"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Eye, EyeOff, LockKeyhole } from "lucide-react";

import { ApiError } from "@/lib/api";
import {
  changePassword,
  getSessions,
  revokeOtherSessions,
  revokeSession,
  type UserSession,
} from "@/lib/auth-api";

export default function SecuritySettingsPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [visible, setVisible] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [sessionError, setSessionError] = useState("");
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isRevokingOthers, setIsRevokingOthers] = useState(false);

  async function loadSessions() {
    setSessionError("");
    try {
      setSessions(await getSessions());
    } catch {
      setSessionError("We could not load your active sessions.");
    } finally {
      setIsLoadingSessions(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    getSessions()
      .then((loadedSessions) => {
        if (!cancelled) {
          setSessions(loadedSessions);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSessionError("We could not load your active sessions.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingSessions(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleRevokeSession(sessionId: string) {
    try {
      await revokeSession(sessionId);
      await loadSessions();
    } catch {
      setSessionError("We could not revoke that session.");
    }
  }

  async function handleRevokeOthers() {
    setIsRevokingOthers(true);
    try {
      await revokeOtherSessions();
      await loadSessions();
    } catch {
      setSessionError("We could not sign out your other sessions.");
    } finally {
      setIsRevokingOthers(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setIsSubmitting(true);

    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
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

  function toggle(field: string) {
    setVisible((current) => ({ ...current, [field]: !current[field] }));
  }

  return (
    <div className="max-w-2xl">
      <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/dashboard">
        <ArrowLeft className="size-4" aria-hidden="true" />
        Back to dashboard
      </Link>
      <div className="mt-6 flex items-center gap-3">
        <div className="rounded-control bg-primary/10 p-3 text-primary">
          <LockKeyhole className="size-6" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-primary">Account security</p>
          <h1 className="font-heading text-3xl font-bold text-text">Change password</h1>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-text-muted">
        Update your password to keep your PaisaLog account secure.
      </p>

      {error && <div className="mt-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">{error}</div>}
      {success && <div className="mt-6 rounded-control bg-income-tint px-4 py-3 text-sm text-income-strong" role="status">{success}</div>}

      <form className="mt-8 max-w-md space-y-5 rounded-card border border-border bg-surface p-6 shadow-card" onSubmit={handleSubmit}>
        {[
          ["current_password", "Current password", currentPassword, setCurrentPassword, "current-password"],
          ["new_password", "New password", newPassword, setNewPassword, "new-password"],
          ["confirm_new_password", "Confirm new password", confirmNewPassword, setConfirmNewPassword, "new-password"],
        ].map(([field, label, value, setter, autoComplete]) => (
          <label className="block" key={field as string}>
            <span className="mb-2 block text-xs font-medium text-text-muted">{label as string}</span>
            <div className="relative">
              <input
                className="h-11 w-full rounded-control border border-border bg-surface px-3 pr-11 text-base outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                type={visible[field as string] ? "text" : "password"}
                value={value as string}
                onChange={(event) => (setter as (value: string) => void)(event.target.value)}
                autoComplete={autoComplete as string}
                minLength={8}
                required
              />
              <button
                className="absolute inset-y-0 right-0 inline-flex w-11 items-center justify-center text-text-muted hover:text-text"
                type="button"
                aria-label={visible[field as string] ? `Hide ${String(label).toLowerCase()}` : `Show ${String(label).toLowerCase()}`}
                onClick={() => toggle(field as string)}
              >
                {visible[field as string] ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
              </button>
            </div>
          </label>
        ))}
        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-60"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Changing password..." : "Change password"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>

      <section className="mt-10 max-w-2xl" aria-labelledby="sessions-heading">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="sessions-heading" className="font-heading text-xl font-bold text-text">
              Active sessions
            </h2>
            <p className="mt-1 text-sm text-text-muted">
              Review devices that are currently signed in to your account.
            </p>
          </div>
          <button
            className="text-sm font-semibold text-primary hover:text-primary-hover disabled:opacity-60"
            type="button"
            onClick={handleRevokeOthers}
            disabled={isRevokingOthers || sessions.filter((session) => !session.is_current).length === 0}
          >
            {isRevokingOthers ? "Signing out..." : "Sign out other sessions"}
          </button>
        </div>

        {sessionError && (
          <div className="mt-4 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
            {sessionError}
          </div>
        )}
        {isLoadingSessions ? (
          <p className="mt-5 text-sm text-text-muted">Loading sessions...</p>
        ) : (
          <div className="mt-5 space-y-3">
            {sessions.map((session) => (
              <div className="rounded-card border border-border bg-surface p-4 shadow-card" key={session.id}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-semibold text-text">
                      {session.is_current ? "This device" : "Signed-in device"}
                    </p>
                    <p className="mt-1 truncate text-sm text-text-muted">
                      {session.user_agent ?? "Unknown browser"}
                    </p>
                    <p className="mt-1 text-xs text-text-muted">
                      Last active {new Date(session.last_used_at).toLocaleString()}
                    </p>
                  </div>
                  {!session.is_current && (
                    <button
                      className="shrink-0 text-sm font-semibold text-expense-strong hover:underline"
                      type="button"
                      onClick={() => void handleRevokeSession(session.id)}
                    >
                      Sign out
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
