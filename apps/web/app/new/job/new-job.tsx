"use client";

import { useNewJob } from "@/lib/use-new-job";
import styles from "./new-job.module.scss";

export function NewJob() {
  const { adUrl, setAdUrl, busy, error, result, handleSubmit } = useNewJob();

  return (
    <div className={styles.root}>
      <form
        className={styles.form}
        onSubmit={(event) => void handleSubmit(event)}
      >
        <div className={styles.field}>
          <label htmlFor="ad-url">Ad URL</label>
          <input
            id="ad-url"
            name="ad_url"
            type="text"
            value={adUrl}
            onChange={(event) => setAdUrl(event.target.value)}
            disabled={busy}
            autoComplete="off"
          />
        </div>
        <button type="submit" disabled={busy || adUrl.trim().length === 0}>
          {busy ? "Submitting" : "Submit"}
        </button>
      </form>
      {error ? <p className={styles.error}>{error}</p> : null}
      {result !== null ? <pre className={styles.result}>{result}</pre> : null}
    </div>
  );
}
