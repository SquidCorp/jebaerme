import { describe, expect, it } from "vitest";
import { consumeChatStream } from "@/lib/consume-chat-stream";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

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

describe("consumeChatStream", () => {
  it("emits decoded stream pieces", async () => {
    const pieces: string[] = [];
    await consumeChatStream(streamResponse(["Hel", "lo"]), (piece) => {
      pieces.push(piece);
    });
    expect(pieces.join("")).toBe("Hello");
  });

  it("throws a gateway error for a failed JSON response", async () => {
    await expect(
      consumeChatStream(jsonResponse(502, { error: "upstream_error" }), () => {
        throw new Error("should not read a body");
      }),
    ).rejects.toThrow("upstream_error");
  });

  it("throws when the response has no body", async () => {
    await expect(
      consumeChatStream(new Response(null, { status: 200 }), () => undefined),
    ).rejects.toThrow("Gateway returned an empty stream");
  });
});
