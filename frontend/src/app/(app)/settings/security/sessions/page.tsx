"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, MonitorSmartphone } from "lucide-react";

import { getSessions, revokeOtherSessions, revokeSession, type UserSession } from "@/lib/auth-api";

export default function SessionsPage() {
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [revokingOthers, setRevokingOthers] = useState(false);

  async function loadSessions() {
    setError("");
    try {
      setSessions(await getSessions());
    } catch {
      setError("We could not load your active sessions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    getSessions()
      .then((result) => { if (!cancelled) setSessions(result); })
      .catch(() => { if (!cancelled) setError("We could not load your active sessions."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function revokeOne(id: string) {
    try { await revokeSession(id); await loadSessions(); }
    catch { setError("We could not revoke that session."); }
  }

  async function revokeOthers() {
    setRevokingOthers(true);
    try { await revokeOtherSessions(); await loadSessions(); }
    catch { setError("We could not sign out your other sessions."); }
    finally { setRevokingOthers(false); }
  }

  return (
    <div className="max-w-3xl">
      <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary-hover" href="/settings/security"><ArrowLeft className="size-4" aria-hidden="true" />Security settings</Link>
      <div className="mt-6 flex items-center gap-3"><div className="rounded-control bg-primary/10 p-3 text-primary"><MonitorSmartphone className="size-6" aria-hidden="true" /></div><div><p className="text-sm font-semibold text-primary">Account security</p><h1 className="font-heading text-3xl font-bold text-text">Active sessions</h1></div></div>
      <p className="mt-4 text-sm leading-6 text-text-muted">Review devices that are currently signed in to your account.</p>
      {error && <div className="mt-6 rounded-control bg-expense-tint px-4 py-3 text-sm text-expense-strong" role="alert">{error}</div>}
      <div className="mt-6 flex justify-end"><button className="text-sm font-semibold text-primary hover:text-primary-hover disabled:opacity-60" type="button" onClick={() => void revokeOthers()} disabled={revokingOthers || sessions.filter((session) => !session.is_current).length === 0}>{revokingOthers ? "Signing out..." : "Sign out other sessions"}</button></div>
      {loading ? <p className="mt-5 text-sm text-text-muted">Loading sessions...</p> : <div className="mt-4 space-y-3">{sessions.map((session) => <div className="rounded-card border border-border bg-surface p-4 shadow-card" key={session.id}><div className="flex items-start justify-between gap-4"><div className="min-w-0"><p className="font-semibold text-text">{session.is_current ? "This device" : "Signed-in device"}</p><p className="mt-1 truncate text-sm text-text-muted">{session.user_agent ?? "Unknown browser"}</p><p className="mt-1 text-xs text-text-muted">Last active {new Date(session.last_used_at).toLocaleString()}</p></div>{!session.is_current && <button className="shrink-0 text-sm font-semibold text-expense-strong hover:underline" type="button" onClick={() => void revokeOne(session.id)}>Sign out</button>}</div></div>)}</div>}
    </div>
  );
}
