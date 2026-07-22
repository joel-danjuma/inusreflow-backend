import { Alert } from "@/components/ui/Alert";

export function WithTitle() {
  return (
    <div className="flex flex-col gap-3 p-4 max-w-md">
      <Alert variant="brand" title="Policy updated">
        Your policy details have been saved and will take effect next billing cycle.
      </Alert>
      <Alert variant="success" title="Payment confirmed">
        ₦45,000 collected for policy POL-2024-001. Settlement initiated.
      </Alert>
      <Alert variant="danger" title="Payment failed">
        We couldn't process your payment. Please check your account balance and try again.
      </Alert>
      <Alert variant="warning" title="Action required">
        3 installments are overdue. Please settle outstanding premiums to keep your policy active.
      </Alert>
    </div>
  );
}

export function WithoutTitle() {
  return (
    <div className="flex flex-col gap-3 p-4 max-w-md">
      <Alert variant="brand">Your account is pending admin approval.</Alert>
      <Alert variant="success">Broker onboarded successfully.</Alert>
      <Alert variant="danger">Invalid credentials. Please try again.</Alert>
      <Alert variant="warning">Your session will expire in 5 minutes.</Alert>
    </div>
  );
}
