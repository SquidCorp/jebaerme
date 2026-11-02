import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Chat } from "@/app/chat";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function streamResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200 });
}

describe("Chat", () => {
  it("streams an assistant reply", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamResponse(["Hi"])));

    render(<Chat />);
    expect(screen.getByText("Ask the model something.")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Message"), "Hello");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("YOU")).toBeInTheDocument();
    expect(await screen.findByText("Hi")).toBeInTheDocument();
  });

  it("shows a gateway error", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "upstream_error" }), {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    render(<Chat />);
    await user.type(screen.getByLabelText("Message"), "Hello");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("upstream_error")).toBeInTheDocument();
  });
});
