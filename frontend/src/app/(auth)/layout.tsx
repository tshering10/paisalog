import { CircleDollarSign, Mountain } from "lucide-react";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <section className="relative hidden overflow-hidden bg-hero p-10 text-white lg:flex lg:flex-col">
        <div className="absolute -right-32 -top-32 size-96 rounded-full bg-accent/30 blur-3xl" />
        <div className="absolute bottom-0 left-0 right-0 h-48 bg-sidebar/20 [clip-path:polygon(0_70%,15%_42%,30%_65%,45%_30%,58%_58%,74%_20%,88%_50%,100%_28%,100%_100%,0_100%)]" />

        <div className="relative flex items-center gap-2 text-xl font-bold">
          <CircleDollarSign className="size-8 text-cyan-200" aria-hidden="true" />
          <span>PaisaLog</span>
        </div>

        <div className="relative mt-auto max-w-lg pb-12">
          <Mountain className="mb-6 size-12 text-cyan-200" aria-hidden="true" />
          <p className="font-heading text-4xl font-extrabold leading-tight">
            Log every paisa.
          </p>
          <p className="mt-4 text-lg text-indigo-100">
            A calmer way to understand your money and your month.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}
