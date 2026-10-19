"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { ArrowRight, CircleDollarSign } from "lucide-react";
import { ApiError } from "@/lib/api";
import { login } from "@/lib/auth-api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setFieldErrors({});
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setFieldErrors(caughtError.fieldErrors);
        setError(
          caughtError.status === 401
            ? "Incorrect email or password."
            : caughtError.message,
        );
      } else {
        setError("We could not connect to PaisaLog. Please try again.");
      }
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
          <p className="mt-4 text-sm text-indigo-100">Log every paisa.</p>
        </div>
      </div>

      <div className="mb-8">
        <p className="text-sm font-semibold text-primary">Welcome back</p>
        <h1 className="mt-2 font-heading text-3xl font-bold text-text">
          Log in to PaisaLog
        </h1>
        <p className="mt-3 text-sm leading-6 text-text-muted">
          Continue tracking your money with clarity.
        </p>
      </div>

      {error && (
        <div
          className="mb-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong"
          role="alert"
        >
          {error}
        </div>
      )}

      <form className="space-y-5" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-xs font-medium text-text-muted">
            Email address
          </span>
          <input
            className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            aria-describedby={fieldErrors.email ? "email-error" : undefined}
            required
          />
          {fieldErrors.email && (
            <span id="email-error" className="mt-1 block text-xs text-expense-strong">
              {fieldErrors.email}
            </span>
          )}
        </label>

        <label className="block">
          <span className="mb-2 block text-xs font-medium text-text-muted">
            Password
          </span>
          <input
            className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            aria-describedby={fieldErrors.password ? "password-error" : undefined}
            required
          />
          {fieldErrors.password && (
            <span id="password-error" className="mt-1 block text-xs text-expense-strong">
              {fieldErrors.password}
            </span>
          )}
        </label>

        <button
          className="flex h-11 w-full items-center justify-center gap-2 rounded-control bg-primary px-5 font-semibold text-white transition hover:bg-primary-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Logging in..." : "Log in"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-text-muted">
        New to PaisaLog?{" "}
        <Link className="font-semibold text-primary hover:text-primary-hover" href="/register">
          Create an account
        </Link>
      </p>
    </div>
  );
}
