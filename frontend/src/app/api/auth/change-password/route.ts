import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";
import { parseSessionToken, SESSION_COOKIE_NAME } from "@/lib/auth/jwt";

interface ChangePasswordRequestBody {
  current_password: string;
  new_password: string;
}

export async function PATCH(request: Request) {
  const { current_password: currentPassword, new_password: newPassword } =
    (await request.json()) as ChangePasswordRequestBody;
  const token = await getAuthToken();

  try {
    const result = await apiFetch<{
      access_token: string;
      must_change_password: boolean;
      org_approved: boolean;
    }>("/auth/change-password", {
      method: "PATCH",
      token,
      body: { current_password: currentPassword, new_password: newPassword },
    });

    const session = parseSessionToken(result.access_token);
    if (!session) {
      return NextResponse.json({ detail: "Received an invalid session token." }, { status: 502 });
    }

    const store = await cookies();
    store.set(SESSION_COOKIE_NAME, result.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: Math.max(session.exp - Math.floor(Date.now() / 1000), 0),
    });

    return NextResponse.json({
      mustChangePassword: result.must_change_password,
      orgApproved: result.org_approved,
    });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    throw error;
  }
}
