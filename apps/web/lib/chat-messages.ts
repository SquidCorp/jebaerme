export type ChatRole = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  text: string;
};

export function createChatMessage(role: ChatRole, text: string): ChatMessage {
  return { id: crypto.randomUUID(), role, text };
}

export function appendAssistantText(
  messages: ChatMessage[],
  piece: string,
): ChatMessage[] {
  if (messages.length === 0) {
    return messages;
  }
  const last = messages[messages.length - 1];
  if (last === undefined || last.role !== "assistant") {
    return messages;
  }
  return [
    ...messages.slice(0, -1),
    { id: last.id, role: "assistant", text: last.text + piece },
  ];
}

export function dropEmptyAssistant(messages: ChatMessage[]): ChatMessage[] {
  const last = messages[messages.length - 1];
  if (last?.role === "assistant" && last.text === "") {
    return messages.slice(0, -1);
  }
  return messages;
}
