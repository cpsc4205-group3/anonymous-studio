# Agent Notes (Project-wide)

## Taipy Auto-Refresh

- Taipy CLI supports auto-refresh:
  - `--use-reloader` / `--no-reloader`
  - `--debug` / `--no-debug`
- In this repo, `app.py` maps runtime behavior to env vars:
  - `ANON_GUI_USE_RELOADER=1` -> enables reloader (preferred)
  - `ANON_GUI_DEBUG=1` -> enables debug (preferred)
  - Backward-compatible aliases: `TAIPY_USE_RELOADER`, `TAIPY_DEBUG`
- Defaults are off (`0`), so code changes require restart unless those vars are enabled.

For dev sessions, prefer running with reloader/debug enabled.
