"use client";

import { useState, useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import { createPolicy } from "@/app/(dashboard)/dashboard/policies/actions";
import { CURATED_POLICY_TYPES, POLICY_TYPE_LABELS } from "@/lib/policyTypes";
import type { components } from "@/lib/api/types";

type PolicyOut = components["schemas"]["PolicyOut"];

function SectionHeading({ title, description }: { title: string; description?: string }) {
  return (
    <div>
      <h2 className="text-base font-medium text-heading">{title}</h2>
      {description && <p className="mt-1 text-sm text-body">{description}</p>}
    </div>
  );
}

export function CreatePolicyForm({
  brokers,
  policyholders,
  fixedPolicyholderId,
}: {
  brokers: { id: string; name: string }[];
  policyholders: { id: string; full_name: string }[];
  fixedPolicyholderId?: string;
}) {
  const [state, formAction, pending] = useActionState(
    createPolicy,
    IDLE_STATE as ActionState<PolicyOut>
  );
  const [policyType, setPolicyType] = useState<string>(CURATED_POLICY_TYPES[0]);

  return (
    <form action={formAction} className="space-y-8">
      {state.status === "error" && <p className="text-sm text-fg-danger">{state.message}</p>}

      {/* Policy Information */}
      <div className="space-y-5">
        <SectionHeading title="Policy information" />

        <div>
          <label htmlFor="broker_id" className="mb-2 block text-sm font-medium text-heading">
            Broker
          </label>
          <select
            id="broker_id"
            name="broker_id"
            required
            className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            <option value="">Select a broker…</option>
            {brokers.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>

        <Input
          id="reference_number"
          name="reference_number"
          label="Debit note / reference number"
          placeholder="The unique identifier for this policy"
          required
          error={state.fieldErrors?.reference_number}
        />

        {fixedPolicyholderId ? (
          <input type="hidden" name="policyholder_id" value={fixedPolicyholderId} />
        ) : (
          <div>
            <label
              htmlFor="policyholder_id"
              className="mb-2 block text-sm font-medium text-heading"
            >
              Policyholder
            </label>
            <select
              id="policyholder_id"
              name="policyholder_id"
              required
              className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
            >
              <option value="">Select a policyholder…</option>
              {policyholders.map((ph) => (
                <option key={ph.id} value={ph.id}>
                  {ph.full_name}
                </option>
              ))}
            </select>
          </div>
        )}

        <Input
          id="policy_name"
          name="policy_name"
          label="Policy name"
          placeholder="e.g. Adaeze Okafor — Comprehensive Auto"
          error={state.fieldErrors?.policy_name}
        />

        <div>
          <label
            htmlFor="policy_type_select"
            className="mb-2 block text-sm font-medium text-heading"
          >
            Policy type
          </label>
          <select
            id="policy_type_select"
            value={policyType}
            onChange={(e) => setPolicyType(e.target.value)}
            className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            {CURATED_POLICY_TYPES.map((t) => (
              <option key={t} value={t}>
                {POLICY_TYPE_LABELS[t]}
              </option>
            ))}
            <option value="OTHER">Other…</option>
          </select>
        </div>
        {policyType === "OTHER" && (
          <Input
            id="policy_type_other"
            name="policy_type_other"
            label="Specify policy type"
            required
            error={state.fieldErrors?.policy_type}
          />
        )}
        <input type="hidden" name="policy_type" value={policyType === "OTHER" ? "" : policyType} />

        <Input
          id="duration_months"
          name="duration_months"
          label="Duration (months)"
          type="number"
          min="1"
          step="1"
          defaultValue={12}
          error={state.fieldErrors?.duration_months}
        />

        <Input
          id="start_date"
          name="start_date"
          label="Start date"
          type="date"
          required
          error={state.fieldErrors?.start_date}
        />
      </div>

      {/* Payment & Premium Details */}
      <div className="space-y-5 border-t border-border-default pt-8">
        <SectionHeading
          title="Payment & premium details"
          description="A rolling window of premium installments is generated automatically once created."
        />

        <Input
          id="premium_amount_naira"
          name="premium_amount_naira"
          label="Premium amount (₦)"
          type="number"
          step="0.01"
          min="0.01"
          required
          error={state.fieldErrors?.premium_amount_kobo}
        />
        <div>
          <label htmlFor="premium_frequency" className="mb-2 block text-sm font-medium text-heading">
            Payment frequency
          </label>
          <select
            id="premium_frequency"
            name="premium_frequency"
            required
            defaultValue="monthly"
            className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="annually">Annually</option>
          </select>
        </div>
      </div>

      {/* Coverage Details */}
      <div className="space-y-5 border-t border-border-default pt-8">
        <SectionHeading title="Coverage details" />

        <Input
          id="coverage_amount_naira"
          name="coverage_amount_naira"
          label="Coverage amount (₦)"
          type="number"
          step="0.01"
          min="0.01"
          error={state.fieldErrors?.coverage_amount_kobo}
        />
        <Textarea
          id="coverage_items"
          name="coverage_items"
          label="Coverage items / risk type"
          placeholder="What's covered under this policy"
          error={state.fieldErrors?.coverage_items}
        />
        <Textarea
          id="beneficiaries"
          name="beneficiaries"
          label="Beneficiaries"
          placeholder="Who benefits from a claim on this policy"
          error={state.fieldErrors?.beneficiaries}
        />
      </div>

      {/* Tags / Broker Visibility */}
      <div className="space-y-5 border-t border-border-default pt-8">
        <SectionHeading title="Tags & broker visibility" />

        <Textarea
          id="broker_notes"
          name="broker_notes"
          label="Broker notes"
          placeholder="Internal notes visible to your team"
          error={state.fieldErrors?.broker_notes}
        />
        <Input
          id="internal_tags"
          name="internal_tags"
          label="Internal tags"
          placeholder="Comma-separated, e.g. high-value, renewal-2026"
          error={state.fieldErrors?.internal_tags}
        />
      </div>

      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Creating…" : "Create policy"}
      </Button>
    </form>
  );
}
