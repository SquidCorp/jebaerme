"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
};

export function Chat() {
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
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [messages]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
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
      { role: "user", text: message },
      { role: "assistant", text: "" },
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
      if (!response.ok) {
        const payload: unknown = await response.json();
        throw new Error(errorMessage(payload, `Gateway returned ${response.status}`));
      }
      if (!response.body) {
        throw new Error("Gateway returned an empty stream");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        const piece = done ? decoder.decode() : decoder.decode(value, { stream: true });
        if (piece) {
          setMessages((current) => appendAssistantText(current, piece));
        }
        if (done) {
          break;
        }
      }
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

  return (
    <section className="card chat" aria-labelledby="chat-heading">
      <h2 id="chat-heading">CHAT</h2>
      <ul ref={logRef} className="chat-log" aria-live="polite">
        {messages.length === 0 ? (
          <li className="chat-empty">Ask the model something.</li>
        ) : (
          messages.map((entry, index) => (
            <li key={`${entry.role}-${index}`}>
              <span className="chat-role">{entry.role === "user" ? "YOU" : "MODEL"}</span>
              <p className="chat-bubble">{entry.text || (busy ? "…" : "")}</p>
            </li>
          ))
        )}
      </ul>
      {error ? <p className="status-error">{error}</p> : null}
      <form className="chat-form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="visually-hidden" htmlFor="chat-message">
          Message
        </label>
        <input
          id="chat-message"
          name="message"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Say hello…"
          autoComplete="off"
          disabled={busy}
        />
        <button type="submit" disabled={busy || draft.trim().length === 0}>
          {busy ? "Sending" : "Send"}
        </button>
      </form>
    </section>
  );
}

function appendAssistantText(messages: ChatMessage[], piece: string): ChatMessage[] {
  if (messages.length === 0) {
    return messages;
  }
  const next = [...messages];
  const last = next[next.length - 1];
  if (last === undefined || last.role !== "assistant") {
    return messages;
  }
  next[next.length - 1] = { role: "assistant", text: last.text + piece };
  return next;
}

function dropEmptyAssistant(messages: ChatMessage[]): ChatMessage[] {
  const last = messages[messages.length - 1];
  if (last?.role === "assistant" && last.text === "") {
    return messages.slice(0, -1);
  }
  return messages;
}

function errorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "error" in payload) {
    const error = payload.error;
    if (typeof error === "string") {
      return error;
    }
  }
  return fallback;
}
