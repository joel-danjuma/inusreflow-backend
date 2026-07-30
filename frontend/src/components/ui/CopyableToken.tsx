"use client";

import { useState } from "react";

/** There's no email infra in this backend -- activation tokens are returned
 * once in the API response and never re-shown, so the admin/broker-admin
 * performing the approval/staff-creation action must copy it manually. */
export function CopyableToken({ token }: { token: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(token);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="flex items-center gap-2 rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5">
      <code className="min-w-0 flex-1 truncate font-mono text-sm text-heading">{token}</code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-default border border-border-default px-2 py-1 text-xs font-medium text-heading transition-colors hover:bg-neutral-tertiary-medium"
      >
        {copied ? "Copied!" : "Copy"}
      </button>
    </div>
  );
}
