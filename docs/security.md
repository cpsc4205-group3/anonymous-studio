# Security

> **Anonymous Studio — CPSC 4205 Course Project**
> This document covers the threat model, applied security controls, known limitations, and hardening guidance for production deployment.

---

## ⚠️ Not Production-Ready Out of the Box

Anonymous Studio is a university capstone project. It ships with **no authentication** and **development-mode defaults** intentionally, so the team can run it locally without infrastructure.

Before deploying on any shared network or with real patient / customer data:

1. Add an authentication layer (see [Authentication](#authentication))
2. Switch to `ANON_MODE=standalone` with a dedicated MongoDB user
3. Enable TLS on MongoDB (`tls=true` in URI)
4. Set `ANON_UPLOAD_DIR` to a dedicated, restricted directory
5. Run behind a reverse proxy (nginx / Caddy) that terminates TLS

---

## Threat Model

| Threat | Likelihood | Impact | Mitigated? |
|--------|-----------|--------|-----------|
| Unauthenticated access to PII results | High (open LAN) | Critical | ⚠️ Optional controls available, off by default |
| Path traversal via `input_csv_path` | Low (internal only) | High | ✅ Fixed |
| Oversized file upload (DoS) | Medium | High | ✅ 500 MB cap |
| MIME-spoofed file upload | Low | Medium | ✅ Magic-byte check |
| MongoDB operator injection | Low | High | ✅ Status whitelists |
| Exception details leaked to browser | Medium | Low | ✅ Fixed |
| PII in world-readable temp files | Medium | High | ✅ mode=0o700 |
| Hardcoded hash salt (rainbow table) | Low | Low | ℹ️ Accepted for course |
| Pickle deserialization of untrusted data | Low (dev mode) | Critical | ✅ Mongo preferred |
| Credential exposure in logs | Low | High | ℹ️ Use separate env vars |

---

## Applied Security Controls

### 1. Path Traversal Guard (`tasks.py`)

CSV jobs that supply an `input_csv_path` are validated against `ANON_UPLOAD_DIR` before any file I/O:

```python
_upload_root = os.path.realpath(os.environ.get("ANON_UPLOAD_DIR", "uploads/"))
_resolved    = os.path.realpath(input_csv_path)
if not _resolved.startswith(_upload_root + os.sep):
    # reject — path escapes allowed root
```

Set `ANON_UPLOAD_DIR` to a dedicated directory outside the project root.

---

### 2. File Upload Limits (`services/jobs.py`)

**Size cap** — default 500 MB, configurable:

```env
ANON_MAX_UPLOAD_MB=500
```

**Magic-byte MIME validation** — file content is checked against known binary signatures before parsing:

| Extension | Magic bytes checked |
|-----------|-------------------|
| `.xlsx` | `PK\x03\x04` (ZIP container) |
| `.xls` | `\xd0\xcf\x11\xe0` (OLE2 container) |
| `.csv` | Rejected if binary header detected |

A `.csv` file that is actually an Excel binary (or any other format) is rejected with a clear error.

---

### 3. MongoDB Query Injection (`store/mongo.py`)

All user-supplied filter values are validated against explicit whitelists before reaching MongoDB:

```python
_VALID_CARD_STATUSES = frozenset({"backlog", "in_progress", "review", "done"})
_VALID_APPT_STATUSES = frozenset({"scheduled", "completed", "cancelled"})
_VALID_SEVERITIES    = frozenset({"info", "warning", "critical"})
```

An invalid `status` value raises `ValueError` server-side rather than being forwarded to the query.

---

### 4. Exception Sanitization (`app.py`)

Raw exception messages are never displayed to the browser. All system errors are:

- Logged server-side via `_log.exception(...)` (full traceback in server logs)
- Shown to the user as a generic message: `"Download failed. Try again or contact support."`

User-facing `ValueError` messages (e.g., "File is 612 MB — exceeds the 500 MB limit") are the only exception; they are intentionally generated with safe, human-readable text.

---

### 5. Temp File Permissions (`services/progress_snapshots.py`)

The progress snapshot directory is created with `mode=0o700` (owner read/write/execute only):

```python
os.makedirs(_SNAPSHOT_DIR, mode=0o700, exist_ok=True)
```

This prevents other OS users from reading job progress metadata.

---

### 6. Environment Variable Validation (`core_config.py`)

All numeric and enum env vars are validated at startup with clear error messages:

```env
ANON_MODE=development        # must be: development | standalone
ANON_WORKERS=4               # must be a positive integer
ANON_MONGO_WRITE_BATCH=5000  # must be integer ≥ 500
```

Invalid values fall back to safe defaults with a `UserWarning` rather than crashing.

---

### 7. Audit Log Integrity

Every action (job submit, download, card move, attestation) is written to the `audit_log` MongoDB collection, which is **capped** (50 MB, max 100 000 documents):

```python
self._db.create_collection("audit_log", capped=True, size=52_428_800, max=100_000)
```

Capped collections are append-only at the storage layer — documents cannot be updated or deleted once written.

---

### 8. PII at Rest

| Storage layer | Backend | Contains PII? | Encrypted at rest? |
|---|---|---|---|
| `raw_input` DataNode | MongoDB (recommended) | Yes — raw upload | Depends on MongoDB config |
| `raw_input` DataNode | Pickle | Yes — raw upload | ❌ No — avoid in production |
| `anon_output` DataNode | Pickle | Pseudonymised | ❌ No |
| `pii_sessions` collection | MongoDB | Truncated sample text | Depends on MongoDB config |
| Progress snapshots | JSON files (mode 0o700) | No — metadata only | N/A |

**Recommendation:** Use `ANON_RAW_INPUT_BACKEND=mongo` (default in standalone mode) and enable MongoDB Encrypted Storage Engine or filesystem encryption on the data volume.

---

## Authentication

The app ships with no login by default. Available mitigations:

### Built-in JWT verification for `rest_main.py` (optional)
Enable direct Auth0 JWT validation in Python:
```env
ANON_AUTH_ENABLED=1
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_API_AUDIENCE=https://anonymous-studio-api
```
Optional:
```env
ANON_AUTH_REQUIRED_SCOPES=read:jobs
ANON_AUTH_EXEMPT_PATHS=/healthz
```

### Local / Demo Only
No action needed. Restrict to `localhost` by not binding to `0.0.0.0`:
```env
ANON_BIND=127.0.0.1
```

### Shared Network / Lab
Add HTTP Basic Auth at the reverse proxy layer:

```nginx
# nginx example
location / {
    auth_basic "Anonymous Studio";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:5000;
}
```

### Production
Implement one of:
- **OAuth2 / OIDC** — Google, Azure AD, Okta via `authlib` or `flask-oidc`
- **Session-based auth** — `flask-login` + `werkzeug.security` for password hashing
- **Reverse proxy SSO** — nginx `auth_request` module or Caddy `forward_auth`

Add RBAC roles: `admin` (full access), `data-officer` (submit + download), `auditor` (read-only audit log).

---

## MongoDB Hardening

### Dedicated User (minimum privilege)
```js
db.createUser({
  user: "anon_app",
  pwd: "<strong-password>",
  roles: [{ role: "readWrite", db: "anon_studio" }]
})
```

### TLS
```env
ANON_MONGO_URI=mongodb://anon_app:pass@host:27017/anon_studio?tls=true&tlsCAFile=/path/to/ca.pem
```

### Credentials — use separate env vars, never embed in URI
```env
# Preferred — credentials separate from host
ANON_MONGO_HOST=db.example.com
ANON_MONGO_USER=anon_app
ANON_MONGO_PASSWORD=<password>
ANON_MONGO_DB=anon_studio

# Acceptable — URI with credentials (never log this value)
ANON_MONGO_URI=mongodb://anon_app:<password>@db.example.com/anon_studio?tls=true
```

The store factory (`store/__init__.py`) already strips credentials when constructing the display label shown in the UI.

---

## Pickle Backend Warning

Taipy Core uses pickle for `anon_output`, `job_stats`, and `job_config` DataNodes. Pickle files:

- Are stored under `ANON_STORAGE` (default `/tmp/anon_studio/`)
- Are **not encrypted** at rest
- Should never be loaded from an untrusted source

For `raw_input`, use `ANON_RAW_INPUT_BACKEND=mongo` in all non-development environments. The pickle backend emits a `UserWarning` at startup if selected.

---

## Known Accepted Risks

| Risk | Severity | Rationale |
|------|----------|-----------|
| No authentication | High | Course demo — documented, not deployed publicly |
| Hardcoded hash salt (`"anonymous-studio"`) | Low | Presidio hash operator; not used for passwords |
| No per-session rate limiting on job submit | Low | Single-tenant local deployment |
| No download throttling | Low | Audit log provides accountability trail |

---

## Security Checklist (Before Any Real Deployment)

- [ ] Add authentication (OAuth2, session, or reverse proxy)
- [ ] Run MongoDB with a dedicated low-privilege user
- [ ] Enable TLS on MongoDB connection
- [ ] Set `ANON_UPLOAD_DIR` to a dedicated directory outside project root
- [ ] Set `ANON_RAW_INPUT_BACKEND=mongo` (never pickle in production)
- [ ] Enable filesystem or MongoDB Encrypted Storage Engine
- [ ] Bind app to `127.0.0.1` and put nginx/Caddy in front
- [ ] Set `ANON_MAX_UPLOAD_MB` appropriate for your environment
- [ ] Review and rotate MongoDB credentials regularly
- [ ] Enable log aggregation (ship server logs to SIEM)
