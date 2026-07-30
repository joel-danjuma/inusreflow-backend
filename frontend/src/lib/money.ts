const NAIRA_FORMATTER = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
});

export function koboToNaira(kobo: number): number {
  return kobo / 100;
}

export function formatNaira(kobo: number): string {
  return NAIRA_FORMATTER.format(koboToNaira(kobo));
}

export function formatBasisPoints(bps: number): string {
  return `${(bps / 100).toLocaleString("en-NG", { maximumFractionDigits: 2 })}%`;
}
