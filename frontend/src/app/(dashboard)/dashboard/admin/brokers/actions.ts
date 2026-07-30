"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BrokerOut = components["schemas"]["BrokerOut"];
type BrokerInsurerAssignmentOut = components["schemas"]["BrokerInsurerAssignmentOut"];

export async function approveBroker(
  brokerId: string,
  _prevState: ActionState<BrokerOut>,
  _formData: FormData
): Promise<ActionState<BrokerOut>> {
  const token = await getAuthToken();
  try {
    const result = await apiFetch<BrokerOut>(`/admin/brokers/${brokerId}/approve`, {
      method: "PATCH",
      token,
    });
    revalidatePath("/dashboard/admin/brokers");
    return { status: "success", data: result };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}

export async function rejectBroker(
  brokerId: string,
  _prevState: ActionState<undefined>,
  formData: FormData
): Promise<ActionState<undefined>> {
  const token = await getAuthToken();
  const reason = String(formData.get("reason") ?? "").trim();
  try {
    await apiFetch(`/admin/brokers/${brokerId}/reject`, {
      method: "PATCH",
      token,
      body: { reason },
    });
    revalidatePath("/dashboard/admin/brokers");
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

export async function assignBrokerToInsurer(
  brokerId: string,
  _prevState: ActionState<BrokerInsurerAssignmentOut>,
  formData: FormData
): Promise<ActionState<BrokerInsurerAssignmentOut>> {
  const token = await getAuthToken();
  const insuranceCompanyId = String(formData.get("insurance_company_id") ?? "");
  try {
    const assignment = await apiFetch<BrokerInsurerAssignmentOut>(
      `/admin/brokers/${brokerId}/assign-insurer`,
      { method: "POST", token, body: { insurance_company_id: insuranceCompanyId } }
    );
    revalidatePath("/dashboard/admin/brokers");
    revalidatePath(`/dashboard/admin/brokers/${brokerId}`);
    return { status: "success", data: assignment };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}

export async function unassignBrokerFromInsurer(
  brokerId: string,
  insuranceCompanyId: string,
  _prevState: ActionState<BrokerInsurerAssignmentOut>,
  _formData: FormData
): Promise<ActionState<BrokerInsurerAssignmentOut>> {
  const token = await getAuthToken();
  try {
    const assignment = await apiFetch<BrokerInsurerAssignmentOut>(
      `/admin/brokers/${brokerId}/assign-insurer/${insuranceCompanyId}`,
      { method: "DELETE", token }
    );
    revalidatePath("/dashboard/admin/brokers");
    revalidatePath(`/dashboard/admin/brokers/${brokerId}`);
    return { status: "success", data: assignment };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}
