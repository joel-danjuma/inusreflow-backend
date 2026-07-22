import { CopyableToken } from "@/components/ui/CopyableToken";

export function Default() {
  return (
    <div className="p-4 space-y-3 max-w-sm">
      <CopyableToken token="sk_live_abc123xyz456789" />
    </div>
  );
}

export function LongToken() {
  return (
    <div className="p-4 max-w-md">
      <CopyableToken token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c" />
    </div>
  );
}
