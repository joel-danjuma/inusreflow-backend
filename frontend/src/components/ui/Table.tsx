import type { ReactNode } from "react";

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-base border border-border-default bg-neutral-primary-soft shadow-xs">
      <table className="w-full text-left text-sm text-body">{children}</table>
    </div>
  );
}

export function TableHead({ children }: { children: ReactNode }) {
  return (
    <thead className="border-b border-border-default bg-neutral-secondary-soft">
      <tr>{children}</tr>
    </thead>
  );
}

export function TableHeaderCell({ children }: { children: ReactNode }) {
  return <th className="px-6 py-3 text-sm font-medium text-body">{children}</th>;
}

export function TableBody({ children }: { children: ReactNode }) {
  return <tbody>{children}</tbody>;
}

export function TableRow({ children }: { children: ReactNode }) {
  return (
    <tr className="border-b border-border-default last:border-b-0 hover:bg-neutral-secondary-soft">
      {children}
    </tr>
  );
}

export function TableCell({
  children,
  header,
  className = "",
}: {
  children: ReactNode;
  header?: boolean;
  className?: string;
}) {
  const Tag = header ? "th" : "td";
  return (
    <Tag
      scope={header ? "row" : undefined}
      className={`px-6 py-4 whitespace-nowrap ${header ? "font-medium text-heading" : ""} ${className}`}
    >
      {children}
    </Tag>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="px-6 py-10 text-center text-sm text-body">{children}</p>;
}
