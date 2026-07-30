"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type SettlementPayoutOut = components["schemas"]["SettlementPayoutOut"];

export async function retrySettlement(
  payoutId: string,
  _prevState: ActionState<SettlementPayoutOut>,
  _formData: FormData
): Promise<ActionState<SettlementPayoutOut>> {
  const token = await getAuthToken();
  try {
    const payout = await apiFetch<SettlementPayoutOut>(`/settlements/${payoutId}/retry`, {
      method: "POST",
      token,
    });
    revalidatePath("/dashboard/settlements");
    revalidatePath(`/dashboard/settlements/${payoutId}`);
    return { status: "success", data: payout };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}
