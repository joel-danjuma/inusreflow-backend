"use server";

import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type PolicyholderOut = components["schemas"]["PolicyholderOut"];

export async function createPolicyholder(
  _prevState: ActionState<PolicyholderOut>,
  formData: FormData
): Promise<ActionState<PolicyholderOut>> {
  const token = await getAuthToken();
  const brokerId = String(formData.get("broker_id") ?? "");
  const fullName = String(formData.get("full_name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const phoneNumber = String(formData.get("phone_number") ?? "").trim();
  const identificationNumber = String(formData.get("identification_number") ?? "").trim();

  let policyholder: PolicyholderOut;
  try {
    policyholder = await apiFetch<PolicyholderOut>("/users", {
      method: "POST",
      token,
      body: {
        broker_id: brokerId,
        full_name: fullName,
        email: email || undefined,
        phone_number: phoneNumber || undefined,
        identification_number: identificationNumber || undefined,
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

  redirect(`/dashboard/policyholders/${policyholder.id}`);
}
