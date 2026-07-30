"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];

export async function recreateVirtualAccount(
  brokerId: string,
  _prevState: ActionState<VirtualAccountOut>,
  _formData: FormData
): Promise<ActionState<VirtualAccountOut>> {
  const token = await getAuthToken();
  try {
    const account = await apiFetch<VirtualAccountOut>(`/virtual-accounts/${brokerId}`, {
      method: "POST",
      token,
    });
    revalidatePath("/dashboard/admin/virtual-accounts");
    return { status: "success", data: account };
  } catch (error) {
    if (error instanceof ApiError) return { status: "error", message: error.message };
    throw error;
  }
}
