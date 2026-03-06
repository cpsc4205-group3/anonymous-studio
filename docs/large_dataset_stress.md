# Large Dataset Stress Playbook

## Goal

Validate that Anonymous Studio can ingest, process, and monitor large datasets using Taipy with Mongo-backed `raw_input` DataNode.

## Recommended environment

```bash
export ANON_MODE=standalone
export ANON_WORKERS=8
export ANON_RAW_INPUT_BACKEND=mongo
export ANON_MONGO_URI=mongodb://localhost:27017/anon_studio
export ANON_MONGO_WRITE_BATCH=5000
```

Optional:

```bash
export MONGODB_URI=mongodb://localhost:27017/anon_studio
```

## What to verify in Data Node Explorer

Scenario: `pii_pipeline`

Nodes:
- `raw_input`
- `job_config`
- `anon_output`
- `job_stats`

Checks:
- `raw_input` row count matches uploaded dataset size
- `job_stats.processed_rows` matches input rows
- `job_stats.total_entities` is non-negative
- `anon_output` can be previewed and downloaded

If you see `Pinned on ???`:
- Submit a job first (this creates a `pii_pipeline` scenario instance).
- In Data Node Explorer, pin `pii_pipeline`.
- Toggle `Pinned only` after pinning to focus on the four pipeline nodes.

## Automated checks

### 0) One-command check

```bash
make stress
```

### 1) Unit/integration checks

```bash
TLDEXTRACT_CACHE=/tmp/tldextract-cache pytest -q
```

### 2) Large processing path checks

```bash
pytest -q tests/test_tasks_large.py
```

## Operational troubleshooting

1. Slow uploads or spikes:
   - Lower `ANON_MONGO_WRITE_BATCH` (for example `2000`).
2. Slow anonymization:
   - Increase Jobs page chunk size if memory allows.
   - Increase `ANON_WORKERS` in standalone mode.
3. Progress stuck:
   - Confirm app is running in standalone mode for multi-worker.
   - Confirm Mongo is reachable and `raw_input` writes succeed.
   - Refresh Jobs page monitor and inspect `job_stats` / audit events.
4. Data Node Explorer shows `Pinned on ???`:
   - No pinned scenario is selected yet.
   - Submit a run and pin `pii_pipeline`.

## Taipy references

- https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_gui/invoke_long_callback/
- https://docs.taipy.io/en/latest/userman/gui/callbacks/
- https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/Config/#taipy.Config.configure_mongo_collection_data_node
- https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/pkg_data_node/DataNode/
