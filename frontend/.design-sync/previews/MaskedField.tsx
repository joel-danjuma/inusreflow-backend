import { MaskedField } from "@/components/pii/MaskedField";

export function Default() {
  return (
    <div className="flex flex-col gap-3 p-4 max-w-sm rounded-base bg-neutral-primary-soft">
      <div className="flex flex-col gap-1">
        <span className="text-xs text-body-subtle">NIN</span>
        <MaskedField label="NIN" value="12345678901" />
      </div>
      <div className="flex flex-col gap-1">
        <span className="text-xs text-body-subtle">BVN</span>
        <MaskedField label="BVN" value="22198765432" />
      </div>
    </div>
  );
}

export function AccountNumber() {
  return (
    <div className="p-4 max-w-sm rounded-base bg-neutral-primary-soft">
      <div className="flex flex-col gap-1">
        <span className="text-xs text-body-subtle">Bank account number</span>
        <MaskedField label="Bank account number" value="0123456789" />
      </div>
    </div>
  );
}
