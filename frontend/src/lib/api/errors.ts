/**
 * FastAPI's own error shapes, handled distinctly rather than shown as a
 * generic toast:
 *  - 401: session invalid, caller should redirect to /login
 *  - 403: permission-denied inline message (should be rare given
 *    nav-gating, but the backend is the real gate)
 *  - 404: not-found
 *  - 409: conflict -- backend 409 `detail` strings are already
 *    human-readable ("Broker has no active insurer assignment", etc.)
 *  - 422: Pydantic validation errors -- `detail` is an ARRAY of
 *    {loc, msg, type} objects, not a string
 *  - 429: rate limit -- backend's own message is shown verbatim
 *  - 502: Squad integration failure -- never show the raw Squad error text
 */

export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: FieldError[];

  constructor(status: number, message: string, fieldErrors: FieldError[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

interface PydanticValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

function isPydanticValidationErrors(detail: unknown): detail is PydanticValidationError[] {
  return (
    Array.isArray(detail) &&
    detail.every(
      (e) => e && typeof e === "object" && "loc" in e && "msg" in e && Array.isArray(e.loc)
    )
  );
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // non-JSON body (rare) -- fall through to the status-based default below
  }

  const detail =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : null;

  if (response.status === 422 && isPydanticValidationErrors(detail)) {
    const fieldErrors = detail.map((e) => ({
      field: e.loc.filter((p) => p !== "body").join("."),
      message: e.msg,
    }));
    // A @model_validator(mode="after") error (e.g. "broker_id is required
    // for scope='broker'") has no specific field path -- surface its
    // message directly rather than a generic "fix the highlighted fields"
    // that points at nothing.
    const wholeModelError = fieldErrors.find((e) => e.field === "");
    if (wholeModelError && fieldErrors.length === 1) {
      return new ApiError(422, wholeModelError.message, []);
    }
    return new ApiError(422, "Please fix the highlighted fields.", fieldErrors);
  }

  if (response.status === 429) {
    return new ApiError(
      429,
      typeof detail === "string" ? detail : "Too many payment attempts, try again shortly."
    );
  }

  if (response.status === 502) {
    return new ApiError(502, "Payment provider is temporarily unavailable. Try again shortly.");
  }

  if (response.status === 401) {
    return new ApiError(401, "Your session has expired. Please log in again.");
  }

  if (response.status === 403) {
    return new ApiError(403, "You don't have permission to do that.");
  }

  if (response.status === 404) {
    return new ApiError(404, typeof detail === "string" ? detail : "Not found.");
  }

  if (typeof detail === "string") {
    return new ApiError(response.status, detail);
  }

  return new ApiError(response.status, `Request failed (${response.status}).`);
}
