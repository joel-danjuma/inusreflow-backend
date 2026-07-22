# Design Sync Notes — Insureflow Frontend

## Repo shape
Next.js 16 app (not a standalone component library). No `dist/` — converter runs in synth-entry mode from `src/components/`.

## CSS
Tailwind v4 via `@tailwindcss/postcss`. CSS is compiled at sync time using a PostCSS script (see Re-sync risks). `cssEntry` points to `compiled-tokens.css` (the compiled output, not the source `globals.css`).

Compile command:
```bash
node /private/tmp/compile-tw.mjs
```

Or inline:
```bash
node --input-type=module --eval "
import { createRequire } from 'module';
import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';
import { pathToFileURL } from 'url';
const frontendDir = '/Users/joeldanjuma/Desktop/Insureflow_v1/frontend';
const require = createRequire(pathToFileURL(frontendDir + '/package.json'));
const postcss = require(frontendDir + '/node_modules/postcss');
const { default: tailwindcss } = await import(frontendDir + '/node_modules/@tailwindcss/postcss/dist/index.mjs');
const from = resolve(frontendDir, 'src/app/globals.css');
const to = resolve(frontendDir, 'compiled-tokens.css');
writeFileSync(to, (await postcss([tailwindcss()]).process(readFileSync(from, 'utf8'), { from, to })).css);
console.log('CSS compiled');
"
```

## Excluded components
These components use `next/link` or `next/navigation` which don't render correctly outside Next.js context:
- `NavLink` — uses `usePathname()` from `next/navigation`
- `Sidebar` — imports NavLink (excluded transitively)
- `Pagination` — uses `next/link`
- `LoginForm`, `ActivateForm`, `PaymentStatusPoller`, `RetrySettlementButton` — use Next.js router/navigation
- `InstallmentsPaymentTable` — uses Next.js Link
- `BrokerRemindersTable`, `ClientPortfolioTable` — use Next.js Link

All excluded via `componentSrcMap: null` in config.json.

## Path aliases
`tsconfig.json` has `@/* → ./src/*`. The converter reads this via `--config` pointing at `tsconfig.json`.

## Entry point

The design system entry is `src/ds-entry.ts` (not `ds-entry.ts` at repo root). Always pass `--entry ./src/ds-entry.ts` to `package-build.mjs`. The synth-entry fallback (no `--entry`) will pull in Next.js router internals via transitive imports, causing `process is not defined` in the browser render check.

Re-sync build command:
```bash
node .ds-sync/package-build.mjs --config .design-sync/config.json --node-modules ./node_modules --entry ./src/ds-entry.ts --out ./ds-bundle
```

## Re-sync risks
- `compiled-tokens.css` is a build artifact and must be regenerated before each re-sync if `globals.css` or component files changed (Tailwind v4 scans content for used utilities)
- The Tailwind utility class set changes when new components or classes are added — a stale `compiled-tokens.css` may be missing utilities used by newer components
- Next.js-specific components added to `src/components/` in the future may need to be added to `componentSrcMap` exclusions
- `@/lib/` modules are plain TypeScript with no Next.js deps — safe as long as no one adds `next/` imports to them
- The `compiled-tokens.css` path in `cfg.cssEntry` is relative to the frontend root; ensure the file exists before running the converter
