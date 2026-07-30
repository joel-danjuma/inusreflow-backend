import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { PaymentRemindersSection } from "@/components/dashboard/PaymentRemindersSection";
import { BrokerRemindersTable } from "@/components/dashboard/BrokerRemindersTable";
import { sendPaymentReminders } from "@/app/(dashboard)/dashboard/insurer-actions";
import type { components } from "@/lib/api/types";

type InsurerDashboardSummary = components["schemas"]["InsurerDashboardSummary"];
type OutstandingPolicyOut = components["schemas"]["OutstandingPolicyOut"];
type ReminderOut = components["schemas"]["ReminderOut"];
type InstallmentOut = components["schemas"]["InstallmentOut"];

export default async function RemindersPage() {
  const [session, token] = await Promise.all([getSession(), getAuthToken()]);

  if (session!.role === "insurance_company_admin") {
    const [summary, outstanding] = await Promise.all([
      apiFetch<InsurerDashboardSummary>("/insurance-companies/me/dashboard-summary", { token }),
      apiFetch<OutstandingPolicyOut[]>("/insurance-companies/me/outstanding-policies", { token }),
    ]);

    return (
      <div>
        <h1 className="text-2xl font-semibold text-heading">Reminders</h1>
        <p className="mt-1 text-sm text-body">
          Nudge brokers about installments overdue past the grace period.
        </p>
        <div className="mt-6">
          <PaymentRemindersSection
            overdueCount={summary.overdue_policies_count}
            outstandingPolicies={outstanding}
            sendPaymentReminders={sendPaymentReminders}
          />
        </div>
      </div>
    );
  }

  const [reminders, installments] = await Promise.all([
    apiFetch<ReminderOut[]>("/reminders", { token, searchParams: { broker_id: session!.orgId! } }),
    apiFetch<InstallmentOut[]>("/installments", { token }),
  ]);
  const installmentById = new Map(installments.map((installment) => [installment.id, installment]));

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Reminders</h1>
      <p className="mt-1 text-sm text-body">
        Payment reminders your insurer has sent about overdue installments.
      </p>
      <div className="mt-6">
        <BrokerRemindersTable reminders={reminders} installmentById={installmentById} />
      </div>
    </div>
  );
}
