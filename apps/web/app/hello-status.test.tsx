import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HelloStatus } from "@/app/hello-status";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("HelloStatus", () => {
  it("renders a hello payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok", text: "bonjour" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<HelloStatus />);
    expect(screen.getByText("Asking the model…")).toBeInTheDocument();
    expect(await screen.findByText("bonjour")).toBeInTheDocument();
  });
});
