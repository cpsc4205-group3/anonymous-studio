# Taipy Recursive Docs Audit

Date: 2026-03-05

## Scope

This audit compares the current codebase against Taipy official documentation (latest + 3.1 reference blog context), with focus on:

- All Taipy APIs imported/called in backend code.
- All Taipy GUI controls used in `pages/definitions.py`.
- 3.1-era features referenced by the product blog (Submission, Plotly figure integration, third-party content integration, distributed execution).
- Current Taipy GUI v4 style and callback best-practice alignment.

## Recursive Crawl Evidence

A recursive crawl over Taipy docs/site sections was executed and reached:

- `219` pages under `docs.taipy.io` (GUI visual elements + Taipy API reference + 3.1 release notes tree).
- `1` page under `taipy.io` (3.1 blog entry).

## Runtime/Test Validation

Executed:

- `pytest -q` -> `78 passed`.
- Taipy GUI smoke routes -> `/`, `/dashboard`, `/analyze`, `/jobs`, `/pipeline`, `/schedule`, `/audit` all returned `200`.
- Orchestrator startup observed in logs (`Orchestrator service has been started.`).

## Comparison Matrix

### Core API usage

1. `tp.run(gui, orchestrator, **kwargs)` -> compliant with Taipy run-service model.
2. `tc.create_scenario(...)` + `tc.submit(...)` -> compliant with scenario submission docs.
3. `Status` handling includes full lifecycle values (`SUBMITTED/BLOCKED/PENDING/RUNNING/CANCELED/FAILED/COMPLETED/SKIPPED/ABANDONED`).
4. `invoke_long_callback(...)` callback model -> compliant.
5. `EventProcessor(...).broadcast_on_event(...).start()/stop()` -> compliant.
6. `Config.configure_core(...)`, `configure_job_executions(...)`, `configure_*_data_node(...)` -> compliant to current reference pages.

### GUI control usage

Controls used in `pages/definitions.py` were compared against GUI visual-element docs:

- Generic: `menu`, `part`, `layout`, `text`, `button`, `selector`, `chart`, `table`, `progress`, `file_selector`, `pane`, `dialog`, `input`, `slider`, `number`, `date`.
- Core: `scenario_selector`, `scenario`, `job_selector`, `data_node_selector`, `data_node`.

All are documented and valid in current docs.

## Findings and Fixes Applied

1. `file_selector` callback alignment fix.
- Finding: docs define selected file path via bound `content` value, while code previously prioritized `payload.path`.
- Fix: `on_file_upload()` now reads `state.job_file_content` first (docs-aligned) and keeps payload path as fallback.

2. Dev reloader/debug handling improved.
- Added env-driven toggles in `run_app()`:
  - `TAIPY_USE_RELOADER` (`0/1`)
  - `TAIPY_DEBUG` (`0/1`)
- Defaults remain `False`, but hot-reload/debug can now be enabled without code edits.

3. Store backend selection made explicit.
- Added `ANON_STORE_BACKEND` with modes:
  - `memory` (default)
  - `mongo`
  - `auto` (legacy behavior)
- Prevents accidental Mongo auto-selection unless explicitly requested.

4. Analyze summary/profile strip refactor (Taipy-native controls only).
- Uses only documented Taipy GUI elements: `part`, `layout`, `text`, `table`, `chart`, `button`, `selector`, `dialog`.
- Replaced ad-hoc summary formatting with consistent KPI + profile blocks.
- Kept content flat and readable for dark theme operation (no custom JS widgets).

5. UI text normalization for operator readability.
- Replaced mixed unicode separators in Analyze status/profile summaries with ASCII separators (`|`, `x`) for consistency.
- Updated Analyze section titles to simple numbered labels (`1.`, `2.`, `3.`).

## Taipy v4 Best-Practice Checks

1. Callback-driven UI updates:
- Long operations continue to use `invoke_long_callback(...)` and explicit state refreshes.

2. Declarative GUI controls:
- Analyze page remains fully declarative in Taipy markup (no non-Taipy front-end framework components).

3. Styling model:
- Uses Taipy-supported application stylesheet (`app.css`) without external component overrides that bypass Taipy controls.

## Residual Notes

1. There is still a backward-compat fallback path using `tc.get_parents(job)` in status resolution logic.
- It is guarded by `try/except` and only used as fallback.
- Primary path uses current `job.submit_entity_id`.

## Primary Sources

- Taipy 3.1 blog: https://taipy.io/blog/taipy-3-1-elevating-ai-and-data-workflows
- Taipy 3.1 release notes: https://docs.taipy.io/en/release-3.1/release-notes/version-3.1/release-notes/
- Taipy run() reference: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/run/
- Config reference: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_common/pkg_config/Config/
- Status enum: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/Status/
- Orchestrator reference: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/Orchestrator/
- invoke_long_callback reference: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_gui/invoke_long_callback/
- EventProcessor reference: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_event/EventProcessor/
- Scenario submission user manual: https://docs.taipy.io/en/latest/userman/scenario_features/task-orchestration/scenario-submission/
- GUI visual elements root: https://docs.taipy.io/en/latest/refmans/gui/viselements/
- file_selector: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/file_selector/
- chart: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/chart/
- table: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/table/
- pane: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/pane/
- dialog: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/dialog/
- menu: https://docs.taipy.io/en/latest/refmans/gui/viselements/generic/menu/
- GUI styling: https://docs.taipy.io/en/latest/userman/gui/styling/
- GUI callbacks: https://docs.taipy.io/en/latest/userman/gui/callbacks/
- scenario_selector: https://docs.taipy.io/en/latest/refmans/gui/viselements/corelements/scenario_selector/
- job_selector: https://docs.taipy.io/en/latest/refmans/gui/viselements/corelements/job_selector/
- data_node_selector: https://docs.taipy.io/en/latest/refmans/gui/viselements/corelements/data_node_selector/
- scenario: https://docs.taipy.io/en/latest/refmans/gui/viselements/corelements/scenario/
- data_node: https://docs.taipy.io/en/latest/refmans/gui/viselements/corelements/data_node/
