import { getAuthToken, getSession, type Session } from "@/lib/auth/session";
import { ROLE_LABELS, roleHasPermission } from "@/lib/auth/rbac";
import { getOrgName } from "@/lib/org";
import { apiFetch } from "@/lib/api/client";
import { Money } from "@/components/money/Money";
import { StatCard } from "@/components/dashboard/StatCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { Panel } from "@/components/ui/Panel";
import { CounterpartySelector } from "@/components/dashboard/CounterpartySelector";
import { PaymentRemindersBanner } from "@/components/dashboard/PaymentRemindersBanner";
import { PaymentRemindersSection } from "@/components/dashboard/PaymentRemindersSection";
import { MonthlyTrendsChart } from "@/components/dashboard/MonthlyTrendsChart";
import { ClientPortfolioTable } from "@/components/dashboard/ClientPortfolioTable";
import { RecentPoliciesTable } from "@/components/dashboard/RecentPoliciesTable";
import { BrokerPerformanceTable } from "@/components/dashboard/BrokerPerformanceTable";
import { LatestPaymentsTable } from "@/components/dashboard/LatestPaymentsTable";
import { createSinglePayment } from "@/app/(dashboard)/dashboard/payments/actions";
import { sendPaymentReminders } from "@/app/(dashboard)/dashboard/insurer-actions";
import type { components } from "@/lib/api/types";

type BrokerDashboardSummary = components["schemas"]["BrokerDashboardSummary"];
type BrokerPortfolioPage = components["schemas"]["BrokerPortfolioPage"];
type InstallmentOut = components["schemas"]["InstallmentOut"];
type InsurerDashboardSummary = components["schemas"]["InsurerDashboardSummary"];
type OutstandingPolicyOut = components["schemas"]["OutstandingPolicyOut"];
type RecentPolicyOut = components["schemas"]["RecentPolicyOut"];
type BrokerPerformanceOut = components["schemas"]["BrokerPerformanceOut"];
type LatestPaymentOut = components["schemas"]["LatestPaymentOut"];
type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

const PORTFOLIO_PER_PAGE = 10;
const PORTFOLIO_BASE_PATH = "/dashboard";

/* Small Lucide-style line icons (24px grid, 1.75px stroke) -- matches the
 * design system's documented icon aesthetic without adding a dependency. */
function WalletIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M21 7H3a1 1 0 0 0-1 1v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a1 1 0 0 0-1-1Z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M18 12.5h.01M2 9V6a2 2 0 0 1 2-2h13"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
function TrendingUpIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M22 7 13.5 15.5 8.5 10.5 2 17M16 7h6v6"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
function UsersIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="9" cy="7" r="4" stroke="currentColor" strokeWidth="1.75" />
      <path
        d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
function FileTextIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M14 2v6h6M9 13h6M9 17h6"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; insurer_id?: string; broker_id?: string }>;
}) {
  const [session, token] = await Promise.all([getSession(), getAuthToken()]);

  if (session!.role === "broker_admin" || session!.role === "broker_staff") {
    const { page: pageParam, insurer_id: insurerId } = await searchParams;
    const page = Math.max(1, Number(pageParam) || 1);
    return <BrokerDashboard session={session!} token={token} page={page} insurerId={insurerId} />;
  }

  if (session!.role === "insurance_company_admin") {
    const { broker_id: brokerId } = await searchParams;
    return <InsurerDashboard session={session!} token={token} brokerId={brokerId} />;
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Welcome back" subtitle={`Signed in as ${ROLE_LABELS[session!.role]}.`} />
      <Panel>
        <h2 className="font-display text-base font-semibold text-heading">Getting started</h2>
        <p className="mt-2 text-sm text-body">
          Use the sidebar to navigate the sections available to your role. Every view is scoped
          server-side to your tenant &mdash; you&apos;ll only ever see data your role and
          organization are permitted to access.
        </p>
      </Panel>
    </div>
  );
}

async function BrokerDashboard({
  session,
  token,
  page,
  insurerId,
}: {
  session: Session;
  token: string | null;
  page: number;
  insurerId?: string;
}) {
  const canPay = roleHasPermission(session.role, "create_payment");

  const [summary, portfolio, overdueInstallments, orgName, insurers] = await Promise.all([
    apiFetch<BrokerDashboardSummary>("/brokers/me/dashboard-summary", {
      token,
      searchParams: { insurer_id: insurerId },
    }),
    apiFetch<BrokerPortfolioPage>("/brokers/me/portfolio", {
      token,
      searchParams: { page, per_page: PORTFOLIO_PER_PAGE, insurer_id: insurerId },
    }),
    apiFetch<InstallmentOut[]>("/installments", {
      token,
      searchParams: { status: "overdue", insurer_id: insurerId },
    }),
    getOrgName(session, token),
    apiFetch<InsuranceCompanyOut[]>(`/brokers/${session.orgId}/insurers`, { token }),
  ]);

  return (
    <div>
      <PageHeader
        title="Welcome back"
        subtitle={`Signed in as ${orgName ?? ROLE_LABELS[session.role]}.`}
      />

      <CounterpartySelector
        paramName="insurer_id"
        selectedId={insurerId}
        options={insurers.map((i) => ({ id: i.id, name: i.name }))}
        placeholder="All insurers"
      />

      <div className="mb-6">
        <PaymentRemindersBanner overdueCount={overdueInstallments.length} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Total premiums"
          value={<Money kobo={summary.total_premiums_collected_kobo} />}
          icon={<WalletIcon />}
          accent="teal"
        />
        <StatCard
          label="Client retention rate"
          value={`${summary.client_retention_rate.toLocaleString("en-NG", { maximumFractionDigits: 1 })}%`}
          hint="Active policies as a share of all policies"
          icon={<TrendingUpIcon />}
          accent="green"
        />
        <StatCard
          label="Total commission"
          value={<Money kobo={summary.total_commission_kobo} />}
          icon={<WalletIcon />}
          accent="orange"
        />
      </div>

      <h2 className="mt-8 mb-3 font-display text-base font-semibold text-heading">
        Premium performance
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          label="Total premiums this month"
          value={<Money kobo={summary.total_premiums_this_month_kobo} />}
          icon={<WalletIcon />}
          accent="teal"
        />
        <StatCard
          label="Active clients"
          value={summary.active_clients_count.toLocaleString("en-NG")}
          icon={<UsersIcon />}
          accent="pink"
        />
      </div>

      <div className="mt-6">
        <MonthlyTrendsChart data={summary.monthly_trends} />
      </div>

      <h2 className="mt-8 mb-1 font-display text-base font-semibold text-heading">
        Client portfolio
      </h2>
      <p className="mb-3 text-sm text-body">Every client and policy your team manages.</p>
      <ClientPortfolioTable
        items={portfolio.items}
        total={portfolio.total}
        page={portfolio.page}
        perPage={portfolio.per_page}
        basePath={PORTFOLIO_BASE_PATH}
        canPay={canPay}
        createSinglePayment={createSinglePayment}
      />
    </div>
  );
}

async function InsurerDashboard({
  session,
  token,
  brokerId,
}: {
  session: Session;
  token: string | null;
  brokerId?: string;
}) {
  const [summary, outstanding, recentPolicies, brokerPerformance, latestPayments, orgName, brokers] =
    await Promise.all([
      apiFetch<InsurerDashboardSummary>("/insurance-companies/me/dashboard-summary", {
        token,
        searchParams: { broker_id: brokerId },
      }),
      apiFetch<OutstandingPolicyOut[]>("/insurance-companies/me/outstanding-policies", {
        token,
        searchParams: { broker_id: brokerId },
      }),
      apiFetch<RecentPolicyOut[]>("/insurance-companies/me/recent-policies", {
        token,
        searchParams: { broker_id: brokerId },
      }),
      apiFetch<BrokerPerformanceOut[]>("/insurance-companies/me/broker-performance", {
        token,
        searchParams: { broker_id: brokerId },
      }),
      apiFetch<LatestPaymentOut[]>("/insurance-companies/me/latest-payments", {
        token,
        searchParams: { broker_id: brokerId },
      }),
      getOrgName(session, token),
      apiFetch<BrokerOut[]>(`/insurance-companies/${session.orgId}/brokers`, { token }),
    ]);

  return (
    <div>
      <PageHeader
        title="Welcome back"
        subtitle={`Signed in as ${orgName ?? ROLE_LABELS[session.role]}.`}
      />

      <CounterpartySelector
        paramName="broker_id"
        selectedId={brokerId}
        options={brokers.map((b) => ({ id: b.id, name: b.name }))}
        placeholder="All brokers"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="New policies"
          value={summary.new_policies_count.toLocaleString("en-NG")}
          hint="This month"
          icon={<FileTextIcon />}
          accent="teal"
        />
        <StatCard
          label="Outstanding premiums"
          value={<Money kobo={summary.outstanding_premiums_kobo} />}
          icon={<WalletIcon />}
          accent="orange"
        />
        <StatCard
          label="Total brokers"
          value={summary.total_brokers_count.toLocaleString("en-NG")}
          icon={<UsersIcon />}
          accent="pink"
        />
      </div>

      <div className="mt-6">
        <PaymentRemindersSection
          overdueCount={summary.overdue_policies_count}
          outstandingPolicies={outstanding}
          sendPaymentReminders={sendPaymentReminders}
        />
      </div>

      <h2 className="mt-8 mb-3 font-display text-base font-semibold text-heading">
        Recent policies
      </h2>
      <RecentPoliciesTable items={recentPolicies} />

      <h2 className="mt-8 mb-3 font-display text-base font-semibold text-heading">
        Broker performance
      </h2>
      <BrokerPerformanceTable items={brokerPerformance} />

      <h2 className="mt-8 mb-3 font-display text-base font-semibold text-heading">
        Latest payments
      </h2>
      <LatestPaymentsTable items={latestPayments} />
    </div>
  );
}
