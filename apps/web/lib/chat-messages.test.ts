import { describe, expect, it } from "vitest";
import {
  appendAssistantText,
  type ChatMessage,
  createChatMessage,
  dropEmptyAssistant,
} from "@/lib/chat-messages";

function message(
  id: string,
  role: ChatMessage["role"],
  text: string,
): ChatMessage {
  return { id, role, text };
}

describe("createChatMessage", () => {
  it("assigns a role, text, and id", () => {
    const created = createChatMessage("user", "hello");
    expect(created.role).toBe("user");
    expect(created.text).toBe("hello");
    expect(created.id.length).toBeGreaterThan(0);
  });
});

describe("appendAssistantText", () => {
  it("appends to the last assistant message", () => {
    const current = [
      message("u", "user", "hi"),
      message("a", "assistant", "Hel"),
    ];
    expect(appendAssistantText(current, "lo")).toEqual([
      message("u", "user", "hi"),
      message("a", "assistant", "Hello"),
    ]);
  });

  it("leaves the list unchanged without a trailing assistant", () => {
    const current = [message("u", "user", "hi")];
    expect(appendAssistantText(current, "lo")).toBe(current);
    expect(appendAssistantText([], "lo")).toEqual([]);
  });
});

describe("dropEmptyAssistant", () => {
  it("removes a trailing empty assistant placeholder", () => {
    const current = [message("u", "user", "hi"), message("a", "assistant", "")];
    expect(dropEmptyAssistant(current)).toEqual([message("u", "user", "hi")]);
  });

  it("keeps a trailing assistant that already has text", () => {
    const current = [message("a", "assistant", "ok")];
    expect(dropEmptyAssistant(current)).toBe(current);
  });
});
