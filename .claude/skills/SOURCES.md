# Skill sources

Log of third-party skills installed in `.claude/skills/`. Policy: [docs/09-conventions.md](../../docs/09-conventions.md) §5.
Read each skill's `SKILL.md` and scripts before installing. Vendored skills stay byte-identical to the reviewed commit: the formatting hooks skip `.claude/skills/` and `.gitattributes` turns off line-ending conversion here.

| Skill | Source repo | Commit / version | Installed | Phase | Reviewed by |
|---|---|---|---|---|---|
| `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills) `skills/frontend-design` | `dbd4588f9e10` | 2026-10-21 | 5 | Claude (full read: guidance only, no scripts) |
| `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills) `skills/webapp-testing` | `dbd4588f9e10` | 2026-10-21 | 5 | Claude (full read incl. `scripts/with_server.py`: starts the commands you pass, polls a localhost port, runs your command, stops the servers; no network; examples write to Linux paths) |
| `react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) `skills/react-best-practices` (MIT) | `063bee94c3f4` | 2026-10-21 | 5 | Claude (SKILL.md read; 76 Markdown/JSON files scanned: no scripts; only example commands and reference links). Replaces the planned `nextjs` skill, which no longer exists (#66) |

Reviewed and **not** installed: `next-dev-loop` ([vercel/next.js](https://github.com/vercel/next.js) `skills/`, `72895219d44d`): needs a globally installed third-party browser CLI (`agent-browser`) with persistent sessions and refuses to run below Next.js 16.3 + Turbopack; overlaps `webapp-testing` (#66).
