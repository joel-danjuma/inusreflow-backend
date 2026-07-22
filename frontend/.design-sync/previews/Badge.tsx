import { Badge } from "@/components/ui/Badge";

export function AllVariants() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <Badge variant="brand">Brand</Badge>
      <Badge variant="neutral">Neutral</Badge>
      <Badge variant="gray">Gray</Badge>
      <Badge variant="danger">Danger</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="dark">Dark</Badge>
    </div>
  );
}

export function InContext() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <Badge variant="success">Approved</Badge>
      <Badge variant="warning">Pending</Badge>
      <Badge variant="danger">Rejected</Badge>
      <Badge variant="dark">Suspended</Badge>
      <Badge variant="neutral">Due</Badge>
      <Badge variant="brand">In progress</Badge>
    </div>
  );
}
