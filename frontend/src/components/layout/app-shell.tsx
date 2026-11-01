"use client";

import Link from "next/link";
import {
  AlertTriangle,
  BarChart3,
  CircleDollarSign,
  LayoutDashboard,
  LogOut,
  Settings,
  Tags,
  UserRound,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { logout, resendVerificationEmail, type User } from "@/lib/auth-api";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/transactions", label: "Transactions", icon: BarChart3 },
  { href: "/categories", label: "Categories", icon: Tags },
  { href: "/settings/security", label: "Security", icon: Settings },
  { href: "/settings/profile", label: "Profile", icon: UserRound },
];

export function AppShell({
  user,
  children,
}: Readonly<{
  user: User;
  children: React.ReactNode;
}>) {
  const router = useRouter();
  const firstName = user.full_name.split(" ")[0] || user.full_name;
  const [resending, setResending] = useState(false);
  const [resendStatus, setResendStatus] = useState("");

  async function handleResend() {
    setResending(true);
    setResendStatus("");
    try {
      await resendVerificationEmail();
      setResendStatus("A new verification link has been sent to your email.");
    } catch {
      setResendStatus("Could not resend link. Please try again shortly.");
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="min-h-screen bg-background lg:flex">
      <aside className="hidden w-64 shrink-0 bg-sidebar p-5 text-text-on-dark lg:flex lg:flex-col">
        <Link className="flex items-center gap-2 text-lg font-bold text-white" href="/dashboard">
          <CircleDollarSign className="size-7 text-cyan-200" aria-hidden="true" />
          <span>PaisaLog</span>
        </Link>

        <nav className="mt-12 space-y-2" aria-label="Main navigation">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              className="flex items-center gap-3 rounded-control px-3 py-3 text-sm font-medium text-text-on-dark/70 transition hover:bg-sidebar-hover hover:text-white"
              href={href}
            >
              <Icon className="size-5" aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="mt-auto border-t border-white/10 pt-5">
          <p className="truncate text-sm font-semibold text-white">{user.full_name}</p>
          <p className="mt-1 truncate text-xs text-text-on-dark/60">{user.email}</p>
          <button
            className="mt-4 inline-flex items-center gap-2 text-sm text-text-on-dark/70 hover:text-white"
            type="button"
            onClick={async () => {
              await logout();
              router.replace("/login");
              router.refresh();
            }}
          >
            <LogOut className="size-4" aria-hidden="true" />
            Log out
          </button>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-between border-b border-border bg-surface px-5 py-4 lg:hidden">
          <Link className="flex items-center gap-2 font-bold text-text" href="/dashboard">
            <CircleDollarSign className="size-6 text-primary" aria-hidden="true" />
            PaisaLog
          </Link>
          <div className="flex items-center gap-3">
            <span className="max-w-32 truncate text-sm font-semibold text-text">{firstName}</span>
            <button
              className="text-text-muted hover:text-text"
              type="button"
              aria-label="Log out"
              onClick={async () => {
                await logout();
                router.replace("/login");
                router.refresh();
              }}
            >
              <LogOut className="size-5" aria-hidden="true" />
            </button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl p-5 sm:p-8">
          {!user.is_verified && (
            <div className="mb-6 rounded-control border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="size-5 shrink-0 text-amber-600" aria-hidden="true" />
                  <p className="text-sm text-text">
                    <span className="font-semibold">Email verification required:</span> Please check your inbox at{" "}
                    <span className="font-semibold">{user.email}</span>. Financial management features are locked until verified.
                  </p>
                </div>
                <button
                  className="shrink-0 text-sm font-semibold text-primary hover:text-primary-hover disabled:opacity-60"
                  type="button"
                  onClick={() => void handleResend()}
                  disabled={resending}
                >
                  {resending ? "Sending..." : "Resend link"}
                </button>
              </div>
              {resendStatus && (
                <p className="mt-2 text-xs font-medium text-amber-800 dark:text-amber-200">
                  {resendStatus}
                </p>
              )}
            </div>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
