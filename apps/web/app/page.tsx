import { Suspense } from "react";
import { Chat } from "./chat";
import { InviteGate } from "./invite-gate";
import styles from "./page.module.scss";
import { PageHeader } from "./page-header";

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <Suspense>
      <InviteGate searchParams={searchParams}>
        <main className={styles.main}>
          <PageHeader title="JÉRÉMY BAER" lede="Chat with my virtual clone." />
          <Chat />
        </main>
      </InviteGate>
    </Suspense>
  );
}
