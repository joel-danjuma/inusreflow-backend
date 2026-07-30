import Link from "next/link";
import { LoginForm } from "@/components/forms/LoginForm";

/* Matches ui_kits/insureflow-app/LoginScreen.jsx: dark ink brand panel +
 * centered LoginForm card. */
export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ reason?: string; next?: string }>;
}) {
  const { reason, next } = await searchParams;

  return (
    <div className="flex min-h-screen bg-neutral-secondary-soft">
      <aside className="hidden flex-1 flex-col justify-between bg-dark p-14 text-white lg:flex">
        <Link href="/" className="font-display text-2xl font-semibold tracking-tight">
          Insure<span className="text-fg-brand">flow</span>
        </Link>
        <div>
          <h1 className="font-display max-w-[460px] text-[40px] leading-[1.15] font-bold tracking-[-0.5px] text-white">
            Premium collection &amp; settlement, reconciled.
          </h1>
          <p className="mt-4 max-w-[430px] text-lg leading-relaxed text-white/70">
            Track every installment across your broker network and release settlements with a
            full audit trail.
          </p>
        </div>
        <span className="text-xs text-white/50">
          {`© ${new Date().getFullYear()} Insureflow · Lagos, Nigeria`}
        </span>
      </aside>

      <div className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-[400px]">
          {reason === "session_expired" && (
            <div className="mb-5 rounded-base border border-border-warning-subtle bg-warning-soft px-4 py-3 text-sm text-fg-warning">
              Your session has expired. Please sign in again.
            </div>
          )}
          <LoginForm next={next && next.startsWith("/") ? next : "/dashboard"} />

          <p className="mt-6 text-center text-sm text-body">
            New here?{" "}
            <Link href="/onboard/insurer" className="font-semibold text-fg-brand hover:underline">
              Onboard an insurer
            </Link>{" "}
            or{" "}
            <Link href="/onboard/broker" className="font-semibold text-fg-brand hover:underline">
              a broker
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
