"use server";

import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type OtpResult = components["schemas"]["OtpResult"];

export async function createBrokerStaff(
  brokerId: string,
  _prevState: ActionState<OtpResult>,
  formData: FormData
): Promise<ActionState<OtpResult>> {
  const token = await getAuthToken();
  const email = String(formData.get("email") ?? "").trim();
  try {
    const result = await apiFetch<OtpResult>(`/brokers/${brokerId}/staff`, {
      method: "POST",
      token,
      body: { email },
    });
    return { status: "success", data: result };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}
