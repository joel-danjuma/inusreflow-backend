"use server";

import { redirect } from "next/navigation";
import { apiFetch, apiFetchMultipart } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type PaymentOut = components["schemas"]["PaymentOut"];
type PaymentBatchOut = components["schemas"]["PaymentBatchOut"];
type BulkPaymentFileResolution = components["schemas"]["BulkPaymentFileResolution"];

export async function createSinglePayment(
  installmentId: string,
  _prevState: ActionState<undefined>,
  formData: FormData
): Promise<ActionState<undefined>> {
  const token = await getAuthToken();
  const idempotencyKey = String(formData.get("idempotency_key") ?? "");

  let payment: PaymentOut;
  try {
    payment = await apiFetch<PaymentOut>("/payments", {
      method: "POST",
      token,
      headers: { "Idempotency-Key": idempotencyKey },
      body: { installment_id: installmentId },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      return { status: "error", message: error.message };
    }
    throw error;
  }

  redirect(`/dashboard/payments/${payment.id}`);
}

export async function createBulkPayment(
  _prevState: ActionState<undefined>,
  formData: FormData
): Promise<ActionState<undefined>> {
  const token = await getAuthToken();
  const idempotencyKey = String(formData.get("idempotency_key") ?? "");
  const installmentIds = formData.getAll("installment_ids").map(String);

  if (installmentIds.length === 0) {
    return { status: "error", message: "Select at least one installment to pay." };
  }

  let batch: PaymentBatchOut;
  try {
    batch = await apiFetch<PaymentBatchOut>("/payments/bulk", {
      method: "POST",
      token,
      headers: { "Idempotency-Key": idempotencyKey },
      body: { installment_ids: installmentIds },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      return { status: "error", message: error.message };
    }
    throw error;
  }

  redirect(`/dashboard/payments/bulk/${batch.id}`);
}

export async function resolveBulkPaymentFile(
  _prevState: ActionState<BulkPaymentFileResolution>,
  formData: FormData
): Promise<ActionState<BulkPaymentFileResolution>> {
  const token = await getAuthToken();
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { status: "error", message: "Choose an Excel file to upload." };
  }

  const upload = new FormData();
  upload.set("file", file);

  try {
    const resolution = await apiFetchMultipart<BulkPaymentFileResolution>(
      "/payments/bulk/resolve-file",
      { formData: upload, token }
    );
    return { status: "success", data: resolution };
  } catch (error) {
    if (error instanceof ApiError) {
      return { status: "error", message: error.message };
    }
    throw error;
  }
}
