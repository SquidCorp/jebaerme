"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";
import { gatewayErrorMessage } from "@/lib/gateway-error";

export type NewJobView = {
  adUrl: string;
  setAdUrl: (value: string) => void;
  busy: boolean;
  error: string | null;
  result: string | null;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
};

function firecrawlMarkdown(payload: unknown): string | null {
  if (
    typeof payload !== "object" ||
    payload === null ||
    !("markdown" in payload)
  ) {
    return null;
  }
  const markdown = payload.markdown;
  if (typeof markdown !== "string" || markdown.length === 0) {
    return null;
  }
  return markdown;
}

async function postNewJob(
  url: string,
  signal: AbortSignal,
): Promise<string | null> {
  const response = await fetch("/api/jobs/new/url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ad_url: url }),
    signal,
  });
  if (!response.ok) {
    const payload: unknown = await response.json();
    throw new Error(
      gatewayErrorMessage(payload, `Gateway returned ${response.status}`),
    );
  }
  const payload: unknown = await response.json();
  return firecrawlMarkdown(payload);
}

export function useNewJob(): NewJobView {
  const [adUrl, setAdUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const url = adUrl.trim();
    if (!url || busy) {
      return;
    }

    setError(null);
    setResult(null);
    setBusy(true);
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      setResult(await postNewJob(url, controller.signal));
    } catch (caught: unknown) {
      if (controller.signal.aborted) {
        return;
      }
      setError(caught instanceof Error ? caught.message : "Unknown error");
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
      setBusy(false);
    }
  }

  return { adUrl, setAdUrl, busy, error, result, handleSubmit };
}
