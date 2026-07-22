import { MonthlyTrendsChart } from "@/components/dashboard/MonthlyTrendsChart";

const sixMonths = [
  { month: "2024-01", amount_kobo: 245000000 },
  { month: "2024-02", amount_kobo: 312000000 },
  { month: "2024-03", amount_kobo: 289000000 },
  { month: "2024-04", amount_kobo: 421000000 },
  { month: "2024-05", amount_kobo: 378000000 },
  { month: "2024-06", amount_kobo: 510000000 },
];

const twelveMonths = [
  { month: "2023-07", amount_kobo: 180000000 },
  { month: "2023-08", amount_kobo: 220000000 },
  { month: "2023-09", amount_kobo: 195000000 },
  { month: "2023-10", amount_kobo: 260000000 },
  { month: "2023-11", amount_kobo: 300000000 },
  { month: "2023-12", amount_kobo: 450000000 },
  { month: "2024-01", amount_kobo: 245000000 },
  { month: "2024-02", amount_kobo: 312000000 },
  { month: "2024-03", amount_kobo: 289000000 },
  { month: "2024-04", amount_kobo: 421000000 },
  { month: "2024-05", amount_kobo: 378000000 },
  { month: "2024-06", amount_kobo: 510000000 },
];

export function SixMonths() {
  return (
    <div className="p-4">
      <MonthlyTrendsChart data={sixMonths} />
    </div>
  );
}

export function TwelveMonths() {
  return (
    <div className="p-4">
      <MonthlyTrendsChart data={twelveMonths} />
    </div>
  );
}

export function Empty() {
  return (
    <div className="p-4">
      <MonthlyTrendsChart data={[]} />
    </div>
  );
}
