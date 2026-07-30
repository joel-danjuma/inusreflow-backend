import Link from "next/link";
import { OnboardInsurerForm } from "@/components/forms/OnboardInsurerForm";

export default function OnboardInsurerPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-secondary-soft px-6 py-12">
      <div className="w-full max-w-sm rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md">
        <h1 className="mb-1 text-xl font-semibold text-heading">Onboard an insurer</h1>
        <p className="mb-6 text-sm text-body">
          An Insureflow Admin will review and approve your application.
        </p>
        <OnboardInsurerForm />
        <p className="mt-6 text-center text-sm text-body">
          Already approved?{" "}
          <Link href="/login" className="font-medium text-fg-brand hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
