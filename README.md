# Anonymous Studio — De-Identified Data Pipelines
**CPSC 4205 | Group 3 | Spring 2026**
*Carley Fant · Sakshi Patel · Diamond Hogans · Elijah Jenkins*

---

## Taipy Studio (Recommended)

Taipy Studio is a VS Code extension that makes building Taipy apps significantly faster. Install it before writing any new pages or modifying `core_config.py`.

### What it gives you

**Configuration Builder** — a point-and-click editor for taipy.core config files (`.toml`). Instead of manually writing DataNode, Task, and Scenario declarations, you build them visually and Taipy Studio generates the config. Opens in the VS Code Secondary Side Bar under "Taipy Configs".

**GUI Helper** — IntelliSense inside the Taipy Markdown DSL (`<|...|component|prop=value|>`). As you type visual element properties in `.md` files or Python strings, it autocompletes component names, property names, and variable references. Also includes a variable explorer and code navigation.

### Install

1. Make sure Taipy 3.0+ is installed in your venv (it is — `requirements.txt` pins `taipy>=3.1.0`)
2. Open VS Code → Extensions (`Ctrl+Shift+X`) → search **"Taipy"**
3. Install **Taipy Studio** — it automatically pulls in both sub-extensions

> Taipy Studio 2.0+ is required for Taipy 3.x. If you see a 1.x version in the marketplace, make sure you select 2.0 or later.

### Relevance to this project

| Taipy Studio feature | Where it helps in Anonymous Studio |
|---------------------|------------------------------------|
| Config Builder | Editing DataNodes / Tasks in `core_config.py` visually |
| GUI Helper IntelliSense | Writing page strings (`DASH`, `JOBS`, `PIPELINE`, etc.) in `app.py` |
| Variable explorer | Seeing all reactive state variables without reading the full file |
| `.toml` config view | If you migrate from inline `Config.configure_*` calls to a `.toml` file |

### Migrating to a `.toml` config (optional)

Right now `core_config.py` declares everything in Python. Taipy also supports `.toml` configuration files, which the Config Builder edits visually. If you want to use the GUI for your DataNode and Scenario setup:

```bash
# Export current config to toml (run once inside the venv)
python -c "from core_config import *; from taipy import Config; Config.export('config.toml')"
```

Then open `config.toml` in VS Code — Taipy Studio will show it in the Taipy Configs panel.

---



```
┌─────────────────────────────────────────────────────────┐
│  Taipy GUI  (app.py)                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │Dashboard │ │Upload/   │ │Pipeline  │ │Schedule/ │    │
│  │          │ │Jobs      │ │Kanban    │ │Audit     │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │
└───────┼────────────┼────────────┼────────────┼──────────┘
        │            │ invoke_    │            │
        │            │ long_      │            │
        ▼            ▼ callback   ▼            ▼
┌───────────────────────────────────────────────────────┐
│  taipy.core  (core_config.py)                         │
│                                                       │
│  DataNode: raw_input  ──┐                             │
│  DataNode: job_config ──┤──► Task: anonymize_task     │
│                          │      │                     │
│  DataNode: anon_output ◄─┤      └── tasks.py          │
│  DataNode: job_stats   ◄─┘          run_pii_          │
│                                     anonymization()   │
│  Scenario: pii_pipeline                               │
│  Orchestrator (development | standalone)              │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│  pii_engine.py           │
│  Presidio Analyzer       │
│  + AnonymizerEngine      │
│  (offline spaCy, no net) │
└──────────────────────────┘
```

## How Background Jobs Work

1. **User uploads** a CSV/Excel file on the Jobs page
2. **`invoke_long_callback`** fires — the GUI stays fully responsive
3. The callback thread calls **`cc.submit_job(df, config)`**
4. `submit_job` creates a fresh **taipy.core Scenario**, writes the two input DataNodes (`raw_input`, `job_config`), and calls `tc.submit(scenario)`
5. The Orchestrator picks up the job and runs **`run_pii_anonymization`** (in `tasks.py`):
   - Auto-detects text/PII columns
   - Processes in configurable chunks (default 500 rows)
   - Writes per-chunk progress to **`PROGRESS_REGISTRY`** dict
   - Returns `(anonymized_df, stats)` → written to output DataNodes
6. The GUI polls **`PROGRESS_REGISTRY`** when the user clicks "Refresh Progress"
7. On completion, results load into the preview table; the linked Kanban card auto-advances to **Review**

### Switching to True Parallel Workers (Production)
```bash
export ANON_MODE=standalone
export ANON_WORKERS=8
export ANON_RAW_INPUT_BACKEND=mongo
export ANON_MONGO_URI=mongodb://localhost:27017/anon_studio
export ANON_MONGO_WRITE_BATCH=5000
taipy run main.py
```
No code changes needed — `core_config.py` reads the env vars.  
`ANON_RAW_INPUT_BACKEND=auto` also works (it resolves to `mongo` in standalone).

### Current Mode and Defaults

- `ANON_MODE` supports:
  - `development` (default)
  - `standalone`
- If `ANON_MODE` is not set in `.env` or your shell, the app runs in `development`.
- Source of truth: `MODE = os.environ.get("ANON_MODE", "development")` in `core_config.py`.

Quick check:

```bash
echo "${ANON_MODE:-development}"
```

---

## Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Live job counts, pipeline status, upcoming reviews, recent audit |
| **PII Text** | Inline text analysis — highlights + anonymizes without file upload |
| **Upload & Jobs** | Submit large CSV/Excel as background jobs; progress bar; result preview + download |
| **Pipeline** | Kanban board (Backlog → In Progress → Review → Done) linked to job status |
| **Schedule** | Book and track PII review appointments, linked to pipeline cards |
| **Audit Log** | Filterable immutable log of every system and user action |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/cpsc4205-group3/anonymous-studio.git
cd anonymous-studio
```

### 2. Check your Python version

```bash
python --version
```

**You need Python 3.9, 3.10, 3.11, or 3.12.** Python 3.13+ is not supported with this Taipy range (`taipy>=3.1.0,<4.2`) and install/runtime will fail.

If you have only Python 3.13+, install 3.12 from [python.org](https://python.org) and use it explicitly in the next step.

### 3. Create and activate a virtual environment

```bash
# Use python3.12 explicitly to avoid picking up 3.14 if both are installed
python3.12 -m venv .venv

# Activate — run this every time you open a new terminal
source .venv/bin/activate        # Mac / Linux
.venv\Scripts\activate           # Windows
```

You'll see `(.venv)` at the start of your prompt when it's active. Run `python --version` inside the venv to confirm it shows 3.12.x.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Download the spaCy NER model (recommended)

Run this **while the venv is active** so the model installs into `.venv` and not system Python.

```bash
python -m spacy download en_core_web_lg
```

This enables detection of free-text entity types: `PERSON`, `LOCATION`, and `ORGANIZATION`. Without it the app still works but will only detect structured PII (emails, SSNs, phone numbers, credit cards, etc.).

In **Analyze Text**, use **Settings → NLP model** to switch runtime model mode:
- `auto` (default, best available installed model)
- `en_core_web_lg`
- `en_core_web_md`
- `en_core_web_sm`
- `en_core_web_trf`
- `blank` (regex-only fallback)

In **Batch Jobs**, use **Advanced Options → NLP model for this job** to pick the model per run (matches the Streamlit PoC workflow).

For standalone multi-worker runs, set `SPACY_MODEL` before startup so every worker resolves the same model.

> **Can't download right now?** Skip this step. The app falls back to a blank model automatically and shows a warning banner in the UI.

### 6. Run

```bash
taipy run main.py
```

Open **http://localhost:5000** in your browser.

If your shell does not resolve `taipy`, run:

```bash
python -m taipy run main.py
```

### 6.1 Auto-refresh during development

Taipy CLI supports hot-reload flags:

- `--use-reloader` / `--no-reloader`
- `--debug` / `--no-debug`

This repo reads these from environment variables in `app.py`:

- `ANON_GUI_USE_RELOADER=1` enables hot reload (preferred)
- `ANON_GUI_DEBUG=1` enables debug mode (preferred)
- Backward-compatible aliases are also supported: `TAIPY_USE_RELOADER`, `TAIPY_DEBUG`

Defaults are off (`0`) for stable production behavior, so restart is required unless you enable them.

Example (development only):

```bash
export ANON_GUI_USE_RELOADER=1
export ANON_GUI_DEBUG=1
taipy run main.py
```

### 7. Add to `.gitignore`

```
.venv/
__pycache__/
*.pyc
user_data/
/tmp/anon_studio_blank_en/
```

`user_data/` is where taipy.core writes DataNode pickles (job inputs and outputs). `/tmp/anon_studio_blank_en/` is the blank spaCy model fallback. Neither should be committed.

---

### Optional: real MongoDB

Mongo can be used for both:
1. Persistent app store (cards, appointments, audit): set `ANON_STORE_BACKEND=mongo` and `MONGODB_URI`
2. Raw input DataNode backend for standalone workers: set `ANON_RAW_INPUT_BACKEND=mongo` and `ANON_MONGO_URI` (or `ANON_MONGO_DB` + host fields)

```bash
export ANON_STORE_BACKEND=mongo
export MONGODB_URI=mongodb://localhost:27017/anon_studio
export ANON_RAW_INPUT_BACKEND=mongo
export ANON_MONGO_URI=mongodb://localhost:27017/anon_studio
export ANON_MONGO_WRITE_BATCH=5000
```

### Where Mongo DataNode Connects (Taipy Core)

If you are switching to Mongo mode and asking "where do I connect the DataNode?", the connection is configured in `taipy.core` (not in the UI store settings):

- Connection parsing: `core_config.py::_mongo_config_from_env()`
  - Reads `ANON_MONGO_URI` (or `MONGODB_URI`) and fallback fields like `ANON_MONGO_DB`, `ANON_MONGO_HOST`, `ANON_MONGO_PORT`.
- DataNode type selection: `core_config.py::_configure_raw_input_data_node()`
  - Uses `ANON_RAW_INPUT_BACKEND` (`auto | memory | mongo | pickle`).
  - In `development`, `auto -> memory`; in `standalone`, `auto -> mongo`.
- Runtime writes: `core_config.py::submit_job()`
  - For Mongo backend, raw input is converted to Mongo documents and written in batches (`ANON_MONGO_WRITE_BATCH`) via `write()` + `append()`.

Important separation:
- `ANON_STORE_BACKEND=mongo` configures the app's operational store (cards/audit/schedule).
- `ANON_RAW_INPUT_BACKEND=mongo` configures Taipy `raw_input` DataNode persistence for job input payloads.

---

## Auth0 Proxy Starter (GUI + REST)

For a lightweight Auth0 integration (without full BFF/KrakenD), use:

- `oauth2-proxy` for OIDC login/session
- `nginx` for route protection and forwarding
- optional `redis` for shared session storage

Starter files:

- `deploy/auth-proxy/docker-compose.yml`
- `deploy/auth-proxy/nginx.conf`
- `deploy/auth-proxy/.env.auth-proxy.example`
- `deploy/auth-proxy/README.md`

Quick start:

```bash
cp deploy/auth-proxy/.env.auth-proxy.example deploy/auth-proxy/.env.auth-proxy
make proxy-cookie-secret   # paste into OAUTH2_PROXY_COOKIE_SECRET

# Terminal A (GUI)
taipy run main.py

# Terminal B (REST on port 5001)
TAIPY_PORT=5001 taipy run rest_main.py

# Terminal C (auth proxy)
make auth-proxy-up
```

Open `http://localhost:8080`.

Stop:

```bash
make auth-proxy-down
```

### Direct Auth0 JWT Auth for REST (optional)

If you prefer token validation inside `rest_main.py` (instead of a proxy-only model),
set these env vars:

```bash
ANON_AUTH_ENABLED=1
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_API_AUDIENCE=https://anonymous-studio-api
```

Optional:

```bash
# Defaults to RS256
ANON_AUTH_JWT_ALGORITHMS=RS256
# Space/comma separated scopes required for every REST request
ANON_AUTH_REQUIRED_SCOPES=read:jobs
# Keep specific routes open (for probes, etc.)
ANON_AUTH_EXEMPT_PATHS=/healthz
```

Then run:

```bash
TAIPY_PORT=5001 taipy run rest_main.py
```

By default (`ANON_AUTH_ENABLED=0`), no token is required, which keeps local development flow unchanged.

---

## Large Dataset + Mongo Runbook

### Backend Matrix

| Environment | `ANON_MODE` | `ANON_RAW_INPUT_BACKEND` | `raw_input` DataNode behavior |
|---|---|---|---|
| Local dev | `development` | `auto` (default) | In-memory (no raw-input persistence across restart) |
| Production | `standalone` | `auto` | Mongo-backed collection (persistent, worker-safe) |
| Explicit Mongo | any | `mongo` | Mongo-backed collection |

### Data Node Explorer (what you should see)

When `pii_pipeline` is pinned in Taipy Data Node Explorer, these nodes are expected:
- `raw_input`
- `job_config`
- `anon_output`
- `job_stats`

`raw_input` will show large uploaded datasets. For large jobs with Mongo backend, writes are batched using `ANON_MONGO_WRITE_BATCH` to reduce memory spikes.

If the explorer shows `Pinned on ???`:
- No scenario is pinned yet, or no scenario has been created in this session.
- Submit one job from **Batch Jobs** to create a `pii_pipeline` scenario.
- In Data Node Explorer, pin `pii_pipeline`, then enable **Pinned only** if you want a filtered view.

### Raw Input DataNode — UI controls

In the **Jobs page → Advanced Options → Raw Input DataNode (MongoDB)** section:

| Control | What it does |
|---------|-------------|
| Status badge | Shows the resolved backend (`In Memory`, `Mongo`, `Pickle`) and env var context |
| Restart note | Reminds that `ANON_RAW_INPUT_BACKEND` is read at startup — backend changes require a restart |
| **MongoDB write batch slider** | Sets the number of documents per MongoDB write (`500`–`50,000`, default `5,000`). Applied to `core_config.MONGO_WRITE_BATCH` in the background thread before the DataNode write. |

The write batch value is per-job — you can lower it for very large uploads to reduce memory pressure without restarting.

### Tuning for very large files

Use these settings first:

```bash
export ANON_MODE=standalone
export ANON_WORKERS=8
export ANON_RAW_INPUT_BACKEND=mongo
export ANON_MONGO_URI=mongodb://localhost:27017/anon_studio
export ANON_MONGO_WRITE_BATCH=5000   # env var default; overridable per-job in UI
```

Then in the **Jobs page → Advanced Options**:
- **Chunk size (rows)**: higher for throughput (`2000`–`5000`), lower if you see memory pressure (`500`–`1000`).
- **MongoDB write batch**: lower (`1000`–`2000`) for very large uploads to avoid OOM on the DataNode write.
- **Compute backend**: `auto` (Dask when row count exceeds threshold) or `dask` to force Dask partitions.

Optional Dask compute backend for very large jobs:

```bash
pip install "dask[dataframe]>=2024.8.0"
export ANON_JOB_COMPUTE_BACKEND=auto   # auto | pandas | dask
export ANON_DASK_MIN_ROWS=250000       # auto-switch threshold
```

`auto` keeps pandas for small jobs and uses Dask partitions only when row count exceeds `ANON_DASK_MIN_ROWS`.

CSV uploads now use a staged file-path pipeline into the Taipy task (instead of eager full DataFrame parsing in UI callbacks), so large CSV jobs can run with worker-side `dd.read_csv(...)` when Dask is enabled.

Detailed runbook: `docs/large_dataset_stress.md`.

One command quick check:

```bash
make stress
```

### Stress validation (current baseline)

Latest run (March 5, 2026):
- Route stress: `210` requests, `0` failures, `P95 6.04ms`, `P99 99.70ms`
- Task stress: `300,000` DataFrame rows processed successfully
- Mongo-shaped payload stress: `250,000` rows processed successfully
- Full test suite: `82 passed`

### Taipy troubleshooting references (official docs)

- `invoke_long_callback` (periodic status updates): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_gui/invoke_long_callback/
- GUI callbacks guide: https://docs.taipy.io/en/latest/userman/gui/callbacks/
- Mongo collection DataNode config: https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/Config/#taipy.Config.configure_mongo_collection_data_node
- Core DataNode API (`write`, `append`, `read`): https://docs.taipy.io/en/latest/refmans/reference/pkg_taipy/pkg_core/pkg_data_node/DataNode/

---

## File Structure

The layout follows Taipy conventions: entrypoints and core modules live at the
root so `taipy run main.py` resolves imports without extra packaging, while
supporting logic is split into focused packages.

```
anonymous-studio/
│
│  # ── Entrypoints ──────────────────────────────────────────────────────────
├── main.py              Taipy CLI entrypoint (`taipy run main.py`)
├── rest_main.py         Taipy REST API entrypoint (`taipy run rest_main.py`)
├── app.py               GUI state variables, callbacks, and runtime wiring
│
│  # ── Taipy core pipeline ──────────────────────────────────────────────────
├── core_config.py       DataNode / Task / Scenario configs + Orchestrator bootstrap
├── config.toml          Mirror of core_config.py for the Taipy Studio VS Code extension
├── tasks.py             run_pii_anonymization() — the function the Orchestrator executes
├── scheduler.py         Background appointment scheduler (daemon thread)
│
│  # ── Domain logic ─────────────────────────────────────────────────────────
├── pii_engine.py        Presidio Analyzer + Anonymizer wrapper; spaCy model resolution
│
│  # ── UI ───────────────────────────────────────────────────────────────────
├── pages/               Taipy Markdown DSL page strings (one const per page)
│   ├── __init__.py          Re-exports PAGES dict
│   └── definitions.py       DASH, QT, JOBS, PIPELINE, SCHEDULE, AUDIT, UI_DEMO
├── ui/
│   └── theme.py             Plotly / Taipy stylekit constants and colour tokens
├── app.css              Custom CSS overrides (taipy-* class selectors)
├── images/              SVG icons used by the navigation menu
│
│  # ── Services ─────────────────────────────────────────────────────────────
├── services/            Extracted business logic (keeps app.py manageable)
│   ├── app_context.py       AppContext dataclass — runtime registries
│   ├── attestation_crypto.py  File integrity hashing
│   ├── auth0_rest.py        Auth0 JWT middleware for REST API
│   ├── geo_signals.py       Geo-token normalisation helpers
│   ├── job_progress.py      Progress read/write/clear (PROGRESS_REGISTRY bridge)
│   ├── jobs.py              Job submission helpers
│   ├── progress_snapshots.py  Durable progress snapshot storage
│   ├── synthetic.py         OpenAI-based synthetic data generation
│   └── telemetry.py         Optional telemetry hooks
│
│  # ── Data store ───────────────────────────────────────────────────────────
├── store/               Backend-agnostic persistence (cards, audit, appointments)
│   ├── __init__.py          get_store() factory + singleton
│   ├── base.py              Abstract StoreBase interface
│   ├── models.py            PipelineCard, Appointment, PIISession, AuditEntry
│   ├── memory.py            In-memory implementation (default)
│   ├── mongo.py             MongoDB implementation
│   └── duckdb.py            DuckDB implementation
│
│  # ── Tests & scripts ──────────────────────────────────────────────────────
├── tests/               pytest suite (test_pii_engine, test_store, …)
├── scripts/             Utility scripts (key generation, stress testing, …)
│
│  # ── Deployment ───────────────────────────────────────────────────────────
├── deploy/
│   ├── auth-proxy/          OAuth2-proxy + Docker Compose for auth
│   └── grafana/             Grafana dashboards for monitoring
│
│  # ── Project config ───────────────────────────────────────────────────────
├── requirements.txt     Python dependencies (taipy, presidio, spacy, …)
├── Makefile             Stress tests, mongo-check, auth-proxy up/down
├── pytest.ini           Pytest configuration
├── .env.example         Sample environment variables
├── .gitignore
└── .taipyignore         Prevents Taipy's built-in server from exposing source files
```

### Why this layout works for Taipy

| Convention | Rationale |
|------------|-----------|
| Root-level `app.py` + `main.py` | `taipy run main.py` expects the GUI module at the import root — no `src/` wrapper needed |
| `pages/` package | Keeps Markdown DSL strings out of `app.py`; Taipy resolves bindings from the module where `Gui()` is created |
| `core_config.py` + `config.toml` | Programmatic config is authoritative; TOML is a read-only mirror for Taipy Studio |
| `store/` package | Separates data persistence from Taipy — `app.py` only calls `get_store()` public methods |
| `services/` package | Extracts business logic from callbacks so `app.py` stays focused on state + UI |
| `.taipyignore` | Blocks Taipy's static file server from exposing `.py`, `.toml`, `.env`, and internal dirs |
```
v2_anonymous-studio/
├── app.py             Main Taipy GUI — all pages, state, callbacks
├── core_config.py     taipy.core: DataNodes, Task, Scenario, Orchestrator
├── tasks.py           run_pii_anonymization() — the actual pipeline function
├── pii_engine.py      Presidio wrapper — analyze(), anonymize(), highlight_html()
├── store.py           In-memory store for Kanban cards, appointments, audit log
├── config.toml        Declarative config mirror (for Taipy Studio extension)
├── requirements.txt
└── docs/
    ├── deployment.md  Deployment notes — online, offline, Docker, cloud
    └── spacy.md       What spaCy is and how Anonymous Studio uses it
anonymous_studio/
├── main.py          Taipy CLI entrypoint (`taipy run main.py`)
├── app.py           App state, callbacks, and runtime wiring
├── pages/
│   ├── __init__.py
│   └── definitions.py   Taipy page markup strings
├── core_config.py   taipy.core: DataNodes, Task, Scenario, Orchestrator
├── tasks.py         run_pii_anonymization() — the actual pipeline function
├── pii_engine.py    Presidio wrapper — analyze(), anonymize(), highlight_html()
├── store.py         In-memory store for Kanban cards, appointments, audit log
└── requirements.txt
```

## Entity Types Detected
`EMAIL_ADDRESS` · `PHONE_NUMBER` · `CREDIT_CARD` · `US_SSN` · `US_PASSPORT`
`US_DRIVER_LICENSE` · `US_ITIN` · `US_BANK_NUMBER` · `IP_ADDRESS` · `URL`
`IBAN_CODE` · `DATE_TIME` · `LOCATION` · `PERSON` · `NRP` · `MEDICAL_LICENSE`

## Anonymization Operators
| Operator | Example output |
|----------|---------------|
| `replace` | `<EMAIL_ADDRESS>` |
| `redact`  | *(text deleted)* |
| `mask`    | `********************` |
| `hash`    | `a665a45920...` (SHA-256) |

The `hash` operator uses **SHA-256 with salt `"anonymous-studio"`**. The same PII value always produces the same hash within this deployment, enabling cross-record correlation without exposing the original text.

---

## Store Backend

Two backends for operational data (pipeline cards, audit log, appointments, PII sessions):

| Backend | When to use |
|---------|-------------|
| `memory` (default) | Development and demos — fast, no external dependency, resets on restart |
| `mongo` | Persistent data across restarts |

### Switching at runtime

Click the **⚙** gear in the top banner → Store Settings. Select **mongo**, enter a URI, click **Apply** — no restart needed.

```
mongodb://localhost:27017/anon_studio       # local
mongodb+srv://user:pass@cluster/anon_studio # Atlas
```

The Store Settings dialog also includes a **Job Data Nodes** explorer so you can inspect Taipy DataNode contents (raw input, anonymized output, stats) without navigating to the Audit page.

**Note:** The store backend (cards, audit, schedule) is separate from the Taipy DataNode backend (job I/O). See *Where Mongo DataNode Connects* above for DataNode configuration.

### MongoDB connection fast-fail

`MongoStore` sets `serverSelectionTimeoutMS=3000`. If the server is unreachable the dialog shows an error within ~3 seconds and reverts to in-memory (default was 30 s, making Apply appear frozen).

### pymongo

`pymongo[srv]>=4.7` is in `requirements.txt`. If missing, Store Settings shows:
```
⚠ pymongo is not installed. Run: pip install 'pymongo[srv]>=4.7'
```

---

## File Integrity Hash

After uploading a CSV or Excel file the Jobs page shows the **SHA-256 of the original file bytes** beneath the filename:

```
filename.csv  ✓
SHA-256  a3f8c2d1e4b7f9...
```

Verify locally before and after transfer to confirm the file was not altered:

```bash
sha256sum filename.csv          # Linux / WSL
shasum -a 256 filename.csv      # macOS
CertUtil -hashfile filename.csv SHA256   # Windows
```

---

## Security

See **[docs/security.md](docs/security.md)** for the full threat model, applied controls, and production hardening checklist.

**TL;DR — controls in place:**

| Control | Status |
|---------|--------|
| Path traversal on CSV input | ✅ `ANON_UPLOAD_DIR` whitelist |
| File upload size cap | ✅ 500 MB (`ANON_MAX_UPLOAD_MB`) |
| MIME-type validation | ✅ Magic-byte check on xlsx/xls |
| MongoDB query injection | ✅ Status / severity whitelists |
| Exception details in browser | ✅ Sanitized; full trace server-side only |
| Temp file permissions | ✅ `mode=0o700` |
| Audit log tamper-resistance | ✅ MongoDB capped collection (append-only) |
| Authentication | ❌ None — course demo, see security.md |

---

## Performance

See **[docs/performance.md](docs/performance.md)** for:

- Benchmark reference numbers (interactive text, batch jobs, dashboard)
- All applied optimizations with before/after code (OperatorConfig cache, denylist regex cache, `lru_cache` on model options, `store.stats()` rewrite, dashboard `list_sessions()` hoist, pipeline `list_cards()` elimination)
- Tuning knobs (`ANON_JOB_COMPUTE_BACKEND`, `ANON_DASK_MIN_ROWS`, entity filtering, `fast=True`, score threshold)
- spaCy model speed/accuracy tradeoff table
- Known remaining bottlenecks and mitigations
