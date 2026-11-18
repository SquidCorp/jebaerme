import { PageHeader } from "@/app/page-header";
import { NewKnowledge } from "./new-knowledge";
import styles from "./page.module.scss";

export default function NewKnowledgePage() {
  return (
    <main className={styles.main}>
      <PageHeader
        title="Add knowledge"
        lede="Upload a markdown or text file into the document store"
      />
      <NewKnowledge />
    </main>
  );
}
