"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Icon, type IconName } from "@/components/ui/Icon";

export function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon?: IconName;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={`flex items-center gap-2.5 rounded-sm px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-brand text-white"
          : "text-body hover:bg-neutral-primary-strong hover:text-heading"
      }`}
    >
      {icon && <Icon name={icon} size={17} />}
      {children}
    </Link>
  );
}
