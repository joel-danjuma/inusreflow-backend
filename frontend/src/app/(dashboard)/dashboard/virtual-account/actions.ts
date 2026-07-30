"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];

export async function updateOwnBrokerKyb(
  _prevState: ActionState<VirtualAccountOut>,
  formData: FormData
): Promise<ActionState<VirtualAccountOut>> {
  const token = await getAuthToken();
  const bvn = String(formData.get("bvn") ?? "").trim();
  const phoneNumber = String(formData.get("phone_number") ?? "").trim();
  try {
    const account = await apiFetch<VirtualAccountOut>("/virtual-accounts/me", {
      method: "PATCH",
      token,
      body: { bvn, phone_number: phoneNumber },
    });
    revalidatePath("/dashboard/virtual-account");
    return { status: "success", data: account };
  } catch (error) {
    if (error instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const fe of error.fieldErrors) fieldErrors[fe.field] = fe.message;
      return { status: "error", message: error.message, fieldErrors };
    }
    throw error;
  }
}
