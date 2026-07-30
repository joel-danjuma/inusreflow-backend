export default function SupportPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">Support</h1>
        <p className="mt-1 text-sm text-body">Need a hand? Here&apos;s how to reach us.</p>
      </div>

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <dl className="space-y-4 text-sm">
          <div>
            <dt className="text-body-subtle">Email</dt>
            <dd className="mt-1 text-heading">support@insureflow.local</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Response time</dt>
            <dd className="mt-1 text-heading">Within one business day</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
