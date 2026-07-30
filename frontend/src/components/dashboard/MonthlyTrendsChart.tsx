"use client";

import { useState } from "react";
import { formatNaira } from "@/lib/money";

const COMPACT_NAIRA = new Intl.NumberFormat("en-NG", {
  style: "currency",
  currency: "NGN",
  notation: "compact",
  maximumFractionDigits: 1,
});

function monthLabel(monthKey: string): string {
  const [year, month] = monthKey.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-NG", { month: "short" });
}

/** Rounds up to a clean 1/2/5 * 10^n step so axis ticks read as round numbers. */
function niceMax(value: number): number {
  if (value <= 0) return 100;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

const CHART_HEIGHT_PX = 200;

export function MonthlyTrendsChart({
  data,
}: {
  data: { month: string; amount_kobo: number }[];
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const maxAmount = Math.max(...data.map((d) => d.amount_kobo), 0);
  const axisMax = niceMax(maxAmount);
  const peakIndex = data.reduce(
    (best, d, i) => (d.amount_kobo > (data[best]?.amount_kobo ?? -1) ? i : best),
    0
  );
  const hasActivity = maxAmount > 0;

  return (
    <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
      <h2 className="text-base font-medium text-heading">Premiums Trend</h2>
      <p className="mt-1 text-sm text-body">Successfully collected premiums, last 6 months.</p>

      {!hasActivity ? (
        <p className="mt-8 mb-4 text-center text-sm text-body">
          No premium activity in the last 6 months yet.
        </p>
      ) : (
        <div className="mt-6 flex gap-3">
          <div
            className="flex w-12 flex-none flex-col justify-between text-right text-xs text-body-subtle"
            style={{ height: CHART_HEIGHT_PX }}
          >
            <span>{COMPACT_NAIRA.format(axisMax / 100)}</span>
            <span>{COMPACT_NAIRA.format(axisMax / 200)}</span>
            <span>0</span>
          </div>

          <div className="flex-1">
            <div className="relative flex items-end justify-between gap-2 border-l border-border-light">
              {[0, 0.5, 1].map((fraction) => (
                <div
                  key={fraction}
                  className="absolute right-0 left-0 border-t border-border-light"
                  style={{ bottom: fraction * CHART_HEIGHT_PX }}
                />
              ))}

              {data.map((point, i) => {
                const heightPx = Math.max(2, (point.amount_kobo / axisMax) * CHART_HEIGHT_PX);
                return (
                  <div
                    key={point.month}
                    className="relative flex flex-1 flex-col items-center justify-end"
                    style={{ height: CHART_HEIGHT_PX }}
                    onMouseEnter={() => setHoverIndex(i)}
                    onMouseLeave={() => setHoverIndex(null)}
                    onFocus={() => setHoverIndex(i)}
                    onBlur={() => setHoverIndex(null)}
                    tabIndex={0}
                    role="img"
                    aria-label={`${monthLabel(point.month)}: ${formatNaira(point.amount_kobo)}`}
                  >
                    {i === peakIndex && point.amount_kobo > 0 && (
                      <span className="mb-1 text-xs font-medium text-heading">
                        {COMPACT_NAIRA.format(point.amount_kobo / 100)}
                      </span>
                    )}
                    {hoverIndex === i && (
                      <div className="absolute bottom-full z-10 mb-2 rounded-default border border-border-default bg-neutral-primary-soft px-2.5 py-1.5 text-xs whitespace-nowrap shadow-md">
                        <p className="font-medium text-heading">
                          {formatNaira(point.amount_kobo)}
                        </p>
                        <p className="text-body-subtle">{monthLabel(point.month)}</p>
                      </div>
                    )}
                    <div
                      className="w-full max-w-6 rounded-t-sm bg-brand transition-opacity hover:opacity-80"
                      style={{ height: heightPx }}
                    />
                  </div>
                );
              })}
            </div>

            <div className="mt-2 flex justify-between gap-2">
              {data.map((point) => (
                <span key={point.month} className="flex-1 text-center text-xs text-body-subtle">
                  {monthLabel(point.month)}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
