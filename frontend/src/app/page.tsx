import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";

/* Insureflow Design System (claude.ai/design 940d93f3) marketing patterns:
 * hero-band, eyebrow-uppercase, card-feature-light, cta-band-dark, footer.
 * No fabricated stats, testimonials, trust badges, or client logos -- only
 * real, built platform characteristics, matching this page's prior stance. */

type Accent = "teal" | "green" | "yellow" | "orange" | "pink";

const FEATURES: { title: string; body: string; accent: Accent; icon: React.ReactNode }[] = [
  {
    title: "Single & bulk premium collection",
    accent: "teal",
    body: "Collect one installment or hundreds in a single action via bank transfer to a permanent virtual account. Upload an Excel of debit-note references and the platform matches every premium for you — no more searching line by line.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="2" y="5" width="20" height="14" rx="2" />
        <line x1="2" y1="10" x2="22" y2="10" />
      </svg>
    ),
  },
  {
    title: "Automatic commission-split settlement",
    accent: "green",
    body: "Every successful payment posts a balanced double-entry ledger record and settles to the insurer in real time, net of the commission split — versioned rates that never rewrite history.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M16 3h5v5" />
        <path d="M8 21H3v-5" />
        <path d="M21 3l-7 7" />
        <path d="M3 21l7-7" />
      </svg>
    ),
  },
  {
    title: "Multi-tenant onboarding & roles",
    accent: "yellow",
    body: "Insurers and brokerages onboard with manual platform approval, and every account operates within a strict permission ceiling — admins, broker admins, and broker staff each see exactly what their role allows.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    title: "Reminders & reconciliation",
    accent: "orange",
    body: "Overdue premiums surface automatically after the grace period, one click nudges every broker at once, and a scheduled reconciliation job re-verifies any payment a webhook ever missed.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
    ),
  },
  {
    title: "Audit trail & data isolation",
    accent: "pink",
    body: "Every approval, rate change, and financial state transition is written to an immutable audit log, and tenant data is isolated all the way down to database row-level security.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    title: "Policy portfolio at a glance",
    accent: "teal",
    body: "Live dashboards for both sides: brokers track premiums, retention, and collections; insurers monitor new policies, outstanding premiums, and broker performance — straight from the database.",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
];

const STEPS = [
  {
    step: "1",
    title: "Onboard & get approved",
    body: "An insurer or brokerage signs up, the platform team reviews and approves, and the broker receives a permanent virtual bank account for collections.",
  },
  {
    step: "2",
    title: "Create policies",
    body: "Brokers register policyholders and policies — auto, health, life, and more — and the platform generates the recurring premium installment schedule.",
  },
  {
    step: "3",
    title: "Collect premiums",
    body: "Policyholders pay by simple bank transfer. Collect installments one at a time, in filtered batches by policy type, or via Excel upload for hundreds at once.",
  },
  {
    step: "4",
    title: "Settle automatically",
    body: "The moment a payment verifies, commission is split and the insurer is settled — with the ledger, audit trail, and dashboards updated in real time.",
  },
];

const ACCENT_ICON_CLASSES: Record<Accent, string> = {
  teal: "bg-accent-teal/12 text-accent-teal",
  green: "bg-accent-green/12 text-accent-green",
  yellow: "bg-accent-yellow/12 text-accent-yellow",
  orange: "bg-accent-orange/12 text-accent-orange",
  pink: "bg-accent-pink/12 text-accent-pink",
};

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-display mb-4 text-xs font-semibold tracking-[1px] text-heading uppercase">
      {children}
    </p>
  );
}

export default async function RootPage() {
  const session = await getSession();
  if (session) redirect("/dashboard");

  return (
    <div className="bg-neutral-primary-soft">
      {/* Navbar */}
      <header className="sticky top-0 z-40 border-b border-border-default bg-neutral-primary-soft/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-6">
          <span className="font-display text-lg font-semibold tracking-tight text-heading">
            Insure<span className="text-fg-brand">flow</span>
          </span>
          <nav aria-label="Main" className="flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-full border border-transparent px-4 py-2.5 text-sm font-semibold text-heading transition-colors hover:bg-neutral-secondary-soft focus-visible:ring-4 focus-visible:ring-neutral-tertiary focus-visible:outline-none"
            >
              Sign in
            </Link>
            <Link
              href="/onboard/insurer"
              className="rounded-full border border-transparent bg-brand px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-strong focus-visible:ring-4 focus-visible:ring-brand-medium focus-visible:outline-none"
            >
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main>
        {/* Hero band */}
        <section className="bg-neutral-primary-soft pt-24 pb-20 sm:pt-28">
          <div className="mx-auto max-w-[840px] px-6 text-center">
            <Eyebrow>Premium collection &amp; settlement</Eyebrow>
            <h1 className="font-display text-[44px] leading-[1.05] font-bold tracking-[-1px] text-heading sm:text-[56px] sm:tracking-[-1.5px] lg:text-[64px] lg:leading-[68px]">
              Every premium collected. Every kobo accounted for.
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-body">
              Insureflow connects insurance companies and their brokers on one platform: premiums
              come in by bank transfer, commissions split automatically, and insurers get settled
              in real time &mdash; with a complete audit trail behind every transaction.
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/onboard/insurer"
                className="rounded-full border border-transparent bg-brand px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-strong focus-visible:ring-4 focus-visible:ring-brand-medium focus-visible:outline-none"
              >
                Onboard your company
              </Link>
              <Link
                href="/onboard/broker"
                className="rounded-full border border-border-default-medium bg-neutral-primary-soft px-6 py-3.5 text-base font-semibold text-heading transition-colors hover:bg-neutral-secondary-soft focus-visible:ring-4 focus-visible:ring-neutral-tertiary-soft focus-visible:outline-none"
              >
                Register a brokerage
              </Link>
            </div>

            {/* Trust row -- real platform characteristics only, no fabricated badges */}
            <div className="mt-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs font-medium text-body-subtle uppercase tracking-wide">
              <span>Row-level tenant isolation</span>
              <span>Immutable audit trail</span>
              <span>Real-time settlement</span>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="bg-neutral-secondary-soft py-24 sm:py-28">
          <div className="mx-auto max-w-[1200px] px-6">
            <div className="mx-auto mb-14 max-w-2xl text-center">
              <Eyebrow>What you get</Eyebrow>
              <h2 className="font-display text-[32px] leading-[1.1] font-bold tracking-[-0.5px] text-heading sm:text-[40px]">
                Built for how premiums actually move
              </h2>
              <p className="mx-auto mt-5 text-lg leading-relaxed text-body">
                From onboarding to settlement, every step is designed around the real workflow
                between insurers, brokers, and policyholders.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-base border border-border-default bg-neutral-primary-soft p-8"
                >
                  <div
                    className={`mb-5 inline-flex h-12 w-12 items-center justify-center rounded-full ${ACCENT_ICON_CLASSES[feature.accent]}`}
                  >
                    {feature.icon}
                  </div>
                  <h3 className="font-display text-xl font-semibold text-heading">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-base leading-relaxed text-body">{feature.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section className="bg-neutral-primary-soft py-24 sm:py-28">
          <div className="mx-auto max-w-[1200px] px-6">
            <div className="mx-auto mb-14 max-w-2xl text-center">
              <Eyebrow>The workflow</Eyebrow>
              <h2 className="font-display text-[32px] leading-[1.1] font-bold tracking-[-0.5px] text-heading sm:text-[40px]">
                How it works
              </h2>
            </div>

            <ol className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
              {STEPS.map((item) => (
                <li
                  key={item.step}
                  className="rounded-base border border-border-default bg-neutral-secondary-soft p-8"
                >
                  <span
                    aria-hidden="true"
                    className="font-display mb-5 inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-softer text-base font-bold text-fg-brand-strong"
                  >
                    {item.step}
                  </span>
                  <h3 className="text-lg font-semibold text-heading">{item.title}</h3>
                  <p className="mt-3 text-base leading-relaxed text-body">{item.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* CTA band (dark) */}
        <section className="bg-dark py-20 sm:py-24">
          <div className="mx-auto max-w-[720px] px-6 text-center">
            <h2 className="font-display text-[32px] leading-[1.1] font-bold tracking-[-0.5px] text-white sm:text-[40px]">
              Ready to streamline your premium collections?
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-white/70">
              Onboard your insurance company or brokerage today. Approval is reviewed by the
              Insureflow team, and your dashboard is ready the moment you&apos;re in.
            </p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/onboard/insurer"
                className="rounded-full border border-transparent bg-brand px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-strong focus-visible:ring-4 focus-visible:ring-brand-medium focus-visible:outline-none"
              >
                Get started
              </Link>
              <Link
                href="/login"
                className="rounded-full border border-white/20 px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-white/10 focus-visible:ring-4 focus-visible:ring-white/20 focus-visible:outline-none"
              >
                Sign in instead
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer (dark ink) */}
      <footer className="bg-dark">
        <div className="mx-auto flex max-w-[1200px] flex-col items-center justify-between gap-4 px-6 py-10 sm:flex-row">
          <span className="font-display text-sm font-semibold text-white">
            Insure<span className="text-fg-brand">flow</span>
          </span>
          <nav aria-label="Footer" className="flex flex-wrap items-center justify-center gap-6">
            <Link href="/login" className="text-sm text-white/70 hover:text-white hover:underline">
              Sign in
            </Link>
            <Link
              href="/onboard/insurer"
              className="text-sm text-white/70 hover:text-white hover:underline"
            >
              Onboard an insurer
            </Link>
            <Link
              href="/onboard/broker"
              className="text-sm text-white/70 hover:text-white hover:underline"
            >
              Onboard a broker
            </Link>
          </nav>
          <span className="text-sm text-white/50">&copy; {new Date().getFullYear()} Insureflow</span>
        </div>
      </footer>
    </div>
  );
}
