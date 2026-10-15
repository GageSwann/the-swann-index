# 08 – Windows Setup (Phase 0)

Run these in PowerShell. **Close and reopen VS Code after installing**, so the new PATH entries are picked up.

## 1. Install tools
Git is already installed. Node.js and the GitHub CLI install machine-wide, so accept the Windows admin (UAC) prompt.
```powershell
winget install --id OpenJS.NodeJS.LTS -e
winget install --id astral-sh.uv -e
winget install --id GitHub.cli -e
```
Then let **uv manage Python**. This avoids the Store alias and PATH conflicts, and the backend pins 3.12 in `pyproject.toml`:
```powershell
uv python install 3.12
uv tool install pre-commit     # git hooks (ruff, gitleaks)
```

> Python packages (pandas, FastAPI, SQLAlchemy…) are **not** installed globally. `uv sync` installs them into `backend/.venv` when the backend is scaffolded in Phase 1. Web packages install with `npm install` inside `web/` in Phase 5.

If `python` opens the Microsoft Store, turn off the alias: Settings → Apps → Advanced app settings → App execution aliases → switch off `python.exe` and `python3.exe`. Inside the project, prefer `uv run python`.

## 2. Verify
```powershell
git --version; node --version; npm --version; uv --version; uv python list --only-installed; gh --version; pre-commit --version
```

## 3. Configure Git
Use your GitHub **noreply** email so your personal email isn't published in commit history. You can find it under GitHub → Settings → Emails (it looks like `12345678+username@users.noreply.github.com`).
```powershell
git config --global user.name "Your Name"
git config --global user.email "ID+username@users.noreply.github.com"
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

## 4. Connect to GitHub
```powershell
gh auth login      # GitHub.com → HTTPS → login with browser
gh auth status
```

## 5. Create the repo and push the docs
From the project folder, **after** `.gitignore` and the pre-commit config exist:
```powershell
git init
pre-commit install
git add .
git commit -m "docs: initial TSI planning documents"
gh repo create the-swann-index --public --source . --remote origin --push
```

## 6. Accounts & keys
- **CFBD:** request a key at https://collegefootballdata.com/key → `CFBD_API_KEY`
- **Neon:** create a free project at https://neon.tech, add a `dev` branch → `DATABASE_URL` (use the dev branch locally)
- Copy `backend/.env.example` → `backend/.env` and paste the values there. `.env` is gitignored; **never** paste keys into code, docs, or chat logs.
- If a key is ever committed or pasted somewhere public, **rotate it** (CFBD: request a new key; Neon: reset the role password).
- Later (Phase 6): Vercel and Render/Fly accounts, both signed in with GitHub.

## 7. VS Code extensions
- Python, Pylance, Ruff
- ESLint, Prettier, Tailwind CSS IntelliSense
- GitHub Pull Requests (optional), GitLens (optional)

## 8. Claude Code skills
Installed per phase, not now. See [09-conventions.md](09-conventions.md) §5 for the list and the review-before-install rule.
