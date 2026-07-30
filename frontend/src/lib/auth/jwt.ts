import type { Role } from "./rbac";

export const SESSION_COOKIE_NAME = "if_session";

export interface SessionPayload {
  userId: string;
  role: Role;
  orgId: string | null;
  mustChangePassword: boolean;
  orgApproved: boolean;
  exp: number;
}

/**
 * Decodes (never verifies) the JWT payload. No security boundary is placed
 * on this decode: the token was received directly from the trusted backend
 * over a server-to-server call at login, and every subsequent real API call
 * is still verified by FastAPI itself. This is purely for UI routing/display
 * convenience (proxy.ts redirects, nav gating, session display).
 */
export function parseSessionToken(token: string | undefined | null): SessionPayload | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length !== 3) return null;

  try {
    let base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    while (base64.length % 4 !== 0) base64 += "=";
    const json = atob(base64);
    const payload = JSON.parse(json) as {
      sub?: string;
      role?: string;
      org_id?: string | null;
      must_change_password?: boolean;
      org_approved?: boolean;
      exp?: number;
    };
    const exp = typeof payload.exp === "number" ? payload.exp : 0;
    if (!payload.sub || !payload.role || exp * 1000 < Date.now()) return null;

    return {
      userId: payload.sub,
      role: payload.role as Role,
      orgId: payload.org_id ?? null,
      mustChangePassword: payload.must_change_password ?? false,
      orgApproved: payload.org_approved ?? true,
      exp,
    };
  } catch {
    return null;
  }
}
