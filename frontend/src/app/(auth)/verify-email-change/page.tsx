"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, CircleDollarSign, XCircle } from "lucide-react";

import { ApiError } from "@/lib/api";
import { confirmEmailChange } from "@/lib/auth-api";

function VerifyEmailChangeContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [isVerifying, setIsVerifying] = useState(Boolean(token));
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState("");

  const tokenError = !token ? "This email change confirmation link is missing its token." : "";
  const displayError = error || tokenError;

  useEffect(() => {
    if (!token) {
      return;
    }

    let isMounted = true;

    confirmEmailChange(token)
      .then(() => {
        if (isMounted) {
          setIsSuccess(true);
        }
      })
      .catch((caughtError) => {
        if (isMounted) {
          setError(
            caughtError instanceof ApiError && caughtError.status === 400
              ? "This email change link is invalid or has expired."
              : caughtError instanceof ApiError && caughtError.status === 409
                ? "This email address is already in use by another account."
                : caughtError instanceof ApiError
                  ? caughtError.message
                  : "We could not confirm your email change. Please try again.",
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
          <h1 className="font-heading text-2xl font-bold text-text">Updating your email...</h1>
          <p className="mt-2 text-sm text-text-muted">Please wait while we confirm your new email address.</p>
        </div>
      )}

      {isSuccess && (
        <div className="text-center">
          <div className="mx-auto mb-4 inline-flex size-14 items-center justify-center rounded-full bg-income-tint text-income-strong">
            <CheckCircle2 className="size-8" aria-hidden="true" />
          </div>
          <h1 className="font-heading text-3xl font-bold text-text">Email updated!</h1>
          <p className="mt-3 text-sm leading-6 text-text-muted">
            Your email address has been updated and verified successfully.
          </p>
          <div className="mt-8">
            <button
              className="flex h-11 w-full items-center justify-center rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover"
              type="button"
              onClick={() => router.push("/dashboard")}
            >
              Go to dashboard
            </button>
          </div>
        </div>
      )}

      {displayError && !isVerifying && !isSuccess && (
        <div>
          <div className="mb-4 inline-flex size-12 items-center justify-center rounded-full bg-expense-tint text-expense-strong">
            <XCircle className="size-6" aria-hidden="true" />
          </div>
          <h1 className="font-heading text-2xl font-bold text-text">Confirmation failed</h1>
          <div className="mt-4 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">
            {displayError}
          </div>

          <div className="mt-6">
            <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/settings/profile">
              <ArrowLeft className="size-4" aria-hidden="true" />
              Return to profile settings
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

export default function VerifyEmailChangePage() {
  return (
    <Suspense fallback={<div className="text-sm text-text-muted">Loading confirmation...</div>}>
      <VerifyEmailChangeContent />
    </Suspense>
  );
}
