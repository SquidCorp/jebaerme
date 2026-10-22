"use client";

import { useEffect, useState } from "react";

type Hello = {
  status: string;
  text: string;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; hello: Hello }
  | { kind: "error"; message: string };

export function HelloStatus() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    void fetch("/api/hello", { signal: controller.signal })
      .then(async (response) => {
        const payload: unknown = await response.json();
        if (!response.ok) {
          throw new Error(errorMessage(payload, `Gateway returned ${response.status}`));
        }
        if (!isHello(payload)) {
          throw new Error("Gateway returned an unexpected payload");
        }
        setState({ kind: "ok", hello: payload });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) {
          return;
        }
        const message = error instanceof Error ? error.message : "Unknown error";
        setState({ kind: "error", message });
      });

    return () => controller.abort();
  }, []);

  if (state.kind === "loading") {
    return (
      <section className="card" aria-labelledby="hello-heading">
        <h2 id="hello-heading">HELLO</h2>
        <p>Asking the model…</p>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="card" aria-labelledby="hello-heading">
        <h2 id="hello-heading">HELLO</h2>
        <p className="status-error">{state.message}</p>
      </section>
    );
  }

  return (
    <section className="card" aria-labelledby="hello-heading">
      <h2 id="hello-heading">HELLO</h2>
      <dl>
        <div>
          <dt>STATUS</dt>
          <dd className="status-ok">{state.hello.status}</dd>
        </div>
        <div>
          <dt>TEXT</dt>
          <dd>{state.hello.text}</dd>
        </div>
      </dl>
    </section>
  );
}

function isHello(value: unknown): value is Hello {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  if (!("status" in value) || !("text" in value)) {
    return false;
  }
  return typeof value.status === "string" && typeof value.text === "string";
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
