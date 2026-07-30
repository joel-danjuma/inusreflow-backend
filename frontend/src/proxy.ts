import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { parseSessionToken, SESSION_COOKIE_NAME } from "@/lib/auth/jwt";
import { PROTECTED_PATH_PERMISSIONS } from "@/lib/nav-config";
import { roleHasPermission } from "@/lib/auth/rbac";

/**
 * Next.js 16 renamed the `middleware.ts` file convention to `proxy.ts`
 * (the exported function is `proxy`, not `middleware`) -- see
 * node_modules/next/dist/docs/01-app/03-api-reference/03-file-conventions/proxy.md.
 *
 * This is UX-layer routing only. The real enforcement is the FastAPI call
 * itself: every server-side page load still sends the token and must
 * handle a 403, since a stale cookie claiming a role after a demotion (or
 * simply a role this table doesn't cover, like an ownership-scoped detail
 * route) can still reach a page here.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = parseSessionToken(token);

  if (!session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("reason", "session_expired");
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Both targets are outside this proxy's /dashboard/:path* matcher, so
  // redirecting to them never loops back through this check again. The real
  // gate is backend-side (app/core/deps.py's require_full_access) -- these
  // are UX-routing hints only, snapshotted at login/change-password time.
  if (session.mustChangePassword) {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }
  if (!session.orgApproved) {
    return NextResponse.redirect(new URL("/pending-approval", request.url));
  }

  const gate = PROTECTED_PATH_PERMISSIONS.find((entry) => pathname.startsWith(entry.prefix));
  if (gate && !roleHasPermission(session.role, gate.permission)) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
