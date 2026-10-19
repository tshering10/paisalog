import { ArrowRight, CircleDollarSign, ShieldCheck, Sparkles } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden">
      <section className="relative isolate">
        <div className="absolute inset-0 -z-10 bg-hero" />
        <div className="absolute right-[-8rem] top-[-10rem] -z-10 size-[28rem] rounded-full bg-accent/30 blur-3xl" />

        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 lg:px-8">
          <div className="flex items-center gap-2 text-lg font-bold text-white">
            <CircleDollarSign className="size-7 text-cyan-200" aria-hidden="true" />
            <span>PaisaLog</span>
          </div>
          <a
            className="rounded-control border border-white/30 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            href="/login"
          >
            Log in
          </a>
        </nav>

        <div className="mx-auto grid max-w-6xl gap-12 px-6 pb-24 pt-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:px-8 lg:pb-32 lg:pt-24">
          <div>
            <p className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-sm font-medium text-cyan-100 ring-1 ring-white/20">
              <Sparkles className="size-4" aria-hidden="true" />
              Personal finance, made clear
            </p>
            <h1 className="max-w-2xl font-heading text-4xl font-extrabold tracking-tight text-white sm:text-6xl">
              Log every paisa.
              <span className="mt-2 block text-cyan-100">Understand every month.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-indigo-100 sm:text-lg">
              Track income, expenses, and the habits behind them in one calm,
              focused space.
            </p>
            <a
              className="mt-8 inline-flex items-center gap-2 rounded-control bg-white px-5 py-3 font-semibold text-primary shadow-hero transition hover:bg-indigo-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              href="/register"
            >
              Create your account
              <ArrowRight className="size-4" aria-hidden="true" />
            </a>
          </div>

          <div className="rounded-modal border border-white/20 bg-white/10 p-5 shadow-hero backdrop-blur-sm sm:p-6">
            <div className="rounded-card bg-surface p-6 shadow-card">
              <p className="text-sm font-medium text-text-muted">Net this month</p>
              <p className="money mt-2 font-heading text-4xl font-extrabold text-text">
                Rs 24,850.00
              </p>
              <div className="mt-8 grid grid-cols-2 gap-4">
                <div className="rounded-control bg-income-tint p-4">
                  <p className="text-xs font-medium text-income-strong">Income</p>
                  <p className="money mt-1 text-lg font-bold text-income-strong">
                    Rs 45,000.00
                  </p>
                </div>
                <div className="rounded-control bg-expense-tint p-4">
                  <p className="text-xs font-medium text-expense-strong">Expenses</p>
                  <p className="money mt-1 text-lg font-bold text-expense-strong">
                    Rs 20,150.00
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 py-12 sm:grid-cols-3 lg:px-8">
        {[
          ["Simple tracking", "Record income and expenses without the clutter."],
          ["Useful insights", "See where your monthly spending actually goes."],
          ["Private by design", "Your financial data stays scoped to your account."],
        ].map(([title, description]) => (
          <div key={title} className="rounded-card border border-border bg-surface p-5 shadow-card">
            <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
            <h2 className="mt-4 font-heading text-base font-bold text-text">{title}</h2>
            <p className="mt-2 text-sm leading-6 text-text-muted">{description}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
