import Link from "next/link";

function pageHref(basePath: string, page: number): string {
  return page <= 1 ? basePath : `${basePath}?page=${page}`;
}

function pageWindow(current: number, total: number): (number | "ellipsis")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const pages = new Set<number>([1, total, current, current - 1, current + 1]);
  const sorted = [...pages].filter((p) => p >= 1 && p <= total).sort((a, b) => a - b);

  const result: (number | "ellipsis")[] = [];
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i] - sorted[i - 1] > 1) result.push("ellipsis");
    result.push(sorted[i]);
  }
  return result;
}

export function Pagination({
  basePath,
  currentPage,
  totalPages,
}: {
  basePath: string;
  currentPage: number;
  totalPages: number;
}) {
  if (totalPages <= 1) return null;

  const itemBase =
    "flex h-9 min-w-9 items-center justify-center border border-border-default-medium bg-neutral-secondary-medium px-3 text-sm font-medium text-body -ml-px first:ml-0 hover:bg-neutral-tertiary-medium hover:text-heading";

  return (
    <nav aria-label="Pagination" className="flex text-sm">
      <Link
        aria-disabled={currentPage <= 1}
        href={pageHref(basePath, Math.max(1, currentPage - 1))}
        className={`${itemBase} rounded-l-base ${currentPage <= 1 ? "pointer-events-none opacity-50" : ""}`}
      >
        Previous
      </Link>
      {pageWindow(currentPage, totalPages).map((entry, i) =>
        entry === "ellipsis" ? (
          <span key={`ellipsis-${i}`} className={`${itemBase} pointer-events-none`}>
            …
          </span>
        ) : (
          <Link
            key={entry}
            href={pageHref(basePath, entry)}
            aria-current={entry === currentPage ? "page" : undefined}
            className={`${itemBase} ${
              entry === currentPage ? "bg-neutral-tertiary-medium text-fg-brand" : ""
            }`}
          >
            {entry}
          </Link>
        )
      )}
      <Link
        aria-disabled={currentPage >= totalPages}
        href={pageHref(basePath, Math.min(totalPages, currentPage + 1))}
        className={`${itemBase} rounded-r-base ${currentPage >= totalPages ? "pointer-events-none opacity-50" : ""}`}
      >
        Next
      </Link>
    </nav>
  );
}
