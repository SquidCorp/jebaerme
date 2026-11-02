# web

Next.js App Router frontend. Call Python only through Route Handlers under `app/api/`.

```bash
pnpm install
cp .env.example .env
pnpm dev
```

Quality gates: `pnpm lint` (Biome), `pnpm typecheck`, `pnpm test` (Vitest), `pnpm build`.

UI pattern (see root `AGENTS.md`): hooks + component composition. No HOCs. Each component TSX has a sibling `*.module.scss`.
