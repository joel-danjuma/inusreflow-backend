"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type CommissionConfigOut = components["schemas"]["CommissionConfigOut"];

function pctToBps(value: FormDataEntryValue | null): number {
  return Math.round(Number(value ?? 0) * 100);
}

export async function createGlobalOrInsurerCommissionConfig(
  _prevState: ActionState<CommissionConfigOut>,
  formData: FormData
): Promise<ActionState<CommissionConfigOut>> {
  const token = await getAuthToken();
  const scope = String(formData.get("scope") ?? "global");
  const insuranceCompanyId = String(formData.get("insurance_company_id") ?? "").trim();

  try {
    const config = await apiFetch<CommissionConfigOut>("/commission-configs", {
      method: "POST",
      token,
      body: {
        scope,
        insurance_company_id: scope === "insurance_company" ? insuranceCompanyId : undefined,
        gtbank_rate_bps: pctToBps(formData.get("gtbank_rate_pct")),
        insureflow_rate_bps: pctToBps(formData.get("insureflow_rate_pct")),
      },
    });
    revalidatePath("/dashboard/commission-config");
    return { status: "success", data: config };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}

export async function createBrokerCommissionConfig(
  _prevState: ActionState<CommissionConfigOut>,
  formData: FormData
): Promise<ActionState<CommissionConfigOut>> {
  const token = await getAuthToken();
  const brokerId = String(formData.get("broker_id") ?? "");

  try {
    const config = await apiFetch<CommissionConfigOut>("/commission-configs", {
      method: "POST",
      token,
      body: {
        scope: "broker",
        broker_id: brokerId,
        gtbank_rate_bps: pctToBps(formData.get("gtbank_rate_pct")),
        insureflow_rate_bps: pctToBps(formData.get("insureflow_rate_pct")),
        broker_rate_bps: pctToBps(formData.get("broker_rate_pct")),
      },
    });
    revalidatePath("/dashboard/commission-config");
    return { status: "success", data: config };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}
