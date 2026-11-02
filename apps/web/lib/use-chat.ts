"use client";

import {
  type FormEvent,
  type RefObject,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  appendAssistantText,
  type ChatMessage,
  createChatMessage,
  dropEmptyAssistant,
} from "@/lib/chat-messages";
import { consumeChatStream } from "@/lib/consume-chat-stream";

export type ChatView = {
  messages: ChatMessage[];
  draft: string;
  setDraft: (value: string) => void;
  busy: boolean;
  error: string | null;
  logRef: RefObject<HTMLUListElement | null>;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
};

export function useChat(): ChatView {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const logRef = useRef<HTMLUListElement | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  useEffect(() => {
    const node = logRef.current;
    if (node === null || messages.length === 0) {
      return;
    }
    node.scrollTo?.({ top: node.scrollHeight });
  }, [messages]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const message = draft.trim();
    if (!message || busy) {
      return;
    }

    setDraft("");
    setError(null);
    setBusy(true);
    setMessages((current) => [
      ...current,
      createChatMessage("user", message),
      createChatMessage("assistant", ""),
    ]);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
      await consumeChatStream(response, (piece) => {
        setMessages((current) => appendAssistantText(current, piece));
      });
    } catch (caught: unknown) {
      if (controller.signal.aborted) {
        return;
      }
      setError(caught instanceof Error ? caught.message : "Unknown error");
      setMessages((current) => dropEmptyAssistant(current));
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
      setBusy(false);
    }
  }

  return { messages, draft, setDraft, busy, error, logRef, handleSubmit };
}
