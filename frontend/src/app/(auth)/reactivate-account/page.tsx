"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";
import { ArrowLeft, ArrowRight, CircleDollarSign } from "lucide-react";

import { ApiError } from "@/lib/api";
import { requestAccountReactivation } from "@/lib/auth-api";

export default function ReactivateAccountPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    try {
      await requestAccountReactivation(email);
      setSubmitted(true);
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "We could not connect to PaisaLog. Please try again.",
      );
    }
  }

  return (
    <div>
      <div className="mb-10 lg:hidden"><div className="bg-hero -mx-6 -mt-12 px-6 py-8 text-white sm:-mx-10 sm:px-10"><div className="flex items-center gap-2 text-xl font-bold"><CircleDollarSign className="size-8 text-cyan-200" aria-hidden="true" /><span>PaisaLog</span></div></div></div>
      <p className="text-sm font-semibold text-primary">Account recovery</p>
      <h1 className="mt-2 font-heading text-3xl font-bold text-text">Reactivate your account</h1>
      <p className="mt-3 text-sm leading-6 text-text-muted">Enter your email to request a secure reactivation link.</p>
      {submitted ? (
        <div className="mt-6 rounded-control bg-income-tint px-4 py-4 text-sm leading-6 text-income-strong" role="status">If a deactivated account exists for that email, a reactivation link has been sent.</div>
      ) : (
        <form className="mt-8 space-y-5" onSubmit={submit}>
          {error && <div className="rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">{error}</div>}
          <label className="block"><span className="mb-2 block text-xs font-medium text-text-muted">Email address</span><input className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none focus:border-primary focus:ring-2 focus:ring-primary/20" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required /></label>
          <button className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white hover:bg-primary-hover" type="submit">Send reactivation link<ArrowRight className="size-4" aria-hidden="true" /></button>
        </form>
      )}
      <Link className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/login"><ArrowLeft className="size-4" aria-hidden="true" />Back to login</Link>
    </div>
  );
}
