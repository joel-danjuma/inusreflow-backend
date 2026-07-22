import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";

export function Open() {
  return (
    <div style={{ position: "relative", height: "320px", overflow: "hidden" }}>
      <Modal open onClose={() => {}} title="Confirm policy cancellation">
        <p className="text-sm text-body mb-6">
          Are you sure you want to cancel policy <strong>POL-2024-001</strong>? This action cannot be undone and
          will mark all future installments as cancelled.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" size="sm">Keep policy</Button>
          <Button variant="danger" size="sm">Cancel policy</Button>
        </div>
      </Modal>
    </div>
  );
}

export function WithForm() {
  return (
    <div style={{ position: "relative", height: "360px", overflow: "hidden" }}>
      <Modal open onClose={() => {}} title="Approve broker application">
        <p className="text-sm text-body mb-4">
          Review and approve <strong>Apex Insurance Brokers Ltd</strong> to begin onboarding.
        </p>
        <p className="text-xs text-body mb-6">
          Once approved, the broker will receive a login link and can start creating policies.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" size="sm">Reject</Button>
          <Button variant="success" size="sm">Approve</Button>
        </div>
      </Modal>
    </div>
  );
}
