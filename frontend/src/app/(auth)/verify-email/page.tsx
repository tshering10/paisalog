"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, CircleDollarSign, XCircle } from "lucide-react";

import { ApiError } from "@/lib/api";
import { resendVerificationEmail, verifyEmail } from "@/lib/auth-api";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [isVerifying, setIsVerifying] = useState(Boolean(token));
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");
  const [emailInput, setEmailInput] = useState("");
  const [isResending, setIsResending] = useState(false);
  const [resendStatus, setResendStatus] = useState("");

  const tokenError = !token ? "This verification link is missing its token." : "";
  const displayError = error || tokenError;

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    verifyEmail(token)
      .then(() => {
        if (isMounted) {
          setIsSuccess(true);
        }
      })
      .catch((caughtError) => {
        if (isMounted) {
          setError(
            caughtError instanceof ApiError && caughtError.status === 400
              ? "This verification link is invalid or has expired."
              : caughtError instanceof ApiError
                ? caughtError.message
                : "We could not verify your email. Please try again.",
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsVerifying(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [token]);

  async function handleResend(event: React.FormEvent) {
    event.preventDefault();
    if (!emailInput) return;

    setIsResending(true);
    setResendStatus("");
    try {
      await resendVerificationEmail(emailInput);
      setResendStatus("If an unverified account exists for that email, a verification link has been sent.");
    } catch {
      setResendStatus("Could not send verification email. Please try again shortly.");
    } finally {
      setIsResending(false);
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

      {isVerifying && (
        <div className="text-center">
          <div className="mx-auto mb-4 size-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <h1 className="font-heading text-2xl font-bold text-text">Verifying your email...</h1>
          <p className="mt-2 text-sm text-text-muted">Please wait while we confirm your email address.</p>
        </div>
      )}

      {isSuccess && (
        <div className="text-center">
          <div className="mx-auto mb-4 inline-flex size-14 items-center justify-center rounded-full bg-income-tint text-income-strong">
            <CheckCircle2 className="size-8" aria-hidden="true" />
          </div>
          <h1 className="font-heading text-3xl font-bold text-text">Email verified!</h1>
          <p className="mt-3 text-sm leading-6 text-text-muted">
            Your email has been successfully verified. You now have complete access to PaisaLog.
          </p>
          <div className="mt-8 space-y-3">
            <button
              className="flex h-11 w-full items-center justify-center rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover"
              type="button"
              onClick={() => router.push("/dashboard")}
            >
              Go to dashboard
            </button>
            <Link
              className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover"
              href="/login?verified=success"
            >
              Sign in to another account
            </Link>
          </div>
        </div>
      )}

      {displayError && !isVerifying && !isSuccess && (
        <div>
          <div className="mb-4 inline-flex size-12 items-center justify-center rounded-full bg-expense-tint text-expense-strong">
            <XCircle className="size-6" aria-hidden="true" />
          </div>
          <h1 className="font-heading text-2xl font-bold text-text">Verification failed</h1>
          <div className="mt-4 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
            {displayError}
          </div>

          <div className="mt-8 rounded-card border border-border bg-surface p-5 shadow-card">
            <h2 className="text-sm font-semibold text-text">Request a new verification link</h2>
            <p className="mt-1 text-xs text-text-muted">
              Enter your registered email address and we will send you a fresh link.
            </p>
            {resendStatus && (
              <div className="mt-3 rounded-control bg-income-tint px-3 py-2 text-xs text-income-strong">
                {resendStatus}
              </div>
            )}
            <form className="mt-4 space-y-3" onSubmit={handleResend}>
              <input
                className="h-10 w-full rounded-control border border-border bg-surface px-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
                type="email"
                placeholder="you@example.com"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                required
              />
              <button
                className="h-10 w-full rounded-control bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover disabled:opacity-60"
                type="submit"
                disabled={isResending}
              >
                {isResending ? "Sending..." : "Send new link"}
              </button>
            </form>
          </div>

          <div className="mt-6">
            <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/login">
              <ArrowLeft className="size-4" aria-hidden="true" />
              Back to login
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="text-sm text-text-muted">Loading verification...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
