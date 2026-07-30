type JsonRecord = Record<string, unknown>;

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** Shallow key-by-key diff -- these are shallow state snapshots (status
 * fields, ids, amounts), not deep objects, so a recursive diff library
 * would be overkill. Shows only keys that changed or were added/removed. */
export function StateDiff({
  before,
  after,
}: {
  before: JsonRecord | null;
  after: JsonRecord | null;
}) {
  if (!before && !after) {
    return <p className="text-sm text-body-subtle">No state recorded for this event.</p>;
  }

  const keys = new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]);
  const rows = [...keys].filter((key) => {
    const beforeValue = before?.[key];
    const afterValue = after?.[key];
    return JSON.stringify(beforeValue) !== JSON.stringify(afterValue);
  });

  if (rows.length === 0) {
    return <p className="text-sm text-body-subtle">No fields changed.</p>;
  }

  return (
    <table className="w-full text-left text-sm">
      <thead>
        <tr className="border-b border-border-default text-body-subtle">
          <th className="py-1.5 pr-4 font-medium">Field</th>
          <th className="py-1.5 pr-4 font-medium">Before</th>
          <th className="py-1.5 font-medium">After</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((key) => (
          <tr key={key} className="border-b border-border-default last:border-b-0">
            <td className="py-1.5 pr-4 font-mono text-xs text-heading">{key}</td>
            <td className="py-1.5 pr-4 text-fg-danger">{formatValue(before?.[key])}</td>
            <td className="py-1.5 text-fg-success-strong">{formatValue(after?.[key])}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
