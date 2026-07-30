import { NextResponse } from "next/server";
import { apiFetchBinary } from "@/lib/api/client";
import { ApiError } from "@/lib/api/errors";
import { getAuthToken } from "@/lib/auth/session";

/** Proxies the bulk-pay reference-number .xlsx template through the BFF --
 * a bare <a href> can't attach the session's Authorization header itself,
 * so this forwards it server-side and streams the file straight back. */
export async function GET() {
  const token = await getAuthToken();

  try {
    const upstream = await apiFetchBinary("/payments/bulk/template", { token });
    return new NextResponse(upstream.body, {
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") ??
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition":
          upstream.headers.get("Content-Disposition") ??
          'attachment; filename="bulk-pay-reference-template.xlsx"',
      },
    });
  } catch (error) {
    if (error instanceof ApiError) {
      return NextResponse.json({ detail: error.message }, { status: error.status });
    }
    throw error;
  }
}
