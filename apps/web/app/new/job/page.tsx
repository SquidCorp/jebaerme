import { PageHeader } from "@/app/page-header";
import { NewJob } from "./new-job";
import styles from "./page.module.scss";

export default function NewJobPage() {
  return (
    <main className={styles.main}>
      <PageHeader
        title="Add a new job description"
        lede="Paste a link to a job ad and get a clean markdown version"
      />
      <NewJob />
    </main>
  );
}
