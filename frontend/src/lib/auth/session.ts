import "server-only";
import { cookies } from "next/headers";
import { parseSessionToken, SESSION_COOKIE_NAME, type SessionPayload } from "./jwt";

export type Session = SessionPayload;

export async function getSession(): Promise<Session | null> {
  const store = await cookies();
  return parseSessionToken(store.get(SESSION_COOKIE_NAME)?.value);
}

/** Raw JWT, for forwarding as `Authorization: Bearer <token>` to FastAPI. */
export async function getAuthToken(): Promise<string | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE_NAME)?.value;
  // Reuse the same expiry check as getSession() so a stale-but-present
  // cookie is never forwarded as if it were still valid.
  return parseSessionToken(token) ? (token ?? null) : null;
}

export { SESSION_COOKIE_NAME };
