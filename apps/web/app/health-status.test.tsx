import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HealthStatus } from "@/app/health-status";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("HealthStatus", () => {
  it("renders a healthy payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", env: "dev" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<HealthStatus />);
    expect(screen.getByText("Checking health…")).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
    expect(screen.getByText("dev")).toBeInTheDocument();
  });

  it("renders a gateway error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "upstream_error" }), {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<HealthStatus />);
    expect(await screen.findByText("upstream_error")).toBeInTheDocument();
  });
});
