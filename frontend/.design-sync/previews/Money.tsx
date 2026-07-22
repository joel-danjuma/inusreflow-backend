import { Money } from "@/components/money/Money";

export function Default() {
  return (
    <div className="flex flex-col gap-2 p-4">
      <div className="text-2xl font-semibold"><Money kobo={450000} /></div>
      <div className="text-xl"><Money kobo={12000000} /></div>
      <div className="text-base text-body"><Money kobo={100} /></div>
    </div>
  );
}

export function InContext() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <div className="flex justify-between items-center border-b border-border-default pb-3">
        <span className="text-sm text-body">Premium amount</span>
        <span className="font-medium"><Money kobo={4500000} /></span>
      </div>
      <div className="flex justify-between items-center border-b border-border-default pb-3">
        <span className="text-sm text-body">Commission (GTBank)</span>
        <span className="font-medium text-fg-success-strong"><Money kobo={22500} /></span>
      </div>
      <div className="flex justify-between items-center border-b border-border-default pb-3">
        <span className="text-sm text-body">Commission (Insureflow)</span>
        <span className="font-medium text-fg-success-strong"><Money kobo={22500} /></span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm font-semibold text-heading">Insurer payable</span>
        <span className="font-semibold"><Money kobo={4455000} /></span>
      </div>
    </div>
  );
}
