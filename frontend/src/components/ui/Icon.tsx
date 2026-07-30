/** Line-icon set ported from the Insureflow Design System's Icon component
 * (claude.ai/design 940d93f3, components/general/Icon.jsx) -- 24px grid,
 * 1.75px stroke, round caps/joins. Same glyph paths, typed for this codebase. */

export type IconName =
  | "x"
  | "check"
  | "chevron-down"
  | "chevron-up"
  | "chevron-right"
  | "chevron-updown"
  | "info"
  | "check-circle"
  | "alert-triangle"
  | "x-circle"
  | "copy"
  | "inbox"
  | "eye"
  | "eye-off"
  | "bell"
  | "log-out"
  | "search"
  | "trending-up"
  | "arrow-up-right"
  | "arrow-down-right"
  | "plus"
  | "more-horizontal"
  | "shield"
  | "credit-card"
  | "file-text"
  | "users"
  | "wallet"
  | "clock";

const PATHS: Record<IconName, React.ReactNode> = {
  x: (
    <>
      <line x1="6" y1="6" x2="18" y2="18" />
      <line x1="18" y1="6" x2="6" y2="18" />
    </>
  ),
  check: <polyline points="4 12.5 9.5 18 20 6.5" />,
  "chevron-down": <polyline points="6 9.5 12 15.5 18 9.5" />,
  "chevron-up": <polyline points="6 14.5 12 8.5 18 14.5" />,
  "chevron-right": <polyline points="9.5 5 15.5 12 9.5 19" />,
  "chevron-updown": (
    <>
      <polyline points="8 10 12 6 16 10" />
      <polyline points="8 14 12 18 16 14" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <line x1="12" y1="11" x2="12" y2="16.5" />
      <circle cx="12" cy="7.6" r="0.6" fill="currentColor" stroke="none" />
    </>
  ),
  "check-circle": (
    <>
      <circle cx="12" cy="12" r="9" />
      <polyline points="8 12.4 11 15.4 16.4 9" />
    </>
  ),
  "alert-triangle": (
    <>
      <path d="M12 4.2 21.2 20 2.8 20Z" />
      <line x1="12" y1="10" x2="12" y2="14.4" />
      <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
    </>
  ),
  "x-circle": (
    <>
      <circle cx="12" cy="12" r="9" />
      <line x1="9.2" y1="9.2" x2="14.8" y2="14.8" />
      <line x1="14.8" y1="9.2" x2="9.2" y2="14.8" />
    </>
  ),
  copy: (
    <>
      <rect x="9" y="9" width="12" height="12" rx="2.5" />
      <path d="M5 15a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2" />
    </>
  ),
  inbox: (
    <>
      <path d="M22 12h-6l-2 3h-4l-2-3H2" />
      <path d="M5.5 5.5h13l3.5 6.5v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-6z" />
    </>
  ),
  eye: (
    <>
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  "eye-off": (
    <>
      <path d="M3 3l18 18" />
      <path d="M10.6 6.1A9.6 9.6 0 0 1 12 6c6 0 9.5 6 9.5 6a16 16 0 0 1-3.2 3.8" />
      <path d="M6.4 8A16 16 0 0 0 2.5 12S6 18 12 18a9 9 0 0 0 3-.5" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8.5a6 6 0 0 0-12 0c0 6.5-2.5 8.5-2.5 8.5h17S18 15 18 8.5" />
      <path d="M10.2 20.5a2 2 0 0 0 3.6 0" />
    </>
  ),
  "log-out": (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="15 17 20 12 15 7" />
      <line x1="20" y1="12" x2="9" y2="12" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <line x1="16.5" y1="16.5" x2="21" y2="21" />
    </>
  ),
  "trending-up": (
    <>
      <polyline points="3 17 9.5 10.5 13.5 14.5 21 6.5" />
      <polyline points="15 6.5 21 6.5 21 12.5" />
    </>
  ),
  "arrow-up-right": (
    <>
      <line x1="7" y1="17" x2="17" y2="7" />
      <polyline points="8 7 17 7 17 16" />
    </>
  ),
  "arrow-down-right": (
    <>
      <line x1="7" y1="7" x2="17" y2="17" />
      <polyline points="17 8 17 17 8 17" />
    </>
  ),
  plus: (
    <>
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </>
  ),
  "more-horizontal": (
    <>
      <circle cx="5" cy="12" r="1.3" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1.3" fill="currentColor" stroke="none" />
    </>
  ),
  shield: <path d="M12 3l7 3v5c0 4.6-3 7.7-7 9-4-1.3-7-4.4-7-9V6z" />,
  "credit-card": (
    <>
      <rect x="2.5" y="5" width="19" height="14" rx="2.5" />
      <line x1="2.5" y1="9.5" x2="21.5" y2="9.5" />
    </>
  ),
  "file-text": (
    <>
      <path d="M13 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9z" />
      <polyline points="13 3 13 9 19 9" />
      <line x1="8.5" y1="13" x2="15.5" y2="13" />
      <line x1="8.5" y1="16.5" x2="13.5" y2="16.5" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 20a5.5 5.5 0 0 1 11 0" />
      <path d="M16 5.2a3.2 3.2 0 0 1 0 5.6" />
      <path d="M17.5 20a5.5 5.5 0 0 0-2.3-4.5" />
    </>
  ),
  wallet: (
    <>
      <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H18a1 1 0 0 1 1 1v1.5" />
      <rect x="3" y="7.5" width="18" height="12" rx="2.5" />
      <circle cx="16.5" cy="13.5" r="1.3" fill="currentColor" stroke="none" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 15.5 14" />
    </>
  ),
};

export function Icon({
  name,
  size = 18,
  stroke = 1.75,
  className = "",
}: {
  name: IconName;
  size?: number;
  stroke?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`block shrink-0 ${className}`}
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}
