import { Chat } from "./chat";
import styles from "./page.module.scss";
import { PageHeader } from "./page-header";

export default function Home() {
  return (
    <main className={styles.main}>
      <PageHeader
        title="JÉRÉMY BAER"
        lede="Frontend talks to Python only through the Next.js gateway."
      />
      <Chat />
    </main>
  );
}
