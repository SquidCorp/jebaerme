import { NextResponse } from "next/server";

import { proxyPythonPostStream } from "@/lib/python";

export async function POST(request: Request) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid_json" }, { status: 400 });
  }
  return proxyPythonPostStream("/chat", payload);
}
