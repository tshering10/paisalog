"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { ArrowRight, CircleDollarSign, Eye, EyeOff } from "lucide-react";
import { ApiError } from "@/lib/api";
import { register } from "@/lib/auth-api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setFieldErrors({});
    setIsSubmitting(true);

    try {
      await register({ full_name: fullName, email, password });
      router.push("/dashboard");
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setFieldErrors(caughtError.fieldErrors);
        setError(
          caughtError.status === 409
            ? "An account with this email already exists."
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
        <p className="text-sm font-semibold text-primary">Start your journey</p>
        <h1 className="mt-2 font-heading text-3xl font-bold text-text">
          Create your account
        </h1>
        <p className="mt-3 text-sm leading-6 text-text-muted">
          Build a clearer picture of your money, one entry at a time.
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
            Full name
          </span>
          <input
            className="h-11 w-full rounded-control border border-border bg-surface px-3 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Your full name"
            autoComplete="name"
            aria-describedby={fieldErrors.full_name ? "full-name-error" : undefined}
            required
          />
          {fieldErrors.full_name && (
            <span id="full-name-error" className="mt-1 block text-xs text-expense-strong">
              {fieldErrors.full_name}
            </span>
          )}
        </label>

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
          <div className="relative">
            <input
              className="h-11 w-full rounded-control border border-border bg-surface px-3 pr-11 text-base outline-none transition placeholder:text-text-muted/70 focus:border-primary focus:ring-2 focus:ring-primary/20"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              minLength={8}
              aria-describedby={fieldErrors.password ? "password-error" : undefined}
              required
            />
            <button
              className="absolute inset-y-0 right-0 inline-flex w-11 items-center justify-center text-text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-primary"
              type="button"
              aria-label={showPassword ? "Hide password" : "Show password"}
              onClick={() => setShowPassword((visible) => !visible)}
            >
              {showPassword ? <EyeOff className="size-5" aria-hidden="true" /> : <Eye className="size-5" aria-hidden="true" />}
            </button>
          </div>
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
          {isSubmitting ? "Creating account..." : "Create account"}
          {!isSubmitting && <ArrowRight className="size-4" aria-hidden="true" />}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-text-muted">
        Already have an account?{" "}
        <Link className="font-semibold text-primary hover:text-primary-hover" href="/login">
          Log in
        </Link>
      </p>
    </div>
  );
}
