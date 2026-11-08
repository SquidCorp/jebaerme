import styles from "./page-header.module.scss";

type PageHeaderProps = {
  title: string;
  lede: string;
};

export function PageHeader({ title, lede }: PageHeaderProps) {
  return (
    <header className={styles.header}>
      <h1 className={styles.title}>
        <span className={styles.prompt} aria-hidden="true">
          &gt;
        </span>
        {title}
      </h1>
      <p className={styles.lede}>{lede}</p>
    </header>
  );
}
