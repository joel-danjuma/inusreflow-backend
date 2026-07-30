import { redirect } from "next/navigation";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { getOrgName } from "@/lib/org";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

/**
 * proxy.ts already redirects unauthenticated/mid-onboarding requests away
 * from /dashboard/*, but that's UX-layer routing only -- this server-side
 * check is the real defense-in-depth backstop for this route group.
 */
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();
  if (!session) {
    redirect("/login?reason=session_expired");
  }
  if (session.mustChangePassword) {
    redirect("/change-password");
  }
  if (!session.orgApproved) {
    redirect("/pending-approval");
  }

  const orgName = await getOrgName(session, await getAuthToken());

  return (
    <div className="flex h-screen overflow-hidden bg-neutral-secondary-soft">
      <Sidebar role={session.role} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar role={session.role} orgName={orgName} />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
