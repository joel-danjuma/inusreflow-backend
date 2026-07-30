"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function ChangePasswordForm() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch("/api/auth/change-password", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const data = (await response.json()) as {
        detail?: string;
        mustChangePassword?: boolean;
        orgApproved?: boolean;
      };

      if (!response.ok) {
        setError(data.detail ?? "Couldn't change your password.");
        return;
      }

      // Hard navigation, same reasoning as LoginForm -- discards any stale
      // role-based layout a client-side transition could leave cached.
      window.location.href = data.orgApproved ? "/dashboard" : "/pending-approval";
    } catch {
      setError("Couldn't reach the server. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div
          role="alert"
          className="rounded-base border border-border-danger-subtle bg-danger-soft px-4 py-3 text-sm text-fg-danger-strong"
        >
          {error}
        </div>
      )}

      <Input
        id="current-password"
        label="Current password (or one-time password)"
        type="password"
        autoComplete="current-password"
        required
        value={currentPassword}
        onChange={(e) => setCurrentPassword(e.target.value)}
      />
      <Input
        id="new-password"
        label="New password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
      />
      <Input
        id="confirm-password"
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />

      <Button type="submit" disabled={submitting} className="w-full">
        {submitting ? "Saving…" : "Set new password"}
      </Button>
    </form>
  );
}
