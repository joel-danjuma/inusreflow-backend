import { Input } from "@/components/ui/Input";

export function Default() {
  return (
    <div className="p-4 max-w-sm space-y-4">
      <Input id="email" label="Email address" type="email" placeholder="broker@company.com" />
      <Input id="phone" label="Phone number" type="tel" placeholder="+234 800 000 0000" />
    </div>
  );
}

export function WithError() {
  return (
    <div className="p-4 max-w-sm space-y-4">
      <Input
        id="email-error"
        label="Email address"
        type="email"
        defaultValue="not-an-email"
        error="Please enter a valid email address."
      />
      <Input
        id="password-error"
        label="Password"
        type="password"
        defaultValue="short"
        error="Password must be at least 8 characters."
      />
    </div>
  );
}

export function Disabled() {
  return (
    <div className="p-4 max-w-sm space-y-4">
      <Input id="disabled-email" label="Email address" type="email" defaultValue="admin@insureflow.com" disabled />
      <Input id="disabled-role" label="Role" defaultValue="Insureflow Admin" disabled />
    </div>
  );
}
