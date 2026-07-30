import { ActivateForm } from "@/components/forms/ActivateForm";

export default async function ActivatePage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-secondary-soft px-6 py-12">
      <div className="w-full max-w-sm rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md">
        <h1 className="mb-1 text-xl font-semibold text-heading">Activate your account</h1>
        <p className="mb-6 text-sm text-body">
          Paste the one-time activation token you were given and choose a password.
        </p>
        <ActivateForm token={token ?? ""} />
      </div>
    </main>
  );
}
