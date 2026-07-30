"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { CopyableToken } from "@/components/ui/CopyableToken";
import { IDLE_STATE } from "@/lib/api/action-state";
import { onboardInsurer } from "@/app/(auth)/onboard/insurer/actions";

export function OnboardInsurerForm() {
  const [state, formAction, pending] = useActionState(onboardInsurer, IDLE_STATE);

  if (state.status === "success" && state.data) {
    return (
      <div className="space-y-3 rounded-base border border-border-success-subtle bg-success-soft px-4 py-3 text-sm text-fg-success-strong">
        <div>
          <p className="font-medium">Application submitted.</p>
          <p className="mt-1">
            {state.data.company.name} is now <strong>pending</strong> Insureflow Admin approval.
          </p>
        </div>
        <div>
          <p className="font-medium">Your one-time password (shown once):</p>
          <p className="mt-1 mb-2">
            Use this to sign in now &mdash; you&apos;ll be asked to set a real password
            immediately after. Full dashboard access still waits on approval.
          </p>
          <CopyableToken token={state.data.otp} />
        </div>
      </div>
    );
  }

  return (
    <form action={formAction} className="space-y-5">
      {state.status === "error" && !Object.keys(state.fieldErrors ?? {}).length && (
        <div
          role="alert"
          className="rounded-base border border-border-danger-subtle bg-danger-soft px-4 py-3 text-sm text-fg-danger-strong"
        >
          {state.message}
        </div>
      )}

      <Input id="name" name="name" label="Company name" required error={state.fieldErrors?.name} />
      <Input
        id="contact_email"
        name="contact_email"
        label="Contact email"
        type="email"
        required
        error={state.fieldErrors?.contact_email}
      />

      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Submitting…" : "Submit application"}
      </Button>
    </form>
  );
}
