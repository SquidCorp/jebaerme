import { afterEach, describe, expect, it, vi } from "vitest";
import { proxyPythonGet, proxyPythonPostStream } from "@/lib/python";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("proxyPythonGet", () => {
  it("forwards a successful JSON payload", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { status: "ok", env: "dev" }));
    vi.stubGlobal("fetch", fetchMock);

    const response = await proxyPythonGet("/health");
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/health", {
      cache: "no-store",
    });
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      status: "ok",
      env: "dev",
    });
  });

  it("maps a failed upstream response to 502", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(500, { detail: "boom" })),
    );
    const response = await proxyPythonGet("/health");
    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({ error: "upstream_error" });
  });

  it("maps a network failure to 502", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("ECONNREFUSED")),
    );
    const response = await proxyPythonGet("/health");
    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      error: "upstream_unreachable",
    });
  });
});

describe("proxyPythonPostStream", () => {
  it("pipes a successful stream", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode("token"));
        controller.close();
      },
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        }),
      ),
    );

    const response = await proxyPythonPostStream("/chat", { message: "hi" });
    expect(response.status).toBe(200);
    await expect(response.text()).resolves.toBe("token");
  });

  it("maps an empty body to 502", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 })),
    );
    const response = await proxyPythonPostStream("/chat", { message: "hi" });
    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({ error: "upstream_error" });
  });
});
