# Insureflow Design System — Conventions

## Theme

Insureflow uses a **dark-first token system**. Color tokens like `text-heading`, `text-body`, `text-body-subtle`, and `text-primary` resolve to light colors intended for dark backgrounds. When composing previews or designing screens, place text-heavy components on `bg-neutral-primary-soft` (dark navy) rather than white. The app's global shell background is dark; components are designed to be seen on it.

## Money & Amounts

All monetary values are **integer kobo** (1 NGN = 100 kobo). Never use floats. Use the `<Money>` component to display any currency value — it accepts `amountKobo: number` and an optional `size` prop (`"sm" | "base" | "lg"`). Commission rates are **integer basis points** (bps), never floats.

## Status Badges

Six domain-specific badge components map to their respective enum values:

| Component | Valid statuses |
|---|---|
| `OnboardingStatusBadge` | `pending`, `approved`, `rejected`, `suspended` |
| `PolicyStatusBadge` | `active`, `lapsed`, `cancelled`, `pending` |
| `InstallmentStatusBadge` | `due`, `overdue`, `paid`, `cancelled` |
| `PaymentStatusBadge` | `initiated`, `processing`, `success`, `failed` |
| `SettlementPayoutStatusBadge` | `pending`, `success`, `failed` |
| `ReminderStatusBadge` | `sent`, `failed`, `pending` |

Use these instead of the generic `<Badge>` for domain entities.

## Table Composition

`Table` is a compound component — always compose the full hierarchy:

```jsx
<Table>
  <TableHead>
    <TableRow>
      <TableHeaderCell>Column</TableHeaderCell>
    </TableRow>
  </TableHead>
  <TableBody>
    <TableRow>
      <TableCell>Value</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

`EmptyState` renders as a `<tbody>` row spanning all columns — use it as a child of `<TableBody>` when the data set is empty.

## Modal

`Modal` uses the native `<dialog>` element and calls `showModal()` internally. Always pass both `open` and `onClose` props:

```jsx
<Modal open={isOpen} onClose={() => setIsOpen(false)} title="Confirm action">
  {/* content */}
</Modal>
```

When designing forms inside a modal, use `Input` / `Textarea` / `Button` from the same system. The backdrop dims the page automatically.

## MaskedField

`MaskedField` renders a sensitive value (NIN, BVN, account number) with a reveal toggle. The `label` prop is **aria-only** and does not appear in the DOM — add a visible `<label>` or wrapping `<span>` yourself when the field context requires a visual label.

## MonthlyTrendsChart

The `data` prop expects an array of `{ month: string; amount_kobo: number }` where `month` is an **ISO `"YYYY-MM"` string** (e.g. `"2024-01"`). The chart splits on `-` internally to extract year/month — locale strings like `"Jan 2024"` will produce invalid dates on the axis.

## Topbar & LogoutButton

`Topbar` accepts a `role` prop of type `"insureflow_admin" | "insurance_company_admin" | "broker_admin" | "broker_staff"` and renders the appropriate role label alongside the Insureflow brand. `LogoutButton` renders a ghost-style button — it is designed to sit inside the `Topbar` on a dark background, not standalone on white.

## Ghost Buttons

`Button` with `variant="ghost"` is transparent/minimal and invisible on light backgrounds. Always compose ghost buttons on `bg-neutral-primary-soft` or equivalent dark surface.

## StateDiff

`StateDiff` renders a before/after JSON comparison for audit logs. It accepts `before: Record<string, unknown> | null` and `after: Record<string, unknown>`. Both values can be any plain object; pass `null` for `before` on newly created records.

## PaymentRemindersBanner

`PaymentRemindersBanner` uses `sessionStorage` to track dismissed state. It will always render on the first mount in a preview context. Pass `overdueCount: number` to control the message copy.

## Forms

`LoginForm` and `ChangePasswordForm` are self-contained controlled forms. `LoginForm` accepts a `next: string` prop (the redirect URL after successful login — not a Next.js import). Both forms include their own submit button and validation state.
