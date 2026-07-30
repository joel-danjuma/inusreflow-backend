"use client";

import { useState } from "react";

/**
 * Generates one Idempotency-Key per scope (e.g. an installment id for a
 * single payment, or a joined/sorted installment-id list for a bulk
 * batch), persisted in sessionStorage so a network-failure retry reuses
 * the same key instead of minting a new one and risking a duplicate
 * charge on the backend's idempotency ledger.
 */
export function useIdempotencyKey(scopeKey: string): {
  key: string;
  clear: () => void;
} {
  const storageKey = `idem:${scopeKey}`;
  const [key] = useState(() => {
    if (typeof window === "undefined") return crypto.randomUUID();
    const existing = window.sessionStorage.getItem(storageKey);
    if (existing) return existing;
    const generated = crypto.randomUUID();
    window.sessionStorage.setItem(storageKey, generated);
    return generated;
  });

  const clear = () => {
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(storageKey);
    }
  };

  return { key, clear };
}
