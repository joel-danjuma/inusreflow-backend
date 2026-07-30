import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { components } from "@/lib/api/types";

type PaymentBatchOut = components["schemas"]["PaymentBatchOut"];

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ batchId: string }> }
) {
  const { batchId } = await params;
  const token = await getAuthToken();

  try {
    const batch = await apiFetch<PaymentBatchOut>(`/payments/bulk/${batchId}`, { token });
    return NextResponse.json(batch);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    throw error;
  }
}
