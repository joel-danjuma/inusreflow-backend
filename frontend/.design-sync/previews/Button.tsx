import { Button } from "@/components/ui/Button";

export function Variants() {
  return (
    <div className="flex flex-wrap gap-3 p-4">
      <Button variant="brand">Brand</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="tertiary">Tertiary</Button>
      <Button variant="success">Success</Button>
      <Button variant="danger">Danger</Button>
      <Button variant="warning">Warning</Button>
      <Button variant="dark">Dark</Button>
      <Button variant="ghost">Ghost</Button>
    </div>
  );
}

export function Sizes() {
  return (
    <div className="flex flex-wrap items-center gap-3 p-4">
      <Button size="xs">Extra small</Button>
      <Button size="sm">Small</Button>
      <Button size="base">Base</Button>
      <Button size="lg">Large</Button>
      <Button size="xl">Extra large</Button>
    </div>
  );
}

export function States() {
  return (
    <div className="flex flex-wrap gap-3 p-4">
      <Button variant="brand">Active</Button>
      <Button variant="brand" disabled>Disabled</Button>
      <Button variant="secondary" disabled>Secondary disabled</Button>
    </div>
  );
}

export function FullWidth() {
  return (
    <div className="p-4 w-64">
      <Button variant="brand" className="w-full">Sign in</Button>
    </div>
  );
}
