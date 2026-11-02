import { Chat } from "./chat";
import { HealthStatus } from "./health-status";
import { HelloStatus } from "./hello-status";
import styles from "./page.module.scss";

export default function Home() {
  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>
          <span className={styles.prompt} aria-hidden="true">
            &gt;
          </span>
          JÉRÉMY BAER
        </h1>
        <p className={styles.lede}>
          Frontend talks to Python only through the Next.js gateway.
        </p>
      </header>
      <Chat />
      <HealthStatus />
      <HelloStatus />
    </main>
  );
}
