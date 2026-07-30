"use client";

import { useState } from "react";
import { Button } from "@/components/ui/Button";

export function LogoutButton() {
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    await fetch("/api/auth/logout", { method: "POST" });
    // Hard navigation, not router.push -- see LoginForm.tsx for why: it's
    // the only way to discard Next.js's back/forward cache so a later
    // Back-button press can't restore this account's stale rendered layout
    // after a different account logs in.
    window.location.href = "/login";
  }

  return (
    <Button variant="ghost" size="sm" onClick={handleLogout} disabled={loggingOut}>
      {loggingOut ? "Signing out…" : "Sign out"}
    </Button>
  );
}
