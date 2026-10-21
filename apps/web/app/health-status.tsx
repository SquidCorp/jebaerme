"use client";

import { useEffect, useState } from "react";

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
          throw new Error(errorMessage(payload, `Gateway returned ${response.status}`));
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
        const message = error instanceof Error ? error.message : "Unknown error";
        setState({ kind: "error", message });
      });

    return () => controller.abort();
  }, []);

  if (state.kind === "loading") {
    return (
      <section className="card" aria-labelledby="health-heading">
        <h2 id="health-heading">HEALTH</h2>
        <p>Checking health…</p>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="card" aria-labelledby="health-heading">
        <h2 id="health-heading">HEALTH</h2>
        <p className="status-error">{state.message}</p>
      </section>
    );
  }

  return (
    <section className="card" aria-labelledby="health-heading">
      <h2 id="health-heading">HEALTH</h2>
      <dl>
        <div>
          <dt>STATUS</dt>
          <dd className="status-ok">{state.health.status}</dd>
        </div>
        <div>
          <dt>ENV</dt>
          <dd>{state.health.env}</dd>
        </div>
      </dl>
    </section>
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

function errorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === "object" && payload !== null && "error" in payload) {
    const error = payload.error;
    if (typeof error === "string") {
      return error;
    }
  }
  return fallback;
}
