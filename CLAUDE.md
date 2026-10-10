# CLAUDE.md

Start every session by reading [context.md](context.md), then [progress.md](progress.md). For product rules read [docs/SRS.md](docs/SRS.md) — it wins over everything else.

Keep the context current so a new session never starts cold:

- Before ending a session (or after any meaningful change), update `context.md` → **Status**, **Open questions**, and add a line to **Session log**.
- Tick items in `progress.md` as they land.
- New team decisions go in `context.md` until the team moves them into `docs/PROJECT.md`. Don't silently edit `docs/SRS.md`; it's the signed spec.

Ground rules: respect the README owners table, never commit `.env` or API keys, no silent fixture fallback that fakes a live call, no thresholds outside `src/news.py` / `src/decide.py`.
