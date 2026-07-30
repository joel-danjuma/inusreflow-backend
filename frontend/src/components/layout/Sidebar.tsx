import { isNavItemVisible, NAV_ITEMS, type NavItem } from "@/lib/nav-config";
import type { Role } from "@/lib/auth/rbac";
import { NavLink } from "./NavLink";

const SECTION_ORDER: NavItem["section"][] = ["Broker", "Payments", "Insurer", "Admin", "Account"];

export function Sidebar({ role }: { role: Role }) {
  const visibleBySection = SECTION_ORDER.map((section) => ({
    section,
    items: NAV_ITEMS.filter((item) => item.section === section && isNavItemVisible(item, role)),
  })).filter((group) => group.items.length > 0);

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border-default bg-neutral-secondary-soft md:block">
      <div className="flex h-full flex-col gap-6 overflow-y-auto px-3 py-4">
        <NavLink href="/dashboard" icon="trending-up">
          Dashboard
        </NavLink>

        {visibleBySection.map(({ section, items }) => (
          <div key={section}>
            <p className="mb-2 px-2 text-xs font-medium tracking-wide text-body-subtle uppercase">
              {section}
            </p>
            <nav className="flex flex-col gap-2">
              {items.map((item) => (
                <NavLink key={item.href} href={item.href} icon={item.icon}>
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        ))}
      </div>
    </aside>
  );
}
