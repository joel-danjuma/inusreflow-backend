import type { InputHTMLAttributes, ReactNode } from "react";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "prefix"> {
  label: string;
  id: string;
  error?: string;
  prefix?: ReactNode;
  suffix?: ReactNode;
}

export function Input({ label, id, error, prefix, suffix, className = "", ...rest }: InputProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-medium text-heading">
        {label}
      </label>
      <div
        className={`flex items-center gap-2 rounded-base border bg-neutral-secondary-medium px-3 py-2.5 shadow-xs transition-all focus-within:ring-1 ${
          error
            ? "border-border-danger focus-within:border-border-danger focus-within:ring-danger"
            : "border-border-default-medium hover:border-border-default-strong focus-within:border-border-brand focus-within:ring-brand"
        } ${className}`}
      >
        {prefix && <span className="shrink-0 text-body-subtle">{prefix}</span>}
        <input
          id={id}
          className="min-w-0 flex-1 border-0 bg-transparent text-sm text-heading placeholder:text-body focus:outline-none disabled:cursor-not-allowed disabled:text-fg-disabled"
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${id}-error` : undefined}
          {...rest}
        />
        {suffix && <span className="shrink-0 text-body-subtle">{suffix}</span>}
      </div>
      {error && (
        <p id={`${id}-error`} className="mt-1.5 text-sm text-fg-danger">
          {error}
        </p>
      )}
    </div>
  );
}
