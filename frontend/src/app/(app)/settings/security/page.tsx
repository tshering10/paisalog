import Link from "next/link";
import { KeyRound, MonitorSmartphone, UserRound } from "lucide-react";

const securityOptions = [
  {
    href: "/settings/security/password",
    title: "Change password",
    description: "Update your password and sign out existing sessions.",
    icon: KeyRound,
  },
  {
    href: "/settings/security/sessions",
    title: "Active sessions",
    description: "Review signed-in devices and revoke access remotely.",
    icon: MonitorSmartphone,
  },
  {
    href: "/settings/security/account",
    title: "Account actions",
    description: "Deactivate or permanently delete your account.",
    icon: UserRound,
  },
];

export default function SecuritySettingsPage() {
  return (
    <div className="max-w-3xl">
      <Link
        className="text-sm font-semibold text-primary hover:text-primary-hover"
        href="/dashboard"
      >
        Back to dashboard
      </Link>
      <p className="mt-6 text-sm font-semibold text-primary">Account security</p>
      <h1 className="mt-2 font-heading text-3xl font-bold text-text">
        Security settings
      </h1>
      <p className="mt-4 text-sm leading-6 text-text-muted">
        Manage your password, signed-in devices, and account status.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {securityOptions.map(({ href, title, description, icon: Icon }) => (
          <Link
            className="rounded-card border border-border bg-surface p-5 shadow-card transition hover:-translate-y-0.5 hover:border-primary/50"
            href={href}
            key={href}
          >
            <Icon className="size-6 text-primary" aria-hidden="true" />
            <h2 className="mt-5 font-semibold text-text">{title}</h2>
            <p className="mt-2 text-sm leading-5 text-text-muted">{description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
