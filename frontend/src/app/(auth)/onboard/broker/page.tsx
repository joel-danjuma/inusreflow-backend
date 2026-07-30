import Link from "next/link";
import { OnboardBrokerForm } from "@/components/forms/OnboardBrokerForm";

export default function OnboardBrokerPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-secondary-soft px-6 py-12">
      <div className="w-full max-w-sm rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md">
        <h1 className="mb-1 text-xl font-semibold text-heading">Onboard as a broker</h1>
        <p className="mb-6 text-sm text-body">
          An Insureflow Admin will review, approve, and assign you to an insurer.
        </p>
        <OnboardBrokerForm />
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
