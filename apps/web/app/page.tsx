import { Chat } from "./chat";
import { HealthStatus } from "./health-status";
import { HelloStatus } from "./hello-status";

export default function Home() {
  return (
    <main>
      <header>
        <h1>
          <span className="prompt" aria-hidden="true">
            &gt;
          </span>
          JÉRÉMY BAER
        </h1>
        <p className="lede">Frontend talks to Python only through the Next.js gateway.</p>
      </header>
      <Chat />
      <HealthStatus />
      <HelloStatus />
    </main>
  );
}
