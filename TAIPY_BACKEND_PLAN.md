# Taipy Backend Compliance and Enhancement Plan

Last updated: 2026-03-05

Related audit:
- `TAIPY_DOC_RECURSIVE_AUDIT.md` (recursive docs comparison + runtime/test evidence)

## Compliance Check (Taipy 4.1 docs)

Current backend alignment:

1. Core and job execution configuration uses documented modes.
- `Config.configure_core(..., mode="development"|"experiment")`
- `Config.configure_job_executions(mode="development"|"standalone", max_nb_of_workers=...)`

2. Scenario submission follows Taipy orchestration flow.
- Scenario is created via `tc.create_scenario(...)`
- Submitted via `tc.submit(...)` (returns `Submission`)

3. In-memory DataNode safety guard is in place.
- `raw_input` in-memory backend is allowed only in development mode.
- Standalone mode is guarded to avoid unsupported in-memory multiprocessing behavior.

4. Job status mapping now covers all Taipy `Status` enum values.
- `SUBMITTED`, `BLOCKED`, `PENDING`, `RUNNING`, `CANCELED`, `FAILED`, `COMPLETED`, `SKIPPED`, `ABANDONED`

5. Progress monitor now reconciles UI state with authoritative Taipy job status.
- Avoids stale "Queuing..." / "Running" states when orchestrator status has moved to terminal states.

## Fixes Applied in This Pass

Files changed:
- `app.py`
- `pages/definitions.py`
- `core_config.py`
- `tasks.py`
- `services/progress_snapshots.py`
- `tests/test_progress_snapshots.py`

Behavioral fixes:
- App startup now runs GUI with Taipy `Orchestrator` service (`tp.run(gui, Orchestrator, ...)`) so submitted jobs are dispatched/executed.
- Fixed job-to-scenario status lookup for current Taipy API (`job.submit_entity_id`) with backward-compatible fallback.
- Implemented durable progress snapshots on disk (`ANON_STORAGE/progress_snapshots`) and made monitor/table polling read the freshest source (snapshot vs in-memory registry).
- Resolved conflicting monitor text (`Active Job` + `No job running.`).
- Added stale-state reset when active job id no longer exists.
- Added Taipy-status reconciliation in `_sync_active_job_progress()`.
- Expanded `_resolve_job_status()` for full enum coverage.
- Updated job table fallback status/count logic to rely on Taipy status when in-memory progress is stale.
- Removed numbered section labels in Jobs monitor UI for consistency.

## Enhancement Roadmap

### Phase 1 (P0): Robust Progress Semantics

1. Replace `PROGRESS_REGISTRY` as the single source of truth.
- Keep registry for fast UI hints.
- Persist progress snapshots in Taipy-managed storage (DataNode or store backend) for cross-process reliability.

2. Add orchestrator health check and recovery signal.
- On each poll, detect "job not found" / terminal inconsistencies.
- Surface explicit health state in monitor (`Orchestrator Healthy`, `Worker Missing`, `Submission Orphaned`).

3. Make queue lifecycle explicit.
- Distinguish `Submitted`, `Pending`, `Blocked`, `Running`, `Completed`, `Failed`, `Cancelled`, `Skipped`, `Abandoned` in UI.

### Phase 2 (P1): Quality and Test Coverage

1. Add unit tests around status reconciliation.
- `_resolve_job_status()`
- `_sync_active_job_progress()`
- `_refresh_job_health()`

2. Add integration smoke tests.
- Submit -> poll -> done path.
- Submit -> cancel path.
- Removed job path.
- Standalone mode simulation path.

3. Add regression test for monitor text coherence.
- Ensure no simultaneous conflicting monitor lines.

### Phase 3 (P2): Observability and Ops

1. Emit structured events for each job transition.
- `job.submit`, `job.pending`, `job.running`, `job.done`, `job.failed`, `job.cancelled`.

2. Add a backend metrics feed suitable for Grafana-style dashboards.
- Queue depth, run latency, failure ratio, abandoned ratio, mean entities per row.

3. Add retention policy for old scenarios/jobs.
- Scheduled cleanup with audit-safe retention window.

### Phase 4 (P3): Taipy 3.1-Inspired Enhancements

1. Submission-centric monitor model. ✅ Implemented
- Active Run Monitor now displays `Active Submission` and `Submission Status`.
- Backend persists and resolves submission id per job (`job_id -> submission_id`) with fallback discovery from `tp.get_submissions()`.

2. Native Plotly-first operational charts.
- Keep operational visualizations as direct Plotly figure objects (already supported in Taipy chart control).
- Add run-throughput and queue-depth time series using the same flat theme tokens.

3. Third-party content provider path for advanced panels.
- Use `Gui.register_content_provider()` only for specialized embeds (for example, rich run diagnostics panes), while keeping core monitor controls native Taipy.

4. Cluster-mode readiness guardrails.
- Keep community-safe `development|standalone` defaults.
- Add explicit docs/runtime warning that cluster mode is Enterprise-only before enabling distributed execution paths.

### Phase 5 (P0): Security Hardening Backlog

1. Limit backend configuration disclosure in user-facing UI.
- Current state: Jobs banner tooltip exposes `ANON_RAW_INPUT_BACKEND` and `ANON_MODE`.
- Target: keep user-facing label (`Mongo` / `In Memory` / `Pickle`) but hide env-key details unless debug/admin mode is enabled.
- Candidate gate: `ANON_UI_SHOW_INTERNAL_CONFIG=1`.

2. Sanitize store connection errors shown in UI.
- Current state: Store settings can surface raw exception text on connection failure.
- Risk: exception strings may include internal hostnames, ports, and driver details.
- Target: show generic user message, write full exception only to server logs/audit diagnostics.

## Recommended Next Implementation Slice

Implement P0.2 next:
- Add explicit orchestrator health surface (`healthy`, `dispatcher missing`, `submission orphaned`) in Active Run Monitor.
- Add timeout watchdog to auto-flip stale queued states to actionable error hints.

## Primary References

- Taipy 3.1 blog (Mar 24, 2024): https://taipy.io/blog/taipy-3-1-elevating-ai-and-data-workflows
- Taipy 3.1 release notes: https://docs.taipy.io/en/release-4.0/release-notes/version-3.1/
- Run multiple services (`tp.run`): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_run/
- Chart `figure` property (Plotly): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_gui/pkg_builder/Chart/
- Content provider / third-party integration: https://docs.taipy.io/en/latest/userman/gui/pages/partials/
- Status enum: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/Status/
- Scenario submission: https://docs.taipy.io/en/latest/userman/scenario_features/task-orchestration/scenario-submission/
- Job execution configuration (`configure_job_executions`): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_common/pkg_config/Config/
- Core configuration: https://docs.taipy.io/en/latest/userman/advanced_features/configuration/core-config/
- Long callbacks (`invoke_long_callback`): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_gui/invoke_long_callback/
- Event processor: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_event/EventProcessor/
- In-memory DataNode warning (multi-process): https://docs.taipy.io/en/release-4.0/userman/scenario_features/data-integration/data-node-config/
