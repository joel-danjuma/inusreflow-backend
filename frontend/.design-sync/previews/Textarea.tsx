import { Textarea } from "@/components/ui/Textarea";

export function Default() {
  return (
    <div className="p-4 max-w-sm space-y-4">
      <Textarea id="notes" label="Policy notes" placeholder="Enter any additional notes about this policy…" rows={4} />
      <Textarea id="rejection-reason" label="Rejection reason" placeholder="Explain why this application is being rejected…" rows={3} />
    </div>
  );
}

export function WithError() {
  return (
    <div className="p-4 max-w-sm">
      <Textarea
        id="notes-error"
        label="Policy notes"
        defaultValue="x"
        error="Notes must be at least 20 characters."
        rows={4}
      />
    </div>
  );
}

export function Disabled() {
  return (
    <div className="p-4 max-w-sm">
      <Textarea
        id="notes-disabled"
        label="Submission notes"
        defaultValue="Policy accepted as-is. No modifications required."
        disabled
        rows={3}
      />
    </div>
  );
}
