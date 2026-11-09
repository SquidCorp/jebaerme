import Image from "next/image";
import styles from "./access-denied.module.scss";

export function AccessDenied() {
  return (
    <main className={styles.root} aria-labelledby="access-denied-heading">
      <div className={styles.inner}>
        <Image
          className={styles.face}
          src="/assets/grimacing_face.png"
          alt=""
          width={360}
          height={360}
        />
        <div className={styles.message}>
          <h1 id="access-denied-heading" className={styles.title}>
            <span className={styles.visuallyHidden}>403 Unauthorized. </span>
            <span className={styles.prompt} aria-hidden="true">
              &gt;
            </span>
            Ouch !
          </h1>
          <p className={styles.copy}>
            This clone is invite-only.
            <br />
            Open the invitation link you were sent.
          </p>
        </div>
      </div>
    </main>
  );
}
