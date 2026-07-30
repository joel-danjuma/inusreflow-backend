"use server";

import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BrokerOnboardResult = components["schemas"]["BrokerOnboardResult"];

export async function onboardBroker(
  _prevState: ActionState<BrokerOnboardResult>,
  formData: FormData
): Promise<ActionState<BrokerOnboardResult>> {
  const name = String(formData.get("name") ?? "").trim();
  const contactEmail = String(formData.get("contact_email") ?? "").trim();

  try {
    const result = await apiFetch<BrokerOnboardResult>("/brokers", {
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
