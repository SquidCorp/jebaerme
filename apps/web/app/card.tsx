import type { ReactNode } from "react";
import styles from "./card.module.scss";

type CardProps = {
  title: string;
  headingId: string;
  children: ReactNode;
  className?: string;
};

export function Card({ title, headingId, children, className }: CardProps) {
  const names = [styles.card, className].filter(
    (name): name is string => name !== undefined && name !== "",
  );
  return (
    <section className={names.join(" ")} aria-labelledby={headingId}>
      <h2 id={headingId}>{title}</h2>
      {children}
    </section>
  );
}
