import { ChangePasswordForm } from "@/components/forms/ChangePasswordForm";

export default function ChangePasswordPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-secondary-soft px-6 py-12">
      <div className="w-full max-w-sm rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md">
        <h1 className="mb-1 text-xl font-semibold text-heading">Set your password</h1>
        <p className="mb-6 text-sm text-body">
          For security, you need to set a real password before continuing. Enter the one-time
          password you were given as your current password.
        </p>
        <ChangePasswordForm />
      </div>
    </main>
  );
}
