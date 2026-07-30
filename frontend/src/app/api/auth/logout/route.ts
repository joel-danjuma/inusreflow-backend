import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { SESSION_COOKIE_NAME } from "@/lib/auth/jwt";

/** JWTs are stateless/unrevoked in this backend (no token blocklist) --
 * logout is purely a client-side cookie clear, no backend call needed. */
export async function POST() {
  const store = await cookies();
  store.delete(SESSION_COOKIE_NAME);
  return NextResponse.json({ ok: true });
}
