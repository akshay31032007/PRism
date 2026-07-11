import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const body = await request.text();

    const res = await fetch(`${BACKEND_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      // Analysis can take 30–90s — no client-side timeout
      signal: AbortSignal.timeout(180_000),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const message =
        (data as { detail?: string; message?: string }).detail ??
        (data as { detail?: string; message?: string }).message ??
        `Analysis API returned ${res.status}`;

      return NextResponse.json({ detail: message }, { status: res.status });
    }

    return NextResponse.json(data);
  } catch (err) {
    const message =
      err instanceof Error && err.name === "TimeoutError"
        ? "Analysis timed out after 3 minutes. Try again or use a smaller PR."
        : err instanceof Error
          ? err.message
          : "Failed to reach analysis backend.";

    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
