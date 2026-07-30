"use server";

import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOnboardResult = components["schemas"]["InsuranceCompanyOnboardResult"];

export async function onboardInsurer(
  _prevState: ActionState<InsuranceCompanyOnboardResult>,
  formData: FormData
): Promise<ActionState<InsuranceCompanyOnboardResult>> {
  const name = String(formData.get("name") ?? "").trim();
  const contactEmail = String(formData.get("contact_email") ?? "").trim();

  try {
    const result = await apiFetch<InsuranceCompanyOnboardResult>("/insurance-companies", {
      method: "POST",
      body: { name, contact_email: contactEmail },
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
