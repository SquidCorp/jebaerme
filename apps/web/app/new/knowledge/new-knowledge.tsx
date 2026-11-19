"use client";

import type { ReactNode } from "react";
import type { DocumentDomain, NewKnowledgeView } from "@/lib/use-new-knowledge";
import { useNewKnowledge } from "@/lib/use-new-knowledge";
import styles from "./new-knowledge.module.scss";

const SOURCES = ["cv", "projects", "experiences", "eval_reports"] as const;
const DOMAINS = ["business", "technical", "general"] as const;

function Field({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      {children}
    </div>
  );
}

function KnowledgeFields({
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
  onFileChange,
  busy,
}: NewKnowledgeView) {
  return (
    <>
      <Field id="knowledge-file" label="File">
        <input
          id="knowledge-file"
          name="file"
          type="file"
          accept=".md,.txt,text/markdown,text/plain"
          onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          disabled={busy}
        />
      </Field>
      <Field id="knowledge-title" label="Title">
        <input
          id="knowledge-title"
          name="title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          disabled={busy}
          autoComplete="off"
        />
      </Field>
      <Field id="knowledge-source" label="Source">
        <select
          id="knowledge-source"
          name="source"
          value={source}
          onChange={(event) => setSource(event.target.value)}
          disabled={busy}
        >
          <option value="">Select source</option>
          {SOURCES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </Field>
      <Field id="knowledge-domain" label="Domain">
        <select
          id="knowledge-domain"
          name="domain"
          value={domain}
          onChange={(event) => {
            const value = event.target.value;
            if (DOMAINS.includes(value as DocumentDomain)) {
              setDomain(value as DocumentDomain);
            }
          }}
          disabled={busy}
        >
          {DOMAINS.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </Field>
      <Field id="knowledge-language" label="Language">
        <input
          id="knowledge-language"
          name="language"
          type="text"
          value={language}
          onChange={(event) => setLanguage(event.target.value)}
          disabled={busy}
          autoComplete="off"
        />
      </Field>
      <Field id="knowledge-roles" label="Roles">
        <input
          id="knowledge-roles"
          name="roles"
          type="text"
          value={roles}
          onChange={(event) => setRoles(event.target.value)}
          disabled={busy}
          placeholder="Staff Engineer, Tech Lead"
          autoComplete="off"
        />
      </Field>
    </>
  );
}

export function NewKnowledge() {
  const view = useNewKnowledge();
  const { file, busy, title, source, language, handleSubmit, error, result } =
    view;

  return (
    <div className={styles.root}>
      <form
        className={styles.form}
        onSubmit={(event) => void handleSubmit(event)}
      >
        <KnowledgeFields {...view} />
        <button
          type="submit"
          disabled={
            busy ||
            file === null ||
            title.trim().length === 0 ||
            source === "" ||
            language.trim().length === 0
          }
        >
          {busy ? "Submitting" : "Submit"}
        </button>
      </form>
      {error ? <p className={styles.error}>{error}</p> : null}
      {result !== null ? <pre className={styles.result}>{result}</pre> : null}
    </div>
  );
}
