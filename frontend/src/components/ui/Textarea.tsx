import type { TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  id: string;
  error?: string;
}

export function Textarea({ label, id, error, className = "", ...rest }: TextareaProps) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-medium text-heading">
        {label}
      </label>
      <textarea
        id={id}
        rows={3}
        className={`block w-full rounded-base border bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs transition-all placeholder:text-body focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:bg-disabled disabled:text-fg-disabled ${
          error
            ? "border-border-danger focus:border-border-danger focus:ring-danger"
            : "border-border-default-medium hover:border-border-default-strong focus:border-border-brand focus:ring-brand"
        } ${className}`}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        {...rest}
      />
      {error && (
        <p id={`${id}-error`} className="mt-1.5 text-sm text-fg-danger">
          {error}
        </p>
      )}
    </div>
  );
}
