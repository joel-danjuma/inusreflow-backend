"use client";

/** A GET-submitting <select> that narrows the dashboard to one counterparty
 * via a URL search param -- no client-side fetch, just plain navigation, so
 * the dashboard itself stays a server component. Auto-submits on change
 * (native <form> behavior, no fetch/JS state) rather than requiring a
 * separate "Apply" button.
 */
export function CounterpartySelector({
  paramName,
  selectedId,
  options,
  placeholder,
}: {
  paramName: string;
  selectedId?: string;
  options: { id: string; name: string }[];
  placeholder: string;
}) {
  if (options.length === 0) return null;

  return (
    <form method="get" className="mb-4">
      <select
        name={paramName}
        defaultValue={selectedId ?? ""}
        onChange={(e) => e.currentTarget.form?.requestSubmit()}
        className="block w-full max-w-xs rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand sm:w-auto"
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}
          </option>
        ))}
      </select>
    </form>
  );
}
