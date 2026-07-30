import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";

interface ActivateRequestBody {
  token: string;
  password: string;
}

export async function POST(request: Request) {
  const { token, password } = (await request.json()) as ActivateRequestBody;

  try {
    await apiFetch<void>("/auth/activate", { method: "POST", body: { token, password } });
    return NextResponse.json({ ok: true });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json(
        { detail: error.message, fieldErrors: error.fieldErrors },
        { status: error.status }
      );
    }
    throw error;
  }
}
