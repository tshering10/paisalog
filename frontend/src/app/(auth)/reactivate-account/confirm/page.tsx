"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ArrowLeft, CircleDollarSign } from "lucide-react";

import { ApiError } from "@/lib/api";
import { confirmAccountReactivation } from "@/lib/auth-api";

function Confirmation() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const errorMessage = error || (!token ? "This reactivation link is missing its token." : "");

  async function confirm() {
    setSubmitting(true);
    try {
      await confirmAccountReactivation(token);
      router.replace("/login?reactivated=success");
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "We could not reactivate your account.");
      setSubmitting(false);
    }
  }

  return <div><div className="mb-10 lg:hidden"><div className="bg-hero -mx-6 -mt-12 px-6 py-8 text-white sm:-mx-10 sm:px-10"><div className="flex items-center gap-2 text-xl font-bold"><CircleDollarSign className="size-8 text-cyan-200" aria-hidden="true" /><span>PaisaLog</span></div></div></div><p className="text-sm font-semibold text-primary">Account recovery</p><h1 className="mt-2 font-heading text-3xl font-bold text-text">Reactivate your account</h1><p className="mt-3 text-sm leading-6 text-text-muted">Confirm reactivation to restore access to your existing data.</p>{errorMessage && <div className="mt-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">{errorMessage}</div>}{!errorMessage && <button className="mt-8 h-11 w-full rounded-control bg-primary px-5 font-semibold text-white hover:bg-primary-hover disabled:opacity-60" type="button" onClick={() => void confirm()} disabled={submitting}>{submitting ? "Reactivating..." : "Reactivate account"}</button>}<Link className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/login"><ArrowLeft className="size-4" aria-hidden="true" />Back to login</Link></div>;
}

export default function ReactivationConfirmationPage() {
  return <Suspense fallback={<div className="text-sm text-text-muted">Loading reactivation link...</div>}><Confirmation /></Suspense>;
}
