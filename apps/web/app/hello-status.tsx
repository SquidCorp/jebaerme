"use client";

import { useEffect, useState } from "react";
import { Card } from "@/app/card";
import { gatewayErrorMessage } from "@/lib/gateway-error";
import styles from "./hello-status.module.scss";

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
          throw new Error(
            gatewayErrorMessage(payload, `Gateway returned ${response.status}`),
          );
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
        const message =
          error instanceof Error ? error.message : "Unknown error";
        setState({ kind: "error", message });
      });

    return () => controller.abort();
  }, []);

  if (state.kind === "loading") {
    return (
      <Card title="HELLO" headingId="hello-heading">
        <p className={styles.message}>Asking the model…</p>
      </Card>
    );
  }

  if (state.kind === "error") {
    return (
      <Card title="HELLO" headingId="hello-heading">
        <p className={styles.error}>{state.message}</p>
      </Card>
    );
  }

  return (
    <Card title="HELLO" headingId="hello-heading">
      <dl className={styles.list}>
        <div>
          <dt>STATUS</dt>
          <dd className={styles.ok}>{state.hello.status}</dd>
        </div>
        <div>
          <dt>TEXT</dt>
          <dd>{state.hello.text}</dd>
        </div>
      </dl>
    </Card>
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
