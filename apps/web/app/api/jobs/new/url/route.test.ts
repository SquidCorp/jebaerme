import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "@/app/api/jobs/new/url/route";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("POST /api/jobs/new/url", () => {
  it("rejects invalid JSON", async () => {
    const response = await POST(
      new Request("http://localhost/api/jobs/new/url", {
        method: "POST",
        body: "{",
        headers: { "Content-Type": "application/json" },
      }),
    );
    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: "invalid_json" });
  });

  it("proxies a valid payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ job_title: "Engineer" }), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await POST(
      new Request("http://localhost/api/jobs/new/url", {
        method: "POST",
        body: JSON.stringify({ ad_url: "https://jobs.example.com/ad" }),
        headers: { "Content-Type": "application/json" },
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/jobs/new/url",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ ad_url: "https://jobs.example.com/ad" }),
      }),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ job_title: "Engineer" });
  });
});
