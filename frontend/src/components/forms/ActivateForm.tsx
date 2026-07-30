"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function ActivateForm({ token }: { token: string }) {
  const router = useRouter();
  const [tokenValue, setTokenValue] = useState(token);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setSubmitting(true);
    try {
      const response = await fetch("/api/auth/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: tokenValue, password }),
      });
      const data = (await response.json()) as { detail?: string };

      if (!response.ok) {
        setError(data.detail ?? "Activation failed.");
        return;
      }

      router.push("/login?reason=activated");
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
        id="token"
        label="Activation token"
        required
        value={tokenValue}
        onChange={(e) => setTokenValue(e.target.value)}
      />
      <Input
        id="password"
        label="New password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <Input
        id="confirm-password"
        label="Confirm password"
        type="password"
        autoComplete="new-password"
        required
        minLength={8}
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />

      <Button type="submit" disabled={submitting} className="w-full">
        {submitting ? "Activating…" : "Activate account"}
      </Button>
    </form>
  );
}
