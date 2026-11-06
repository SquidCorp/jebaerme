"use client";

import {
  type ChangeEvent,
  type FormEvent,
  type KeyboardEvent,
  useEffect,
  useRef,
} from "react";
import type { ChatMessage } from "@/lib/chat-messages";
import { useChat } from "@/lib/use-chat";
import styles from "./chat.module.scss";

export function Chat() {
  const { messages, draft, setDraft, busy, error, logRef, handleSubmit } =
    useChat();

  return (
    <section className={styles.root} aria-labelledby="chat-heading">
      <h2 id="chat-heading" className={styles.visuallyHidden}>
        Chat
      </h2>
      <ul ref={logRef} className={styles.log} aria-live="polite">
        {messages.length === 0 ? (
          <li className={styles.empty}>Ask the model something.</li>
        ) : (
          messages.map((entry) => (
            <ChatBubble key={entry.id} entry={entry} busy={busy} />
          ))
        )}
      </ul>
      {error ? <p className={styles.error}>{error}</p> : null}
      <ChatComposer
        draft={draft}
        setDraft={setDraft}
        busy={busy}
        onSubmit={handleSubmit}
      />
    </section>
  );
}

type ChatBubbleProps = {
  entry: ChatMessage;
  busy: boolean;
};

function ChatBubble({ entry, busy }: ChatBubbleProps) {
  const isUser = entry.role === "user";
  return (
    <li className={isUser ? styles.user : styles.assistant}>
      <span className={styles.visuallyHidden}>{isUser ? "You" : "Model"}</span>
      <p className={styles.bubble}>{entry.text || (busy ? "…" : "")}</p>
    </li>
  );
}

type ChatComposerProps = {
  draft: string;
  setDraft: (value: string) => void;
  busy: boolean;
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
};

function resizeComposer(node: HTMLTextAreaElement) {
  node.style.height = "auto";
  node.style.height = `${node.scrollHeight}px`;
}

function ChatComposer({ draft, setDraft, busy, onSubmit }: ChatComposerProps) {
  const fieldRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const node = fieldRef.current;
    if (node === null || draft !== "") {
      return;
    }
    resizeComposer(node);
  }, [draft]);

  function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
    const node = event.target;
    setDraft(node.value);
    resizeComposer(node);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key !== "Enter" ||
      event.shiftKey ||
      event.nativeEvent.isComposing
    ) {
      return;
    }
    event.preventDefault();
    if (busy || draft.trim().length === 0) {
      return;
    }
    event.currentTarget.form?.requestSubmit();
  }

  return (
    <form className={styles.form} onSubmit={(event) => void onSubmit(event)}>
      <label className={styles.visuallyHidden} htmlFor="chat-message">
        Message
      </label>
      <textarea
        ref={fieldRef}
        id="chat-message"
        name="message"
        rows={1}
        value={draft}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Say hello…"
        autoComplete="off"
        enterKeyHint="send"
        disabled={busy}
      />
      <button type="submit" disabled={busy || draft.trim().length === 0}>
        {busy ? "Sending" : "Send"}
      </button>
    </form>
  );
}
