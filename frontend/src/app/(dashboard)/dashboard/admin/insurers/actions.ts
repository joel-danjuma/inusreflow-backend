"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];

export async function approveInsurer(
  companyId: string,
  _prevState: ActionState<InsuranceCompanyOut>,
  _formData: FormData
): Promise<ActionState<InsuranceCompanyOut>> {
  const token = await getAuthToken();
  try {
    const result = await apiFetch<InsuranceCompanyOut>(
      `/admin/insurance-companies/${companyId}/approve`,
      { method: "PATCH", token }
    );
    revalidatePath("/dashboard/admin/insurers");
    return { status: "success", data: result };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}

export async function rejectInsurer(
  companyId: string,
  _prevState: ActionState<undefined>,
  formData: FormData
): Promise<ActionState<undefined>> {
  const token = await getAuthToken();
  const reason = String(formData.get("reason") ?? "").trim();
  try {
    await apiFetch(`/admin/insurance-companies/${companyId}/reject`, {
      method: "PATCH",
      token,
      body: { reason },
    });
    revalidatePath("/dashboard/admin/insurers");
    return { status: "success" };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}

export async function setInsurerParent(
  companyId: string,
  _prevState: ActionState<InsuranceCompanyOut>,
  formData: FormData
): Promise<ActionState<InsuranceCompanyOut>> {
  const token = await getAuthToken();
  const parentCompanyId = String(formData.get("parent_company_id") ?? "").trim();
  try {
    const company = await apiFetch<InsuranceCompanyOut>(
      `/admin/insurance-companies/${companyId}/set-parent`,
      {
        method: "PATCH",
        token,
        body: { parent_company_id: parentCompanyId || null },
      }
    );
    revalidatePath(`/dashboard/admin/insurers/${companyId}`);
    revalidatePath("/dashboard/admin/insurers");
    return { status: "success", data: company };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}

export async function setSettlementAccount(
  companyId: string,
  _prevState: ActionState<InsuranceCompanyOut>,
  formData: FormData
): Promise<ActionState<InsuranceCompanyOut>> {
  const token = await getAuthToken();
  const bankCode = String(formData.get("bank_code") ?? "").trim();
  const accountNumber = String(formData.get("account_number") ?? "").trim();
  try {
    const company = await apiFetch<InsuranceCompanyOut>(
      `/insurance-companies/${companyId}/settlement-account`,
      { method: "POST", token, body: { bank_code: bankCode, account_number: accountNumber } }
    );
    revalidatePath(`/dashboard/admin/insurers/${companyId}`);
    revalidatePath("/dashboard/settings");
    return { status: "success", data: company };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}
