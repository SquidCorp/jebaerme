"use client";

import { Card } from "@/app/card";
import { useChat } from "@/lib/use-chat";
import styles from "./chat.module.scss";

export function Chat() {
  const { messages, draft, setDraft, busy, error, logRef, handleSubmit } =
    useChat();

  return (
    <Card title="CHAT" headingId="chat-heading" className={styles.root}>
      <ul ref={logRef} className={styles.log} aria-live="polite">
        {messages.length === 0 ? (
          <li className={styles.empty}>Ask the model something.</li>
        ) : (
          messages.map((entry) => (
            <li key={entry.id}>
              <span className={styles.role}>
                {entry.role === "user" ? "YOU" : "MODEL"}
              </span>
              <p className={styles.bubble}>{entry.text || (busy ? "…" : "")}</p>
            </li>
          ))
        )}
      </ul>
      {error ? <p className={styles.error}>{error}</p> : null}
      <form
        className={styles.form}
        onSubmit={(event) => void handleSubmit(event)}
      >
        <label className={styles.visuallyHidden} htmlFor="chat-message">
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
    </Card>
  );
}
