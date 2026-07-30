import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import type { components } from "@/lib/api/types";

type PaymentOut = components["schemas"]["PaymentOut"];

/** Same-origin, cookie-authenticated poll target for PaymentStatusPoller --
 * a client component can't call FastAPI directly (no CORS, and the JWT
 * never leaves the server), so it polls this instead. */
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const token = await getAuthToken();

  try {
    const payment = await apiFetch<PaymentOut>(`/payments/${id}`, { token });
    return NextResponse.json(payment);
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    throw error;
  }
}
