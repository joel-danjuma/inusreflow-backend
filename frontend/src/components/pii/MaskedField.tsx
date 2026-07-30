"use client";

import { useState } from "react";
import { maskTail } from "@/lib/mask";

export function MaskedField({ value, label }: { value: string; label: string }) {
  const [revealed, setRevealed] = useState(false);

  return (
    <span className="inline-flex items-center gap-2">
      <span className="font-mono text-sm text-heading">{revealed ? value : maskTail(value)}</span>
      <button
        type="button"
        onClick={() => setRevealed((r) => !r)}
        className="text-xs font-medium text-fg-brand hover:underline"
        aria-label={revealed ? `Hide ${label}` : `Show ${label}`}
      >
        {revealed ? "Hide" : "Show"}
      </button>
    </span>
  );
}
