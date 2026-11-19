"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";
import { gatewayErrorMessage } from "@/lib/gateway-error";

export type DocumentDomain = "business" | "technical" | "general";
export type DocumentSource = "cv" | "projects" | "experiences" | "eval_reports";

export type NewKnowledgeView = {
  title: string;
  setTitle: (value: string) => void;
  source: string;
  setSource: (value: string) => void;
  domain: DocumentDomain;
  setDomain: (value: DocumentDomain) => void;
  language: string;
  setLanguage: (value: string) => void;
  roles: string;
  setRoles: (value: string) => void;
  file: File | null;
  onFileChange: (file: File | null) => void;
  busy: boolean;
  error: string | null;
  result: string | null;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
};

type SubmitFields = {
  title: string;
  source: string;
  domain: DocumentDomain;
  language: string;
  roles: string;
  file: File | null;
  busy: boolean;
};

type SubmitSetters = {
  setError: (value: string | null) => void;
  setResult: (value: string | null) => void;
  setBusy: (value: boolean) => void;
};

type KnowledgeIngestBody = {
  title: string;
  text: string;
  source: DocumentSource;
  source_kind: "file";
  domain: DocumentDomain;
  language: string;
  roles: string[];
  source_ids: string[];
};

function isTextDocument(name: string): boolean {
  const lower = name.toLowerCase();
  return lower.endsWith(".md") || lower.endsWith(".txt");
}

function basename(name: string): string | null {
  const segments = name.split(/[/\\]/);
  const last = segments[segments.length - 1] ?? "";
  if (
    last.length === 0 ||
    name.includes("\\") ||
    name.startsWith("/") ||
    name.split("/").includes("..")
  ) {
    return null;
  }
  return last;
}

function titleFromFilename(name: string): string | null {
  const fileName = basename(name);
  if (fileName === null) {
    return null;
  }
  const lower = fileName.toLowerCase();
  let stem = fileName;
  if (lower.endsWith(".md")) {
    stem = fileName.slice(0, -3);
  } else if (lower.endsWith(".txt")) {
    stem = fileName.slice(0, -4);
  }
  const trimmed = stem.trim();
  return trimmed.length === 0 ? null : trimmed;
}

function splitRoles(value: string): string[] {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

function isSource(value: string): value is DocumentSource {
  return (
    value === "cv" ||
    value === "projects" ||
    value === "experiences" ||
    value === "eval_reports"
  );
}

function ingestSummary(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null) {
    return null;
  }
  if (
    !("document_id" in payload) ||
    !("chunk_count" in payload) ||
    !("skipped_chunks" in payload)
  ) {
    return null;
  }
  if (
    typeof payload.document_id !== "string" ||
    typeof payload.chunk_count !== "number" ||
    typeof payload.skipped_chunks !== "number"
  ) {
    return null;
  }
  return [
    `document_id: ${payload.document_id}`,
    `chunk_count: ${payload.chunk_count}`,
    `skipped_chunks: ${payload.skipped_chunks}`,
  ].join("\n");
}

function applyChosenFile(
  next: File | null,
  setFile: (file: File | null) => void,
  setError: (error: string | null) => void,
  setTitle: (title: string) => void,
): void {
  if (next === null) {
    setFile(null);
    return;
  }
  if (!isTextDocument(next.name)) {
    setError("Choose a .md or .txt file");
    setFile(null);
    return;
  }
  setFile(next);
  setError(null);
  const prefill = titleFromFilename(next.name);
  if (prefill !== null) {
    setTitle(prefill);
  }
}

async function postDocuments(
  body: KnowledgeIngestBody,
  signal: AbortSignal,
): Promise<string> {
  const response = await fetch("/api/documents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const payload: unknown = await response.json();
    throw new Error(
      gatewayErrorMessage(payload, `Gateway returned ${response.status}`),
    );
  }
  const payload: unknown = await response.json();
  const summary = ingestSummary(payload);
  if (summary === null) {
    throw new Error("Gateway returned an unexpected payload");
  }
  return summary;
}

async function runSubmit(
  event: FormEvent<HTMLFormElement>,
  fields: SubmitFields,
  setters: SubmitSetters,
  controllerRef: { current: AbortController | null },
): Promise<void> {
  event.preventDefault();
  const { title, source, domain, language, roles, file, busy } = fields;
  if (
    busy ||
    file === null ||
    title.trim().length === 0 ||
    !isSource(source) ||
    language.trim().length === 0
  ) {
    return;
  }
  const filename = basename(file.name);
  if (filename === null) {
    setters.setError("File name is not a relative POSIX path");
    return;
  }

  setters.setError(null);
  setters.setResult(null);
  setters.setBusy(true);
  const controller = new AbortController();
  controllerRef.current = controller;

  try {
    const text = (await file.text()).trim();
    if (text.length === 0) {
      setters.setError("File is empty");
      return;
    }
    setters.setResult(
      await postDocuments(
        {
          title: title.trim(),
          text,
          source,
          source_kind: "file",
          domain,
          language: language.trim(),
          roles: splitRoles(roles),
          source_ids: [filename],
        },
        controller.signal,
      ),
    );
  } catch (caught: unknown) {
    if (controller.signal.aborted) {
      return;
    }
    setters.setError(
      caught instanceof Error ? caught.message : "Unknown error",
    );
  } finally {
    if (controllerRef.current === controller) {
      controllerRef.current = null;
    }
    setters.setBusy(false);
  }
}

export function useNewKnowledge(): NewKnowledgeView {
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("");
  const [domain, setDomain] = useState<DocumentDomain>("general");
  const [language, setLanguage] = useState("en");
  const [roles, setRoles] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  return {
    title,
    setTitle,
    source,
    setSource,
    domain,
    setDomain,
    language,
    setLanguage,
    roles,
    setRoles,
    file,
    onFileChange: (next) => applyChosenFile(next, setFile, setError, setTitle),
    busy,
    error,
    result,
    handleSubmit: (event) =>
      runSubmit(
        event,
        { title, source, domain, language, roles, file, busy },
        { setError, setResult, setBusy },
        controllerRef,
      ),
  };
}
