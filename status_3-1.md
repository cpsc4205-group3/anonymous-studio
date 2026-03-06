## Anonymous Studio — Current State Summary

## Checkpoint (2026-03-05): Auth0 Backend Integration

### Where we are now
- Added optional direct Auth0 JWT validation for `rest_main.py` via Flask `before_request` hook.
- Kept local development flow unchanged: auth is disabled unless `ANON_AUTH_ENABLED=1`.
- Added scope support (`ANON_AUTH_REQUIRED_SCOPES`) and path exemptions (`ANON_AUTH_EXEMPT_PATHS`, `ANON_AUTH_EXEMPT_PREFIXES`).
- Added focused tests for token/header/scope/exempt-path behavior.
- Updated docs and env template for setup and ops handoff.

### Files added
- `services/auth0_rest.py`
- `tests/test_auth0_rest.py`

### Files updated
- `rest_main.py`
- `.env.example`
- `README.md`
- `docs/security.md`
- `requirements.txt` (adds `PyJWT>=2.8.0,<3`)

### Validation status
- Test command: `pytest -q tests/test_auth0_rest.py`
- Result: `5 passed`

### Important implementation note (Taipy compatibility)
- Taipy Community REST does not expose a first-class auth middleware API.
- Integration uses `Rest()._app` (Flask app) before `tp.run()`, which is compatible with current Taipy runtime behavior.

### Remaining follow-ups (if we continue this track)
- Decide whether GUI (`main.py`) should also enforce token/session auth, or remain behind reverse proxy only.
- Decide if `/healthz` (or other paths) should be exempt in production.
- Add an integration smoke test with a real Auth0 tenant token if environment secrets are available.

### Project Overview
A Taipy 4.x GUI application for PII detection and anonymization using Microsoft Presidio + spaCy. Six pages: Dashboard, PII Text, Upload & Jobs, Pipeline (Kanban), Schedule, Audit Log.

---

### Tech Stack
| Layer | Technology |
|---|---|
| UI Framework | Taipy GUI 4.x (Markdown controls, WebSocket state) |
| PII Engine | Microsoft Presidio (analyzer + anonymizer) |
| NLP Model | spaCy `en_core_web_lg` (blank fallback if not installed) |
| Orchestrator | Taipy Core (DataNodes, Scenarios, background jobs) |
| Data Store | In-memory Python ([store.py](cci:7://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:0:0-0:0)) |
| File Support | CSV, Excel (.xlsx/.xls) via pandas + openpyxl |

---

### Pages & Status

**Dashboard** — ✅ Working
- 6 stat cards (Jobs Submitted, Running, Completed, Failed, Pipeline Cards, Attested) with colored metric values
- Recent audit log table (last 4 entries)
- Upcoming reviews panel
- Full-width layout (MUI container override)

**PII Text** — ✅ Working
- Quick-scan text input with entity/operator selectors
- PII highlights rendered via [highlight_md()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/pii_engine.py:296:0-317:25) using `mode=md` text control (replaced broken `raw=True` HTML approach)
- Entity table, summary count, anonymized output — all rendering

**Upload & Jobs** — ✅ Working
- CSV/Excel upload via `file_selector` — bytes cached in module-level `_FILE_CACHE` dict (bypasses Taipy JSON state serialization which converts bytes→str)
- Background job submission via `invoke_long_callback` → Taipy Orchestrator
- Job progress table, NLP model status banner

**Pipeline (Kanban)** — ✅ Working
- 4-column board: Backlog / In Progress / Review / Done
- Card forward/back with null-safe guard + `ValueError` catch on invalid `status`
- Attestation dialog (single audit entry — duplicate log removed)
- Correct Taipy scenario ID linked to card in [_bg_job_done](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:460:0-469:66) (was previously set to wrong UUID)

**Schedule** — ✅ Renders correctly
- Appointment table with add/edit/delete

**Audit Log** — ✅ Working
- Filterable by severity
- All actions logged (job.submit, pipeline.move, compliance.attest, app.start)

---

### Bugs Fixed This Session

| # | Bug | Root Cause | Fix |
|---|---|---|---|
| 1 | [store.stats()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:219:4-242:9) TypeError | `dict_keys * 0` is invalid | Removed dead line, fixed loop indentation |
| 2 | `on_card_forward/back` crash | No null check on [store.get_card()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:146:4-147:39) result; `ValueError` if bad status | Added `if not c: return` + `try/except ValueError` |
| 3 | Wrong `scenario_id` on linked card | `scenario_id` was set to the internal job UUID, not the Taipy scenario ID | [_bg_submit_job](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:449:0-457:34) now returns `(sc.id, job_id)`; [_bg_job_done](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:460:0-469:66) updates the card |
| 4 | Duplicate attestation audit entry | [on_attest_confirm](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:733:0-741:51) called [log_user_action](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:213:4-215:79) redundantly (store already logs) | Removed extra [log_user_action](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:213:4-215:79) call |
| 5 | PII highlights not rendering | `raw=True` not supported for HTML in Taipy 4.x `text` control | Implemented [highlight_md()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/pii_engine.py:296:0-317:25) in [pii_engine.py](cci:7://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/pii_engine.py:0:0-0:0), switched to `mode=md` |
| 6 | CSV upload: both fail + success alerts | Taipy's `file_selector` fires `on_action` twice (once valid, once spurious cancel) | Silent `return` when `path` is missing/invalid |
| 7 | CSV parse: "bytes-like object required, not str" | Taipy serializes state as JSON — bytes stored in state become strings | Binary file content cached in module-level `_FILE_CACHE` dict; [on_submit_job](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:455:0-518:43) falls back to bound-var bytes or path-string if cache misses |
| 8 | Jobs KPI cards parsed with warnings / broken labels | Invalid nested Taipy inline markup in Upload & Jobs KPI block | Rewrote KPI cards to valid multi-line Taipy markup (`Total Jobs`, `Running`, `Success Rate`, `Entities Found`) |
| 9 | Active Run Monitor showed conflicting text (`Active Job` + `No job running.`) | Stale client state and fallback message handling were not normalized | Normalized monitor state in `_refresh_job_health()`, removed stale fallback text path, and reset monitor when active job no longer exists |
| 10 | Runs stuck at "Queuing…" with no progress updates | In-memory progress registry may be empty/stale relative to Taipy job state | Added fallback sync in `_sync_active_job_progress()` using Taipy job status and strengthened on-init monitor refresh |
| 11 | Jobs remained queued/submitted and never executed | App launched with `gui.run()` only, so Taipy Orchestrator was not started | `run_app()` now starts GUI through `tp.run(gui, tp.Orchestrator(), ...)`; also replaced broken `tc.get_parents(job)` linkage with `job.submit_entity_id` mapping |
| 12 | Progress could disappear across process boundaries/restarts | UI relied only on in-memory `PROGRESS_REGISTRY` | Added durable snapshot writes in `tasks._progress()` and read/merge logic in app monitor/table polling (`services/progress_snapshots.py`) |
| 13 | Active Run Monitor lacked Submission lifecycle visibility | Monitor only showed job-level fields | Added submission-id tracking (`job_id -> submission_id`) and live `Active Submission` + `Submission Status` fields in Jobs monitor |
| 14 | Upload handling depended on non-doc `file_selector` payload path | Callback expected `payload.path`; Taipy docs define selected path via bound `content` value | `on_file_upload()` now reads `state.job_file_content` first (docs-aligned) with payload fallback for compatibility |
| 15 | Store auto-selected Mongo unexpectedly when `MONGODB_URI` was set | Backend selection was implicit and URI-driven only | Added explicit `ANON_STORE_BACKEND` (`memory` default, `mongo`, `auto`) so Mongo is opt-in |
| 16 | Dev hot-reload/debug required code edits | `run_kwargs` booleans were fixed in code | Added env-driven toggles (`TAIPY_USE_RELOADER`, `TAIPY_DEBUG`) while keeping defaults off |

---

### Known Remaining Items (Low Priority)

- **`store.list_appts()` / `store.upcoming_appts()`** — wrong method names called in [app.py](cci:7://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:0:0-0:0); correct names are [list_appointments()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:184:4-188:9) / [upcoming_appointments()](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:190:4-194:70). Currently masked because the refresh helpers catch exceptions silently.
- **`store` has no `get_appointment()` public method** — [on_appt_edit](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/app.py:783:0-799:31) accesses `_appointments` dict directly (internal access).
- **[update_appointment](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:169:4-176:19) / [delete_appointment](cci:1://file:///home/51nk0r5w1m/school/capstone/v2_anonymous-studio/store.py:178:4-182:20)** leave no audit trail.
- **spaCy model not installed** — running in blank-fallback mode; PERSON/LOCATION/ORG entities not detected. Fixable with `python -m spacy download en_core_web_lg`.

---

### File Structure
```
app.py          — Main Taipy GUI (state, callbacks, page markup, CSS)
pii_engine.py   — Presidio wrapper + highlight_md()
tasks.py        — run_pii_anonymization (Taipy Core task function)
store.py        — In-memory data store (PIISession, PipelineCard, Appointment, AuditEntry)
core_config.py  — Programmatic Taipy Core configuration (DataNodes, Scenarios)
config.toml     — Declarative mirror of core_config.py (for VS Code extension)
requirements.txt — Python deps (taipy, presidio, spacy, pandas, openpyxl, etc.)
```
