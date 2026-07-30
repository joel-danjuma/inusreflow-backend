import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { apiFormPost } from "@/lib/api/client";
import { parseApiError } from "@/lib/api/errors";
import { parseSessionToken, SESSION_COOKIE_NAME } from "@/lib/auth/jwt";

interface LoginRequestBody {
  email: string;
  password: string;
}

export async function POST(request: Request) {
  const { email, password } = (await request.json()) as LoginRequestBody;

  const backendResponse = await apiFormPost("/auth/login", {
    username: email,
    password,
  });

  if (!backendResponse.ok) {
    const error = await parseApiError(backendResponse);
    return NextResponse.json({ detail: error.message }, { status: error.status });
  }

  const {
    access_token: accessToken,
    must_change_password: mustChangePassword,
    org_approved: orgApproved,
  } = (await backendResponse.json()) as {
    access_token: string;
    must_change_password: boolean;
    org_approved: boolean;
  };
  const session = parseSessionToken(accessToken);
  if (!session) {
    return NextResponse.json({ detail: "Received an invalid session token." }, { status: 502 });
  }

  const store = await cookies();
  store.set(SESSION_COOKIE_NAME, accessToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: Math.max(session.exp - Math.floor(Date.now() / 1000), 0),
  });

  return NextResponse.json({
    role: session.role,
    orgId: session.orgId,
    mustChangePassword,
    orgApproved,
  });
}
