"use server";

import { revalidatePath } from "next/cache";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BulkReminderResult = components["schemas"]["BulkReminderResult"];

export async function sendPaymentReminders(
  _prevState: ActionState<BulkReminderResult>,
  _formData: FormData
): Promise<ActionState<BulkReminderResult>> {
  const token = await getAuthToken();

  try {
    const result = await apiFetch<BulkReminderResult>("/reminders/bulk", {
      method: "POST",
      token,
    });
    revalidatePath("/dashboard");
    return { status: "success", data: result };
  } catch (error) {
    if (error instanceof ApiError) {
      return { status: "error", message: error.message };
    }
    throw error;
  }
}
