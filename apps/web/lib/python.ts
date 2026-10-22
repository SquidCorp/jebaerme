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
