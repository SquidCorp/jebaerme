# Web contract

- App Router + TypeScript. Styles in Sass (`.scss`), not Tailwind.
- Each presentational component TSX has a sibling CSS module (`chat.tsx` + `chat.module.scss`) and imports it. Do not add component rules to a shared dump file.
- `globals.scss` is tokens, reset, and fonts only (`:root`, `html`/`body`). Layout may import it. Hooks, route handlers, and tests have no stylesheets.
- Browser calls Next.js only. Python is reached through Route Handlers under `app/api/` (Node gateway). Do not call the Python origin from client code.
- Gateway handlers proxy/map errors. No business rules there.
- Package manager is pnpm. Do not add npm/yarn lockfiles.
- Lint/format with Biome only (no ESLint). Caps: cognitive complexity 15, 80 lines/function, 4 params.
- Named exports by default. Default exports only for App Router `page`/`layout` files and `*.config.ts`.
- No barrel files and no `export *`. No `any`. TypeScript `noUncheckedIndexedAccess` is on.
- Colocate unit tests as `*.test.ts` / `*.test.tsx`. Use Vitest + Testing Library. No network, no secrets.
- React UI is hooks + composition only. No HOCs (`withX(Component)`), no class components, no inheritance.
- Split stateful UI into a `use*` hook (state, effects, fetch) and presentational components (JSX, props, `children`). Hooks must not return JSX. Presentational components must not call `fetch` or `useState` for server data.
- `app/**/page.tsx` only composes components. No `fetch`, no `useState`, no effects in pages.
- Prefer `children` / small composed components over one component with a large props surface. Repeat markup becomes a component.

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.
