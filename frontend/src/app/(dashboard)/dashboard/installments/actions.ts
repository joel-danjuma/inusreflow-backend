"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InstallmentOut = components["schemas"]["InstallmentOut"];

export async function setInstallmentReferenceNumber(
  installmentId: string,
  _prevState: ActionState<InstallmentOut>,
  formData: FormData
): Promise<ActionState<InstallmentOut>> {
  const token = await getAuthToken();
  const raw = String(formData.get("reference_number") ?? "").trim();

  try {
    const installment = await apiFetch<InstallmentOut>(
      `/installments/${installmentId}/reference-number`,
      {
        method: "PATCH",
        token,
        body: { reference_number: raw || null },
      }
    );
    revalidatePath("/dashboard/installments");
    revalidatePath("/dashboard");
    return { status: "success", data: installment };
  } catch (error) {
    if (error instanceof ApiError) {
      return { status: "error", message: error.message };
    }
    throw error;
  }
}
