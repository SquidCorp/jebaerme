import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

export async function proxyPythonGet(path: `/${string}`): Promise<NextResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
    if (!response.ok) {
      return NextResponse.json({ error: "upstream_error" }, { status: 502 });
    }
    const payload: unknown = await response.json();
    return NextResponse.json(payload);
  } catch {
    return NextResponse.json({ error: "upstream_unreachable" }, { status: 502 });
  }
}

export async function proxyPythonPostStream(
  path: `/${string}`,
  body: unknown,
): Promise<NextResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    if (!response.ok) {
      return NextResponse.json({ error: "upstream_error" }, { status: 502 });
    }
    if (!response.body) {
      return NextResponse.json({ error: "upstream_error" }, { status: 502 });
    }
    return new NextResponse(response.body, {
      status: 200,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") ?? "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return NextResponse.json({ error: "upstream_unreachable" }, { status: 502 });
  }
}
