"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

function EyeIcon({ off }: { off: boolean }) {
  return off ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M9.88 9.88a3 3 0 1 0 4.24 4.24M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68M6.61 6.61C3.35 8.36 1 12 1 12s3 7 11 7a10.44 10.44 0 0 0 5.39-1.61M1 1l22 22"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.75" />
    </svg>
  );
}

export function LoginForm({ next }: { next: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = (await response.json()) as {
        detail?: string;
        mustChangePassword?: boolean;
        orgApproved?: boolean;
      };

      if (!response.ok) {
        setError(data.detail ?? "Login failed.");
        return;
      }

      // Hard navigation, not router.push -- a client-side transition leaves
      // the previous account's rendered layouts (e.g. the role-based
      // Sidebar) sitting in Next.js's back/forward cache, which browser
      // Back/Forward can restore instead of fetching fresh (confirmed via
      // next/dist/docs: staleTimes explicitly doesn't govern that cache).
      // A full page load discards that cache entirely.
      if (data.mustChangePassword) {
        window.location.href = "/change-password";
      } else if (!data.orgApproved) {
        window.location.href = "/pending-approval";
      } else {
        window.location.href = next;
      }
    } catch {
      setError("Couldn't reach the server. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-5 rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md"
    >
      <div>
        <span className="font-display text-2xl font-semibold tracking-tight text-heading">
          Insure<span className="text-fg-brand">flow</span>
        </span>
        <p className="mt-2 text-base font-medium text-heading">Sign in to your account</p>
        <p className="text-sm text-body">Premium collection &amp; settlement</p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-base border border-border-danger-subtle bg-danger-soft px-4 py-3 text-sm text-fg-danger-strong"
        >
          {error}
        </div>
      )}

      <Input
        id="email"
        label="Email address"
        type="email"
        autoComplete="username"
        placeholder="you@company.ng"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <Input
        id="password"
        label="Password"
        type={showPassword ? "text" : "password"}
        autoComplete="current-password"
        placeholder="Enter your password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        suffix={
          <button
            type="button"
            onClick={() => setShowPassword((s) => !s)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            className="inline-flex text-body-subtle hover:text-body"
          >
            <EyeIcon off={showPassword} />
          </button>
        }
      />

      <Button type="submit" disabled={submitting} className="w-full">
        {submitting ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
