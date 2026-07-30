import "server-only";
import { apiFetch } from "@/lib/api/client";
import type { Session } from "@/lib/auth/session";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

/** The signed-in user's organization name -- resolved fresh per request
 * (never cached on the session/JWT), same "never stale" convention as
 * get_tenant_id server-side. Null for insureflow_admin, who has no org. */
export async function getOrgName(session: Session, token: string | null): Promise<string | null> {
  if (!session.orgId) return null;

  if (session.role === "insurance_company_admin") {
    const company = await apiFetch<InsuranceCompanyOut>(`/insurance-companies/${session.orgId}`, {
      token,
    });
    return company.name;
  }

  const broker = await apiFetch<BrokerOut>(`/brokers/${session.orgId}`, { token });
  return broker.name;
}
