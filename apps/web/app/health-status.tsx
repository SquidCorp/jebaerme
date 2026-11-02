"use client";

import { useEffect, useState } from "react";
import { Card } from "@/app/card";
import { gatewayErrorMessage } from "@/lib/gateway-error";
import styles from "./health-status.module.scss";

type Health = {
  status: string;
  env: string;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error"; message: string };

export function HealthStatus() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    void fetch("/api/health", { signal: controller.signal })
      .then(async (response) => {
        const payload: unknown = await response.json();
        if (!response.ok) {
          throw new Error(
            gatewayErrorMessage(payload, `Gateway returned ${response.status}`),
          );
        }
        if (!isHealth(payload)) {
          throw new Error("Gateway returned an unexpected payload");
        }
        setState({ kind: "ok", health: payload });
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
      <Card title="HEALTH" headingId="health-heading">
        <p className={styles.message}>Checking health…</p>
      </Card>
    );
  }

  if (state.kind === "error") {
    return (
      <Card title="HEALTH" headingId="health-heading">
        <p className={styles.error}>{state.message}</p>
      </Card>
    );
  }

  return (
    <Card title="HEALTH" headingId="health-heading">
      <dl className={styles.list}>
        <div>
          <dt>STATUS</dt>
          <dd className={styles.ok}>{state.health.status}</dd>
        </div>
        <div>
          <dt>ENV</dt>
          <dd>{state.health.env}</dd>
        </div>
      </dl>
    </Card>
  );
}

function isHealth(value: unknown): value is Health {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  if (!("status" in value) || !("env" in value)) {
    return false;
  }
  return typeof value.status === "string" && typeof value.env === "string";
}
