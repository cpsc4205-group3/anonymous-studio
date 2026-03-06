# Anonymous Studio Repo Assessment and UI-Aligned Enhancement Plan

Date: 2026-03-05  
Scope: Current repository at `v2_anonymous-studio` (Taipy GUI + Taipy Core + Mongo/Memory store + Presidio anonymization)

## 1. Executive summary

The current repo is strong on core workflow coverage and has recently improved large-dataset plumbing and Mongo DataNode support. The app is feature-complete for the intended operator flow:

1. Analyze text
2. Submit batch jobs
3. Monitor runs
4. Move cards through pipeline
5. Schedule reviews
6. Audit decisions

The biggest remaining gap is not missing UI components; it is operational robustness at scale:

- persistent job registry beyond process memory
- reliable standalone + Mongo worker execution under stress
- queue/backpressure and multi-user concurrency controls
- clearer job lifecycle semantics in the monitor for long-running runs

Current automated baseline is healthy (`72 passed` in local pytest), but end-to-end production-hardening should focus on orchestration reliability, not just component correctness.

## 2. What is already working well

### 2.1 UI/use-case coverage

- Dashboard, Analyze, Jobs, Pipeline, Schedule, Audit pages are cohesive and linked.
- Jobs page has actionable controls for submit, poll, cancel, remove, download.
- Pipeline integration (auto-move to review after completion) supports compliance workflow.
- Audit page includes Data Node Explorer, which is valuable for troubleshooting Taipy runtime state.

### 2.2 Taipy architecture alignment (current state)

- Uses `tp.run(gui, orchestrator, ...)`, so GUI and Core services run together.
- Uses `invoke_long_callback` for non-blocking submission UX.
- Uses scenario/task/data node patterns correctly (`tc.create_scenario`, `tc.submit`).
- Uses `figure`-based Plotly charts in multiple views (modern Taipy GUI path).
- Supports development and standalone execution modes through env-driven config.

### 2.3 Large-data direction

- Chunked task processing and progress checkpoints are in place.
- Mongo write batching for `raw_input` DataNode is implemented.
- Durable progress snapshots reduce monitor drift across process boundaries.
- Stress helper (`make stress`, task-level stress test/script) exists.

## 3. Key risks and enhancement opportunities (prioritized)

## P0 (high impact, near-term)

### P0.1 Persist job registry (replace process-only `_SCENARIOS` as source of truth)

Why:
- `_SCENARIOS` and `_SUBMISSION_IDS` are in-memory globals, so restart loses job mapping/history.
- Multi-instance deployment will diverge job visibility.

Enhancement:
- Create persistent `job_runs` collection/table keyed by `job_id`.
- Store `scenario_id`, `submission_id`, status timestamps, row totals, and cleanup state.
- Rebuild monitor and history from persistent records + Taipy status lookup.

Files touched:
- `app.py` (job lifecycle/state reconstruction)
- `store/base.py`, `store/memory.py`, `store/mongo.py` (new read/write methods)

### P0.2 Resolve standalone + Mongo task-pickling reliability

Why:
- There is an identified standalone+mongo failure path (`cannot pickle '_thread.lock' object`) in task dispatch context.
- This blocks the most production-aligned architecture.

Enhancement:
- Isolate and eliminate non-picklable objects in task inputs/config path.
- Add standalone+mongo integration test from script entrypoint (not heredoc) and gate CI on it.

Files touched:
- `core_config.py`, `tasks.py`, new integration test under `tests/`

### P0.3 Queue control and backpressure

Why:
- Users can submit arbitrarily many large jobs with no throttle.
- Under load, UI “queued/running” experience can degrade and cause resource pressure.

Enhancement:
- Add max concurrent submissions per app/user.
- Add queue depth indicator + “queued position”.
- Reject/soft-throttle with explicit message when max queued jobs is exceeded.

Files touched:
- `app.py`, `services/jobs.py`, store backend for queue metadata

### P0.4 Monitor lifecycle semantics and cancellation fidelity

Why:
- Cancellation currently maps to generic `"error"` in progress snapshot.
- Ops users need explicit terminal states (`cancelled`, `abandoned`, `skipped`) for audit/reporting.

Enhancement:
- Standardize status model across progress snapshot, job table, and run health.
- Preserve Taipy-native terminal states in UI and audit.

Files touched:
- `app.py`, `services/progress_snapshots.py`, `services/jobs.py`

## P1 (important UX/ops improvements)

### P1.1 Streaming ingestion for very large files

Why:
- `on_submit_job` parses whole file into a DataFrame first, which can become memory-heavy for large datasets.

Enhancement:
- Add optional streaming mode for CSV:
  - read in chunks
  - write chunks directly to Mongo DataNode
  - submit task once ingestion completes
- Keep current in-memory parse path for dev/small files.

Files touched:
- `services/jobs.py`, `core_config.py`, `app.py`

### P1.2 Dashboard mode-aware rendering

Why:
- `dash_report_mode` changes summary text but does not strongly recompose widgets by mode.

Enhancement:
- Explicitly switch sections by mode:
  - `Operations`: run health, throughput trends, queue depth
  - `Compliance`: attestation velocity, critical audit rates, overdue reviews
  - `Throughput`: entities/row, chunk throughput, completion latencies
  - `Overview`: blended high-level KPIs

Files touched:
- `app.py`, `pages/definitions.py`

### P1.3 Geo map enrichment

Why:
- Map currently depends on static city dictionary + text counts.
- Coverage is useful for demos but weak for real-world location diversity.

Enhancement:
- Introduce optional geocoding adapter (cached, configurable, offline fallback).
- Keep static dictionary as deterministic fallback for secure/offline environments.

Files touched:
- `app.py`, optional new `services/geo.py`

### P1.4 Retention and cleanup policy

Why:
- Progress snapshot files and old scenarios can accumulate.
- Cleanup currently occurs in user-triggered paths, not scheduled policy.

Enhancement:
- Add retention settings:
  - job metadata retention
  - scenario/data node cleanup window
  - snapshot file TTL cleanup task

Files touched:
- `core_config.py`, new maintenance module/script, `README.md`

### P1.5 Dev-mode hot reload ergonomics

Why:
- Runtime already supports env-driven toggles in `app.py`:
  - `ANON_GUI_USE_RELOADER=1` (preferred)
  - `ANON_GUI_DEBUG=1` (preferred)
  - `TAIPY_USE_RELOADER` / `TAIPY_DEBUG` (backward-compatible aliases)
- Defaults are off for stability, so restart is still required unless toggles are enabled.

Enhancement:
- Standardize developer workflow docs and `.env.example` usage around these toggles.
- Keep production default as non-reloader/non-debug.

Files touched:
- `README.md`, `AGENTS.md`, `CLAUDE.md`, `.env.example`

## P2 (quality, maintainability, product depth)

### P2.1 Split `app.py` into feature modules

Why:
- `app.py` is large and mixes state, callbacks, orchestration, and analytics logic.
- This slows safe iteration.

Enhancement:
- Split by domain:
  - `controllers/jobs.py`
  - `controllers/pipeline.py`
  - `controllers/dashboard.py`
  - `state.py` for shared state defaults/constants

### P2.2 Add UI smoke/E2E tests

Why:
- Current tests are strong in unit/integration, weaker in interactive GUI regression.

Enhancement:
- Add smoke tests for core flows:
  - upload -> submit -> monitor -> download
  - card lifecycle with selection/edit/attestation
  - schedule create/edit/delete
  - dashboard refresh sanity

### P2.3 Accessibility and operator ergonomics

Enhancement:
- Keyboard-first selection/action flow on tables.
- Status color contrast audit and color-blind-safe palette variants.
- Consistent inline validation and field-level error hints on dialogs.

## 4. Specific architecture mismatches or drift to correct

### 4.1 Standalone warning text drift

In `app.py`, startup warning text says standalone implies raw input pickle-to-disk behavior.  
Current `core_config.py` now supports mode-based backend resolution (`auto -> mongo` in standalone), so this warning is outdated and can mislead operators.

Enhancement:
- Update warning to reflect effective backend (`memory|mongo|pickle`) from config resolution.

### 4.2 `config.toml` is informational, not runtime authority

Current design explicitly uses programmatic registration and does not load TOML as source of truth. This is valid, but team members may assume TOML is authoritative.

Enhancement:
- Add explicit “single source of truth” section in docs and CI check for config drift (optional).

## 5. Taipy 4.x-aligned opportunities relevant to this UI

Already used:
- `chart` with `figure` for Plotly-heavy visuals.

Good next adoptions for this app:

1. `table.sortable` for high-density Job History / Audit / Sessions tables.
2. `input`/`number` `action_on_blur` for large forms and filters to reduce callback churn.
3. Continue native `scenario_selector`/`job_selector` + Submission monitor for operational troubleshooting.

## 6. Stress and large-dataset readiness assessment

Current strengths:
- chunked anonymization path
- Mongo batch writes
- progress snapshots
- stress tooling and docs

Remaining bottlenecks:
- pre-submit full-file parse in memory
- no queue backpressure
- process-memory job registry
- unresolved standalone+mongo pickling edge

Recommended hard target profile:

- Sustained ingestion with bounded memory
- deterministic queue behavior under concurrent submits
- reliable status transitions across restarts
- repeatable standalone+mongo E2E pass criteria in CI-like script

## 7. Security/compliance hardening opportunities

1. Default production profile to mongo-backed raw input and store backend.
2. Ensure sensitive payloads are never logged in audit/details fields.
3. Add configuration guardrails:
- fail startup if `ANON_MODE=standalone` with `raw_input=memory`
- warn/fail in production when `raw_input=pickle`
4. Add explicit data retention/deletion policy doc and command.

## 8. Recommended implementation roadmap

### Sprint 1 (P0 stabilization)

1. Persistent job registry model + monitor rebuild from persistence.
2. Standalone+mongo reliability fix and E2E validation script.
3. Queue/backpressure controls and explicit queue position in Jobs monitor.
4. Status model unification (`running/done/failed/cancelled/...`) across UI/store/snapshots.

### Sprint 2 (P1 product UX)

1. Mode-aware dashboard rendering.
2. Streaming CSV ingest option.
3. Snapshot/scenario retention tasks.
4. Geo enrichment adapter with fallback dictionary.

### Sprint 3 (P2 maintainability + test depth)

1. `app.py` modularization.
2. GUI smoke tests.
3. Accessibility and keyboard flow pass.

## 9. Quick wins (can implement immediately)

1. Fix standalone backend warning copy to reflect real backend.
2. Add `table.sortable` to Jobs/Audit/Sessions tables.
3. Add queue depth + queued position labels in Active Run Monitor.
4. Add retention config env vars and a cleanup command.
5. Add one integration test for “submit -> complete -> persisted monitor record”.

## 10. Assessment conclusion

The repo is already a solid functional prototype with strong UI breadth and improving Taipy/Mongo alignment.  
For your use case (operator-facing PII workflow with large datasets), the highest-value next step is production-hardening the orchestration lifecycle, not adding more pages.

If you execute the P0 set first, you will materially improve reliability under stress and make the existing UI significantly more trustworthy for real workloads.
