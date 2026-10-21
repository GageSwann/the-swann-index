# TSI web

The public, read-only dashboard for The Swann Index: rankings, matchup board, game
center and team pages. It renders what the TSI API returns and never calculates odds
or ratings itself (doc 02).

Stack: Next.js 16 (App Router, Turbopack, Cache Components), TypeScript (strict),
Tailwind CSS 4, shadcn/ui (Base UI, `base-nova`), Recharts, TanStack Table.

## Run locally

```powershell
cd backend; uv run tsi serve      # the API on http://127.0.0.1:8000
cd web; npm install; npm run dev  # the site on http://localhost:3000
```

Copy `.env.example` to `.env.local` first. `TSI_API_URL` points at the API.
`REVALIDATE_TOKEN` is server-only: never prefix a secret with `NEXT_PUBLIC_`.

## Scripts

| Command          | What it does                    |
| ---------------- | ------------------------------- |
| `npm run dev`    | dev server                      |
| `npm run build`  | production build                |
| `npm run check`  | typecheck + lint + format check |
| `npm run format` | format everything with Prettier |

## Layout

- `app/`: routes only; files stay thin (fetch and compose).
- `components/<area>/`: one component per file; `components/ui/` is shadcn/ui.
- `lib/api/`: typed API client (types generated from `docs/api/openapi.json`).
- `lib/format/`: formatting helpers.

Before writing Next.js code, read the version-matched docs in
`node_modules/next/dist/docs/` (see `AGENTS.md`): this Next.js differs from older
versions.
