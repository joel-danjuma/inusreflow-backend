import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant =
  | "brand"
  | "secondary"
  | "tertiary"
  | "success"
  | "danger"
  | "warning"
  | "dark"
  | "ghost";
export type ButtonSize = "xs" | "sm" | "base" | "lg" | "xl";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  brand:
    "bg-brand text-white border-transparent hover:bg-brand-strong active:bg-brand-press focus-visible:ring-brand-medium",
  dark: "bg-dark text-white border-transparent hover:bg-dark-strong focus-visible:ring-neutral-tertiary",
  secondary:
    "bg-neutral-primary-soft text-heading border-border-default-medium hover:bg-neutral-secondary-soft focus-visible:ring-neutral-tertiary",
  tertiary:
    "bg-transparent text-heading border-transparent hover:bg-neutral-secondary-soft focus-visible:ring-neutral-tertiary-soft",
  success:
    "bg-success text-white border-transparent hover:bg-success-strong focus-visible:ring-success-medium",
  danger:
    "bg-danger text-white border-transparent hover:bg-danger-strong focus-visible:ring-danger-medium",
  warning:
    "bg-warning text-white border-transparent hover:bg-warning-strong focus-visible:ring-warning-medium",
  ghost:
    "bg-transparent text-heading border-transparent hover:bg-neutral-secondary-soft focus-visible:ring-neutral-tertiary",
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  xs: "text-xs px-3 py-1.5",
  sm: "text-sm px-3 py-2",
  base: "text-sm px-4 py-2.5",
  lg: "text-base px-5 py-3",
  xl: "text-base px-6 py-3.5",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

export function Button({
  variant = "brand",
  size = "base",
  className = "",
  disabled,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full border font-semibold whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:border-border-default-medium disabled:bg-disabled disabled:text-fg-disabled active:translate-y-px ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
      disabled={disabled}
      {...rest}
    >
      {children}
    </button>
  );
}
