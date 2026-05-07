# Anonymous Studio - De-Identified Data Pipelines

**CPSC 4205 | Group 3 | Spring 2026**

Anonymous Studio is a production-grade PII (Personally Identifiable Information) detection and anonymization platform. It processes structured data files (CSV/Excel) and free text through an enterprise NLP pipeline, tracking every job through a Kanban workflow with cryptographically signed compliance attestations and a tamper-resistant audit log.

---

## Team Members

| Name | Role | GitHub |
|------|------|--------|
| Carley Fant | Project Lead, Backend & Security | [@51nk0r5w1m](https://github.com/51nk0r5w1m) |
| Sakshi Patel | UI/UX Developer | [@Sakshi2131](https://github.com/Sakshi2131) |
| Elijah Jenkins | Authorization & Security | [@ejenkins0113](https://github.com/ejenkins0113) |

---

## Technology Stack

| Category | Technology |
|----------|-----------|
| **Language** | Python 3.9–3.12 |
| **GUI Framework** | [Taipy](https://www.taipy.io/) 3.1+ (GUI + Core orchestration) |
| **NLP / PII Detection** | [Microsoft Presidio](https://microsoft.github.io/presidio/) Analyzer + Anonymizer |
| **NER Model** | [spaCy](https://spacy.io/) `en_core_web_lg` (with blank regex fallback) |
| **Data Processing** | Pandas 2.x; Dask (optional, >250K rows) |
| **Database** | MongoDB (production persistence); DuckDB (analytics alternative) |
| **Authorization** | [OpenFGA](https://openfga.dev/) fine-grained authorization |
| **Authentication** | Auth0 JWT (REST API); oauth2-proxy + nginx (GUI proxy) |
| **Telemetry** | Prometheus metrics + Grafana dashboards |
| **REST API** | Taipy REST + FastAPI |
| **Synthetic Data** | OpenAI / Azure OpenAI; Faker |
| **Deployment** | Docker Compose (auth proxy + OpenFGA stack) |
| **Testing** | pytest (22 test modules, 82+ tests) |

---

## Project Objectives Assessment

The following objectives are drawn from the original project proposal to rebuild the Presidio/Streamlit proof-of-concept as a production-ready, enterprise-grade anonymization platform.

### Objective 1: Migrate PII detection PoC from Streamlit to a production-ready Taipy application

**Status:** Met

The original Streamlit proof-of-concept was fully rebuilt using Taipy 3.1, with all original detection capabilities preserved and extended. The new application supports the same entity types (17 total), operators, threshold controls, allowlist/denylist configuration, and highlighted output — while adding Taipy Core orchestration, background job execution, and reactive state management. Feature parity tracking reached 92% (11/12 PoC features), with the remaining item (encrypt operator key management) partially implemented on the backend.

### Objective 2: Implement batch processing for large CSV and Excel files

**Status:** Met

The Batch Jobs page supports uploading CSV and Excel files (up to 500 MB) as non-blocking background jobs orchestrated by Taipy Core. Jobs run in configurable chunks (default 500 rows), report real-time progress through a polling registry, and automatically advance linked Kanban cards on completion. For very large datasets, an optional Dask compute backend handles files exceeding 250,000 rows. Stress testing validated 300,000+ row jobs and confirmed P95 response times of ~6ms for interactive routes.

### Objective 3: Build a Kanban pipeline management system for tracking anonymization tasks

**Status:** Met

The Pipeline page implements a full Kanban board with four columns (Backlog → In Progress → Review → Done). Cards are automatically created when batch jobs are submitted and advance through the board as jobs complete. Cards support manual editing, priority/label assignment, and compliance attestation with Ed25519 cryptographic signatures. Both CSV and JSON export of pipeline data are available for compliance documentation.

### Objective 4: Implement persistent storage with a pluggable backend architecture

**Status:** Met

The `store/` package provides a backend-agnostic interface (`StoreBase`) with three pluggable implementations: in-memory (default, for development), MongoDB (`MongoStore`), and DuckDB (`DuckDBStore`). The backend is switchable at runtime via the Store Settings dialog or `ANON_STORE_BACKEND` environment variable with no code changes required. MongoDB collections are indexed for audit log queries, and the Taipy Core DataNode backend is separately configurable (`ANON_RAW_INPUT_BACKEND`) for large job payloads.

### Objective 5: Create a comprehensive, tamper-resistant audit log for compliance

**Status:** Met

Every user and system action is logged to an immutable audit trail (MongoDB capped collection or in-memory equivalent). The Audit Log page provides a filterable, searchable view of all events with export to CSV and JSON. Compliance attestations are recorded with Ed25519 signatures and can be verified offline. All export operations themselves are logged to prevent audit bypass.

### Objective 6: Build a REST API for programmatic access to PII detection

**Status:** Met

A separate REST entrypoint (`rest_main.py`) exposes Taipy REST endpoints with optional Auth0 JWT authentication. API endpoints support PII detection, anonymization, and pipeline CRUD operations. Auth0 JWT validation (`services/auth0_rest.py`) is configurable via environment variables and disabled by default to keep local development simple. Swagger/OpenAPI documentation is auto-generated by Taipy REST.

### Objective 7: Implement fine-grained authorization and authentication

**Status:** Partially Met

OpenFGA fine-grained authorization was implemented for sensitive operations: attestation of pipeline cards (`can_attest`), audit log exports (`can_export`), and key pipeline/job mutations. Authorization checks are enforced at action time with fail-closed behavior — service errors deny rather than allow. An Auth0 JWT proxy stack (`deploy/auth-proxy/`) provides OIDC login for the GUI. However, full role-based user registration and login within the application UI (card-013) was not implemented; authentication remains proxy-based rather than in-app, which is appropriate for a course demo but would need to be extended for a production multi-user deployment.

### Objective 8: Enable production deployment with monitoring and container orchestration

**Status:** Partially Met

Docker Compose stacks are provided for the Auth0 proxy (`deploy/auth-proxy/`) and OpenFGA authorization server (`deploy/openfga/`). Prometheus metrics are exposed via `services/telemetry.py` and a Grafana dashboard is included in `deploy/grafana/`. A `Makefile` provides one-command startup for each stack. However, the application itself was not deployed to a cloud environment during the semester — all demonstrations ran locally. A production deployment to a cloud provider with a CI/CD pipeline remains as future work.

---

## Installation Instructions

### Prerequisites

- **Python 3.9, 3.10, 3.11, or 3.12** — Python 3.13+ is **not supported** with Taipy 3.x
- **Docker** (optional) — required only for MongoDB, OpenFGA, or auth proxy stacks
- **Git**

### 1. Clone the repository

```bash
git clone https://github.com/cpsc4205-group3/anonymous-studio.git
cd anonymous-studio
```

### 2. Create and activate a virtual environment

```bash
# Use python3.12 explicitly if multiple versions are installed
python3.12 -m venv .venv

source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

Confirm the version: `python --version` should show `3.12.x`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the spaCy NER model (recommended)

```bash
python -m spacy download en_core_web_lg
```

This enables detection of `PERSON`, `LOCATION`, and `ORGANIZATION` entity types via Named Entity Recognition. Without it, the app falls back to regex-only detection and shows a warning banner. Skip this step if you are offline — the fallback works automatically.

### 5. Configure environment variables (optional)

```bash
cp .env.example .env
# Edit .env as needed — all values are optional for local development
```

Key variables for local use:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANON_MODE` | `development` | `development` (default) or `standalone` (parallel workers) |
| `ANON_STORE_BACKEND` | `memory` | `memory`, `mongo`, or `auto` |
| `MONGODB_URI` | *(unset)* | MongoDB connection string (needed only for `mongo` backend) |
| `ANON_GUI_DEBUG` | `0` | Set to `1` for debug mode |
| `ANON_GUI_USE_RELOADER` | `0` | Set to `1` for hot reload during development |

No environment configuration is needed to run the app in development mode — all defaults work out of the box.

### 6. Run the application

```bash
taipy run main.py
```

Open **http://localhost:5000** in your browser.

If `taipy` is not on your PATH:

```bash
python -m taipy run main.py
```

---

## Usage Instructions

### Pages Overview

| Page | Description |
|------|-------------|
| **Dashboard** | Live job counts, pipeline status, service health, upcoming reviews, recent audit entries |
| **Analyze Text** | Interactive PII detection — paste text, adjust confidence threshold, choose operator, view highlighted results and entity table |
| **Batch Jobs** | Upload CSV/Excel files as background jobs with real-time progress, result preview, and download |
| **Pipeline** | Kanban board (Backlog → In Progress → Review → Done) linked to batch job status; supports attestation and export |
| **Schedule** | Book and manage compliance review appointments linked to pipeline cards |
| **Audit Log** | Filterable, exportable immutable log of every system and user action |

### Common Workflows

**Analyze a single document:**
1. Go to **Analyze Text** → paste text into the input box
2. Select entity types, confidence threshold, and anonymization operator
3. Click **Analyze** — highlighted results appear immediately
4. Use **Allowlist/Denylist** fields to fine-tune detection

**Process a CSV file:**
1. Go to **Batch Jobs** → click **Upload File**
2. Select your CSV or Excel file (up to 500 MB)
3. Configure chunk size and NLP model in **Advanced Options** if needed
4. Click **Submit Job** — progress updates in real time
5. When complete, click **Download Results** to get the anonymized CSV

**Attest a completed job:**
1. Go to **Pipeline** — find the card in the **Review** column
2. Click **Attest** — sign with Ed25519 cryptographic signature
3. Card advances to **Done**; attestation recorded in the audit log

### Switching to MongoDB persistence

```bash
# Start a local MongoDB instance (Docker required)
docker run -d -p 27017:27017 mongo:7

# Set environment variables
export ANON_STORE_BACKEND=mongo
export MONGODB_URI=mongodb://localhost:27017/anon_studio

taipy run main.py
```

Alternatively, click the **gear icon** in the top banner → Store Settings to switch without restarting.

---

## Known Issues and Future Enhancements

### Known Issues

- **`app.py` is monolithic** (5,500+ lines) — callbacks, state variables, and page logic are co-located, making the file difficult to navigate. A refactor into separate service modules is planned.
- **N+1 store queries on dashboard refresh** — `_refresh_dashboard()` issues 60+ individual store calls per refresh cycle. A 5-second TTL cache mitigates this but does not eliminate it.
- **No in-app user login** — Authentication is handled by an external oauth2-proxy. Users cannot register or log in directly within the application UI.
- **Scheduler race condition** — The background appointment scheduler writes to a shared dict without a mutex (see `scheduler.py:47-49`). Safe for single-process development mode but should be addressed before multi-worker deployment.
- **Encrypt operator UI incomplete** — The Presidio backend supports AES encryption/decryption, but the UI operator selector does not yet expose the `encrypt` option or key input field.

### Features We Would Add With More Time

- **In-app RBAC (card-013)** — Full user registration, login, and role-based access control (Admin, Compliance Officer, Developer, Researcher) with hashed passwords stored in MongoDB.
- **Compliance review notifications (card-014)** — Email or in-app notifications 24 hours before scheduled compliance review appointments, extending the existing scheduler.
- **File attachments on pipeline cards (card-015)** — Attach anonymized output files directly to Kanban cards for streamlined compliance documentation packages.
- **Image OCR PII detection (card-012)** — Accept PNG/JPG uploads, extract text via Tesseract OCR, and run Presidio on the extracted content.
- **Encrypt operator key management** — Complete the partially-implemented encrypt operator with UI key input, environment-variable key storage, and a decrypt round-trip for reversible anonymization.
- **Cloud deployment with CI/CD** — Deploy to a cloud provider (AWS ECS or GCP Cloud Run) with a GitHub Actions pipeline for automated testing and deployment.
- **`app.py` refactor** — Split the monolithic application file into focused modules: `callbacks/`, `state/`, `ui/` to improve maintainability and enable unit testing of individual callbacks.

---

## File Structure

```
anonymous-studio/
├── main.py              # Taipy CLI entrypoint
├── rest_main.py         # REST API entrypoint
├── app.py               # GUI state, callbacks, and runtime wiring
├── core_config.py       # Taipy DataNode / Task / Scenario config
├── tasks.py             # PII anonymization task (Orchestrator-executed)
├── scheduler.py         # Background appointment scheduler
├── pii_engine.py        # Presidio Analyzer + Anonymizer wrapper
├── pages/
│   └── definitions.py   # Taipy Markdown DSL page strings
├── services/            # Auth, attestation, telemetry, job, progress services
├── store/               # StoreBase interface + memory, MongoDB, DuckDB backends
├── ui/                  # Plotly/Taipy theme helpers
├── deploy/
│   ├── auth-proxy/      # oauth2-proxy + nginx Docker Compose stack
│   ├── openfga/         # OpenFGA authorization server stack
│   └── grafana/         # Prometheus + Grafana monitoring stack
├── tests/               # 22 pytest modules, 82+ tests
├── docs/
│   └── runbooks/        # deployment.md, spacy.md, store-utils.md
├── images/
│   └── icons/           # SVG nav icons (referenced by app.py and app.css)
├── scripts/             # Utility and dev scripts
├── requirements.txt
├── Makefile
└── .env.example
```

---

## Running Tests

```bash
# Run the full test suite
pytest

# Run a specific module
pytest tests/test_pii_engine.py -v
```

The test suite covers: PII engine, store backends (memory/Mongo/DuckDB), attestation crypto, Auth0 REST, OpenFGA authorization, export functionality, progress snapshots, and Taipy state smoke tests.
