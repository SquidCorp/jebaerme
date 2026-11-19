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

    expect(await screen.findByText("You")).toBeInTheDocument();
    expect(await screen.findByText("Hi")).toBeInTheDocument();
    expect(
      screen
        .getByText("You")
        .closest("li")
        ?.querySelector("img")
        ?.getAttribute("src"),
    ).toContain("avatar-visitor.png");
    expect(
      screen
        .getByText("Model")
        .closest("li")
        ?.querySelector("img")
        ?.getAttribute("src"),
    ).toContain("avatar.png");
  });

  it("submits on Enter and keeps Shift+Enter as a newline", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(streamResponse(["Hi"]));
    vi.stubGlobal("fetch", fetchMock);

    render(<Chat />);
    const field = screen.getByLabelText("Message");
    await user.type(field, "Hello{Shift>}{Enter}{/Shift}");
    expect(fetchMock).not.toHaveBeenCalled();

    await user.type(field, "{Enter}");
    expect(fetchMock).toHaveBeenCalledTimes(1);
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

async function renderSentChat(message: string, chunks: string[]) {
  const user = userEvent.setup();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(streamResponse(chunks)));
  render(<Chat />);
  await user.type(screen.getByLabelText("Message"), message);
  await user.click(screen.getByRole("button", { name: "Send" }));
}

describe("Chat markdown", () => {
  it("renders assistant markdown as formatted HTML", async () => {
    await renderSentChat("Hello", ["**Hi**"]);
    expect(await screen.findByText("Hi")).toBeInTheDocument();
    const modelItem = screen.getByText("Model").closest("li");
    expect(modelItem?.querySelector("strong")?.textContent).toBe("Hi");
  });

  it("leaves user markdown as literal text", async () => {
    await renderSentChat("**plain**", ["ok"]);
    expect(await screen.findByText("ok")).toBeInTheDocument();
    const youItem = screen.getByText("You").closest("li");
    expect(youItem?.querySelector("strong")).toBeNull();
    expect(youItem).toHaveTextContent("**plain**");
  });

  it("renders GFM tables in assistant bubbles", async () => {
    await renderSentChat("Hello", ["| a | b |\n| --- | --- |\n| 1 | 2 |\n"]);
    expect(await screen.findByRole("table")).toBeInTheDocument();
    const table = screen
      .getByText("Model")
      .closest("li")
      ?.querySelector("table");
    expect(table).not.toBeNull();
    expect(table).toHaveTextContent("1");
    expect(table).toHaveTextContent("2");
  });

  it("opens assistant links in a new tab", async () => {
    await renderSentChat("Hello", ["[docs](https://example.com)"]);
    expect(await screen.findByText("docs")).toBeInTheDocument();
    const link = screen
      .getByText("Model")
      .closest("li")
      ?.querySelector(
        'a[href="https://example.com"][target="_blank"][rel="noreferrer"]',
      );
    expect(link).not.toBeNull();
  });

  it("does not execute raw HTML in assistant markdown", async () => {
    await renderSentChat("Hello", ["<script>alert(1)</script>"]);
    const modelItem = (
      await screen.findByText("<script>alert(1)</script>")
    ).closest("li");
    expect(modelItem?.querySelector("script")).toBeNull();
    expect(modelItem).toHaveTextContent("<script>alert(1)</script>");
  });
});
