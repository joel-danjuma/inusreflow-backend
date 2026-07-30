"use server";

import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type PolicyOut = components["schemas"]["PolicyOut"];

export async function createPolicy(
  _prevState: ActionState<PolicyOut>,
  formData: FormData
): Promise<ActionState<PolicyOut>> {
  const token = await getAuthToken();
  const brokerId = String(formData.get("broker_id") ?? "");
  const referenceNumber = String(formData.get("reference_number") ?? "").trim();
  const policyholderId = String(formData.get("policyholder_id") ?? "");
  const premiumNaira = String(formData.get("premium_amount_naira") ?? "").trim();
  const premiumFrequency = String(formData.get("premium_frequency") ?? "");
  const startDate = String(formData.get("start_date") ?? "");
  const policyTypeSelect = String(formData.get("policy_type") ?? "").trim();
  const policyTypeOther = String(formData.get("policy_type_other") ?? "").trim();
  const policyType = policyTypeSelect || policyTypeOther || "GENERIC";

  const policyName = String(formData.get("policy_name") ?? "").trim();
  const durationMonths = String(formData.get("duration_months") ?? "").trim();
  const coverageAmountNaira = String(formData.get("coverage_amount_naira") ?? "").trim();
  const coverageItems = String(formData.get("coverage_items") ?? "").trim();
  const beneficiaries = String(formData.get("beneficiaries") ?? "").trim();
  const brokerNotes = String(formData.get("broker_notes") ?? "").trim();
  const internalTags = String(formData.get("internal_tags") ?? "").trim();

  const premiumAmountKobo = Math.round(Number(premiumNaira) * 100);

  let policy: PolicyOut;
  try {
    policy = await apiFetch<PolicyOut>("/policies", {
      method: "POST",
      token,
      body: {
        broker_id: brokerId,
        reference_number: referenceNumber,
        policyholder_id: policyholderId,
        premium_amount_kobo: premiumAmountKobo,
        premium_frequency: premiumFrequency,
        start_date: startDate,
        policy_type: policyType,
        policy_name: policyName || undefined,
        duration_months: durationMonths ? Math.round(Number(durationMonths)) : undefined,
        coverage_amount_kobo: coverageAmountNaira
          ? Math.round(Number(coverageAmountNaira) * 100)
          : undefined,
        coverage_items: coverageItems || undefined,
        beneficiaries: beneficiaries || undefined,
        broker_notes: brokerNotes || undefined,
        internal_tags: internalTags || undefined,
      },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }

  redirect(`/dashboard/policies/${policy.id}`);
}
