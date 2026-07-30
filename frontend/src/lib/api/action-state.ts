export interface ActionState<T = undefined> {
  status: "idle" | "success" | "error";
  message?: string;
  fieldErrors?: Record<string, string>;
  data?: T;
}

export const IDLE_STATE: ActionState<never> = { status: "idle" };
