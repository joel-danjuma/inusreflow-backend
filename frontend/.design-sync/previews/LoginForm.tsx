import { LoginForm } from "@/components/forms/LoginForm";

export function Default() {
  return (
    <div className="p-6 max-w-sm">
      <LoginForm next="/dashboard" />
    </div>
  );
}
