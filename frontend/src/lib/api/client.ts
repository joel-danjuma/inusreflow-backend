import "server-only";
import { parseApiError } from "./errors";

const BASE_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1";

interface ApiFetchOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
  searchParams?: Record<string, string | number | boolean | undefined>;
  headers?: Record<string, string>;
}

export async function apiFetch<T>(path: string, opts: ApiFetchOptions = {}): Promise<T> {
  const url = new URL(BASE_URL + path);
  for (const [key, value] of Object.entries(opts.searchParams ?? {})) {
    // An empty string means "unfilled" for every GET-based filter form in
    // this app (native <form method="GET"> submits all fields, blank ones
    // included) -- treat it the same as absent rather than sending a
    // literal `?field=` the backend would validate as a real (malformed)
    // filter value.
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }

  const headers: Record<string, string> = { ...opts.headers };
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  let body: string | undefined;
  if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  const response = await fetch(url, {
    method: opts.method ?? "GET",
    headers,
    body,
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** Only used by the login Route Handler -- FastAPI's OAuth2PasswordRequestForm
 * requires application/x-www-form-urlencoded, not JSON. */
export async function apiFormPost(
  path: string,
  form: Record<string, string>
): Promise<Response> {
  const url = new URL(BASE_URL + path);
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(form).toString(),
    cache: "no-store",
  });
}

/** For multipart/form-data uploads (e.g. the Excel bulk-pay resolver) --
 * never set Content-Type manually here, the runtime sets the multipart
 * boundary itself when the body is a FormData instance. */
export async function apiFetchMultipart<T>(
  path: string,
  opts: { formData: FormData; token?: string | null }
): Promise<T> {
  const url = new URL(BASE_URL + path);
  const headers: Record<string, string> = {};
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: opts.formData,
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }
  return (await response.json()) as T;
}

/** For endpoints that return a raw file (e.g. the bulk-pay Excel template)
 * -- returns the Response unparsed so the caller (a Route Handler) can
 * stream the bytes and headers straight through, instead of the .json()
 * every other helper here does. */
export async function apiFetchBinary(
  path: string,
  opts: { token?: string | null } = {}
): Promise<Response> {
  const url = new URL(BASE_URL + path);
  const headers: Record<string, string> = {};
  if (opts.token) headers.Authorization = `Bearer ${opts.token}`;

  const response = await fetch(url, { method: "GET", headers, cache: "no-store" });
  if (!response.ok) {
    throw await parseApiError(response);
  }
  return response;
}
