# All Stories - Complete Inventory

This document consolidates ALL stories from the anonymous-studio project, including implemented features, work in progress, and backlog items. This was created to recover stories that may have been lost when the repository was archived.

**Last Updated:** 2026-03-06
**Total Stories:** 15 pipeline cards + additional feature requests documented below

---

## Story Status Legend

- ✅ **Done** — Fully implemented and tested
- ⚠️ **In Progress** — Partially implemented, work ongoing
- 📋 **Backlog** — Not yet started, planned for future
- 🔍 **Lost** — Referenced in memories but not found in codebase

---

## Pipeline Cards (card-001 through card-015)

These are the core project stories defined in `store/memory.py` as demo cards.

### ✅ card-001: Q1 Customer Export Anonymization
**Status:** Review (implemented)  
**Priority:** High  
**Labels:** HIPAA, customer-data  
**Assignee:** Carley Fant  
**Description:** De-identify customer names, emails, and SSNs from Q1 export.

### ✅ card-002: HR Records PII Scrub
**Status:** In Progress (implemented)  
**Priority:** Critical  
**Labels:** GDPR, HR  
**Assignee:** Sakshi Patel  
**Description:** Remove all PII from historical HR records prior to archival.

### ✅ card-003: Research Dataset Anonymization
**Status:** Done ✅  
**Priority:** Medium  
**Labels:** research  
**Assignee:** Diamond Hogans  
**Attestation:** ✅ Attested by Compliance Officer  
**Description:** Apply k-anonymity preprocessing and de-identify participant data.  
**Notes:** Verified: all PII removed per IRB protocol.

### 📋 card-004: Patient Records HIPAA Compliance
**Status:** Backlog  
**Priority:** High  
**Labels:** HIPAA, healthcare  
**Description:** Scrub PHI from inbound patient dataset before ML pipeline.

### 📋 card-005: Vendor Contract Data Review
**Status:** Backlog  
**Priority:** Low  
**Labels:** contracts  
**Assignee:** Elijah Jenkins  
**Description:** Flag and remove bank account numbers and SSNs from vendor contracts.

---

## Feature Enhancement Stories (card-006 through card-010)

### ✅ card-006: Allowlist / Denylist Support
**Status:** Done ✅  
**Priority:** Medium  
**Labels:** feature, pii-engine  
**Implementation:** `pii_engine.py`, `app.py`  
**Description:** Add allow_list and deny_list inputs to PII Text page. Pass allow_list= to analyzer.analyze() and use ad_hoc_recognizers=[PatternRecognizer(deny_list=...)] for denylist.

**Acceptance Criteria:**
- [x] UI fields for allowlist and denylist on PII Text page
- [x] PIIEngine.analyze() accepts allowlist parameter
- [x] PIIEngine.analyze() accepts denylist parameter
- [x] CUSTOM_DENYLIST entity type created
- [x] Post-filtering for allowlist implemented
- [x] Regex pattern cache for denylist

### ⚠️ card-007: Encrypt Operator Key Management
**Status:** In Progress (Partial) ⚠️  
**Priority:** Medium  
**Labels:** feature, security  
**Description:** Implement encrypt operator in pii_engine.py. Add 'encrypt' option to UI operator selector. Add UI field for AES encryption key (128/192/256-bit). Store key securely via env var (ANON_ENCRYPT_KEY). Enable DeanonymizeEngine decrypt round-trip for reversible anonymization.

**What's Implemented:**
- ✅ Presidio library supports encrypt/decrypt operators
- ✅ Backend infrastructure ready

**What's Missing:**
- ❌ UI operator selector doesn't include 'encrypt' option
- ❌ No UI field for encryption key input
- ❌ OperatorConfig("encrypt", {"key": key}) not implemented in pii_engine.py
- ❌ No env var (ANON_ENCRYPT_KEY) support
- ❌ No DeanonymizeEngine integration

**Acceptance Criteria:**
- [ ] Add 'encrypt' to operator selector dropdown
- [ ] Add encrypted text input field for AES key (128/192/256-bit)
- [ ] Validate key length (16/24/32 characters)
- [ ] Read ANON_ENCRYPT_KEY from environment
- [ ] Implement OperatorConfig("encrypt", {"key": key})
- [ ] Add DeanonymizeEngine.deanonymize() capability
- [ ] Test encrypt/decrypt round-trip
- [ ] Document key management in README

### ✅ card-008: ORGANIZATION Entity Support
**Status:** Done ✅  
**Priority:** Low  
**Labels:** feature, pii-engine  
**Implementation:** `pii_engine.py`  
**Description:** Add ORGANIZATION to ALL_ENTITIES in pii_engine.py. Configure ORG→ORGANIZATION NLP mapping with 0.4 confidence multiplier to reduce false positives.

**Acceptance Criteria:**
- [x] ORGANIZATION added to ALL_ENTITIES (now 17 entities total)
- [x] NLP mapping: spaCy ORG tag → ORGANIZATION
- [x] Confidence multiplier configured
- [x] Requires trained spaCy model (en_core_web_lg recommended)

### ✅ card-009: REST API for PII Detection
**Status:** Done ✅  
**Priority:** High  
**Labels:** feature, api  
**Implementation:** `rest_main.py`, `services/auth0_rest.py`  
**Description:** Build REST API endpoints for PII detection, de-identification, and pipeline CRUD using FastAPI. Add API key authentication and Swagger documentation.

**Acceptance Criteria:**
- [x] REST API entrypoint (rest_main.py)
- [x] Taipy Rest integration
- [x] Auth0 JWT authentication support
- [x] API endpoints for PII operations
- [x] Pipeline CRUD endpoints
- [x] Swagger/OpenAPI documentation

### ✅ card-010: MongoDB Persistence Layer
**Status:** Done ✅  
**Priority:** Critical  
**Labels:** feature, infrastructure  
**Assignee:** Sakshi Patel  
**Implementation:** `store/mongo.py`, `store/duckdb.py`  
**Description:** Implement MongoStore backend for persistent storage of sessions, cards, appointments, and audit logs. Read MONGODB_URI from env. Replace in-memory store for production use.

**Acceptance Criteria:**
- [x] MongoStore class in store/mongo.py
- [x] All StoreBase abstract methods implemented
- [x] MONGODB_URI environment variable support
- [x] Sessions, cards, appointments, audit logs persisted
- [x] Bonus: DuckDBStore alternative backend
- [x] Store backend switching via ANON_STORE_BACKEND env var

---

## Backlog Stories (card-011 through card-015)

### 📋 card-011: Export Audit Logs as CSV/JSON
**Status:** Backlog 📋  
**Priority:** Medium  
**Labels:** feature, compliance  
**Description:** Add download buttons to export audit log and pipeline data in CSV and JSON formats for compliance documentation sharing.

**⚠️ IMPORTANT NOTE:** Repository memories reference this as "implemented" with citations to:
- `app.py:5008-5072`
- `app.py:4926-5040`
- `pages/definitions.py:593-602`
- `pages/definitions.py:503-511`

However, these line numbers don't exist in current codebase. **This functionality appears to be LOST.**

**Acceptance Criteria:**
- [ ] Add "Export CSV" button to Audit page
- [ ] Add "Export JSON" button to Audit page
- [ ] Add "Export All CSV" button to Pipeline page
- [ ] Add "Export All JSON" button to Pipeline page
- [ ] Implement on_audit_export_csv callback
- [ ] Implement on_audit_export_json callback
- [ ] Implement on_pipeline_export_csv callback
- [ ] Implement on_pipeline_export_json callback
- [ ] Use pandas.to_csv() for CSV export
- [ ] Use json.dumps() for JSON export (no pickle)
- [ ] All exports log to audit trail
- [ ] Show success/error notifications
- [ ] Use taipy.gui.download() for file download

**UI Locations:**
- Audit page: After the audit log table, add "Export" section
- Pipeline page: After "All Cards" table, add "Export Pipeline Data" section

**Referenced Implementation (LOST):**
```python
# These functions were supposedly implemented but are missing:
# - on_audit_export_csv(state)
# - on_audit_export_json(state)
# - on_pipeline_export_csv(state)
# - on_pipeline_export_json(state)
```

### 📋 card-012: Image PII Detection via OCR
**Status:** Backlog 📋  
**Priority:** Low  
**Labels:** feature, ocr  
**Description:** Accept PNG/JPG uploads, extract text via Tesseract OCR, then apply Presidio PII detection to the extracted text. Display annotated results.

**Acceptance Criteria:**
- [ ] Add file upload widget for PNG/JPG on PII Text page
- [ ] Integrate Tesseract OCR (pytesseract library)
- [ ] Extract text from uploaded images
- [ ] Pass extracted text to PIIEngine.analyze()
- [ ] Display OCR text with PII highlighting
- [ ] Show detected entities table for image
- [ ] Add error handling for unsupported formats
- [ ] Document Tesseract installation in README

**Technical Requirements:**
- Install pytesseract: `pip install pytesseract`
- System dependency: Tesseract OCR binary
- Supported formats: PNG, JPG, JPEG
- Max file size: 10MB (configurable)

### 📋 card-013: Role-Based Authentication
**Status:** Backlog 📋  
**Priority:** High  
**Labels:** feature, security  
**Description:** Implement user login with email/password and role-based access (Admin, Compliance Officer, Developer, Researcher). Store hashed passwords in MongoDB.

**Acceptance Criteria:**
- [ ] User registration page with email/password
- [ ] Password hashing (bcrypt or argon2)
- [ ] Login page with authentication
- [ ] Session management
- [ ] Role assignment (Admin, Compliance Officer, Developer, Researcher)
- [ ] Role-based access control (RBAC)
- [ ] Protect sensitive pages based on role
- [ ] Store users collection in MongoDB
- [ ] Logout functionality
- [ ] Password reset flow (optional)

**Roles and Permissions:**
- **Admin:** Full access to all features, user management
- **Compliance Officer:** View/attest cards, export audit logs, view all data
- **Developer:** Create/edit pipeline cards, run jobs, view own data
- **Researcher:** Read-only access, can view anonymized outputs

### 📋 card-014: Compliance Review Notifications
**Status:** Backlog 📋  
**Priority:** Medium  
**Labels:** feature, compliance  
**Description:** Send email or in-app notifications 24 hours before scheduled review appointments. Include appointment details and linked pipeline card information.

**Acceptance Criteria:**
- [ ] Background notification service (daemon thread or scheduled job)
- [ ] Check appointments 24 hours in advance
- [ ] Send email notifications (SMTP integration)
- [ ] OR show in-app notifications (banner/toast)
- [ ] Notification includes: appointment title, time, description, linked card
- [ ] Mark notifications as sent (avoid duplicates)
- [ ] Configuration: SMTP settings in env vars
- [ ] Graceful failure if email service unavailable

**Technical Requirements:**
- Email backend: SMTP (smtplib) or SendGrid API
- Environment variables: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
- Notification scheduler: runs every hour
- Persistence: track notification_sent flag on appointments

**Integration with Existing Code:**
- Extends `scheduler.py` (appointment scheduler already exists)
- Use `store.list_appointments()` to find upcoming appointments
- Filter for appointments in 24-hour window
- Send notification and update appointment record

### 📋 card-015: File Attachments on Pipeline Cards
**Status:** Backlog 📋  
**Priority:** Medium  
**Labels:** feature, pipeline  
**Description:** Allow users to attach anonymized output files (CSV, TXT, JSON) to pipeline cards. Support multiple attachments per card with download capability.

**Acceptance Criteria:**
- [ ] Add "Attachments" section to pipeline card detail page
- [ ] File upload widget for attachments (multiple files)
- [ ] Support formats: CSV, TXT, JSON
- [ ] Store files: local filesystem or MongoDB GridFS
- [ ] Display attachment list on card (filename, size, upload date)
- [ ] Download button for each attachment
- [ ] Delete attachment capability
- [ ] Max file size limit (e.g., 50MB per file)
- [ ] Audit log: attachment.upload, attachment.delete events

**Technical Requirements:**
- Storage backend: filesystem (ANON_STORAGE path) or GridFS
- File metadata: store in PipelineCard.attachments (List[Dict])
- Each attachment: {filename, size, uploaded_at, stored_path, content_type}
- Download uses taipy.gui.download()

**Data Model Changes:**
```python
@dataclass
class PipelineCard:
    # ... existing fields ...
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    # Each dict: {"filename": str, "size": int, "uploaded_at": str, 
    #             "stored_path": str, "content_type": str}
```

---

## Additional Stories from Repository Memories

These stories were referenced in repository memories but don't have corresponding pipeline cards.

### 🔍 LOST: Export Functionality (Detailed Implementation)

**Status:** LOST 🔍 (mentioned in memories but not in code)  
**Evidence:** Repository memories cite specific implementation at:
- `app.py:5008-5072` (does not exist — app.py is 5409 lines)
- `app.py:4926-5040` (does not exist)
- `pages/definitions.py:593-602` (pages/definitions.py is 835 lines)
- `pages/definitions.py:503-511` (does not exist)
- `docs/export-functionality.md:1-300` (file does not exist)

**What Was Supposedly Implemented:**
1. Audit page export buttons (CSV, JSON)
2. Pipeline page export buttons (CSV, JSON)
3. Callback functions: on_audit_export_csv, on_audit_export_json
4. Callback functions: on_pipeline_export_csv, on_pipeline_export_json
5. Full audit trail logging for all exports
6. Success/error notifications

**Why This Matters:**
This suggests that either:
1. The implementation was in a branch that was never merged
2. The implementation was in commits that were lost during repo archiving
3. The memories are incorrect/outdated

**Recommended Action:**
Implement card-011 from scratch, using the memory details as design guidance.

---

## Summary Statistics

**Total Pipeline Cards:** 15
- ✅ Done: 6 (card-001, card-002, card-003, card-006, card-008, card-009, card-010)
- ⚠️ In Progress: 1 (card-007)
- 📋 Backlog: 5 (card-004, card-005, card-011, card-012, card-013, card-014, card-015)
- 🔍 Lost: 1 (Export functionality from card-011 may have been implemented but lost)

**Priority Breakdown:**
- Critical: 2 (1 done, 1 backlog)
- High: 3 (1 done, 2 backlog)
- Medium: 7 (3 done, 1 in progress, 3 backlog)
- Low: 3 (1 done, 2 backlog)

**Feature Categories:**
- Core PII Detection: 6 done
- Infrastructure: 1 done, 1 backlog
- Security: 1 in progress, 1 backlog
- Compliance: 2 backlog
- User Experience: 2 backlog

---

## Implementation Recommendations

### Immediate Priority (Next Sprint)
1. **card-007:** Complete encrypt operator (finish what's started)
2. **card-011:** Implement export functionality (LOST, needs recovery)
3. **card-013:** Role-based authentication (high security priority)

### Medium Priority (Sprint +1)
4. **card-014:** Compliance notifications (extends existing scheduler)
5. **card-015:** File attachments on cards (enhances workflow)
6. **card-004:** Patient records HIPAA (high priority use case)

### Low Priority (Future)
7. **card-012:** Image OCR (new capability)
8. **card-005:** Vendor contracts (low priority use case)

---

## Related Documentation

- **Feature Parity Tracking:** `docs/feature-parity.md`
- **Demo Cards Source:** `store/memory.py` lines 269-415
- **Store Interface:** `store/base.py`
- **Pipeline UI:** `pages/definitions.py`
- **App Callbacks:** `app.py`

---

## How to Use This Document

### For Project Managers
- Review backlog priorities
- Assign stories to sprints
- Track implementation status
- Update card statuses in `store/memory.py` when done

### For Developers
- Pick a backlog story to implement
- Follow acceptance criteria
- Update feature-parity.md when complete
- Change card status from "backlog" to "done"
- Add tests in `tests/` directory
- Document any new env vars in README

### For Compliance/Security
- Review high-priority security stories (card-007, card-013)
- Verify attestation requirements met (card-003 example)
- Ensure audit logging for all features (card-011, card-014)

---

## Appendix: Lost Implementation Recovery

### Export Functionality Pseudo-Code (Reconstructed from Memories)

Based on repository memories, here's what the lost export implementation might have looked like:

```python
# app.py - Audit page export callbacks

def on_audit_export_csv(state):
    """Export audit log to CSV file."""
    try:
        audit_entries = APP_CTX.store.list_audit()
        df = pd.DataFrame([
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "user": e.user,
                "details": e.details,
                "severity": e.severity,
            }
            for e in audit_entries
        ])
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        
        # Log export to audit trail
        APP_CTX.store.log_user_action("audit.export", "admin", "CSV export")
        
        # Trigger download
        download(state, content=csv_bytes, name="audit_log.csv")
        notify(state, "success", f"Exported {len(audit_entries)} audit entries to CSV")
    except Exception as e:
        notify(state, "error", f"Export failed: {e}")

def on_audit_export_json(state):
    """Export audit log to JSON file."""
    try:
        audit_entries = APP_CTX.store.list_audit()
        data = [
            {
                "timestamp": e.timestamp,
                "action": e.action,
                "user": e.user,
                "details": e.details,
                "severity": e.severity,
            }
            for e in audit_entries
        ]
        json_bytes = json.dumps(data, indent=2).encode('utf-8')
        
        APP_CTX.store.log_user_action("audit.export", "admin", "JSON export")
        download(state, content=json_bytes, name="audit_log.json")
        notify(state, "success", f"Exported {len(audit_entries)} audit entries to JSON")
    except Exception as e:
        notify(state, "error", f"Export failed: {e}")

def on_pipeline_export_csv(state):
    """Export all pipeline cards to CSV."""
    try:
        cards = APP_CTX.store.list_cards()
        df = pd.DataFrame([
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "assignee": c.assignee,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "attested": c.attested,
            }
            for c in cards
        ])
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        
        APP_CTX.store.log_user_action("pipeline.export", "admin", "CSV export")
        download(state, content=csv_bytes, name="pipeline_cards.csv")
        notify(state, "success", f"Exported {len(cards)} cards to CSV")
    except Exception as e:
        notify(state, "error", f"Export failed: {e}")

def on_pipeline_export_json(state):
    """Export all pipeline cards to JSON."""
    try:
        cards = APP_CTX.store.list_cards()
        data = [dataclasses.asdict(c) for c in cards]
        json_bytes = json.dumps(data, indent=2, default=str).encode('utf-8')
        
        APP_CTX.store.log_user_action("pipeline.export", "admin", "JSON export")
        download(state, content=json_bytes, name="pipeline_cards.json")
        notify(state, "success", f"Exported {len(cards)} cards to JSON")
    except Exception as e:
        notify(state, "error", f"Export failed: {e}")
```

```markdown
# pages/definitions.py - UI markup additions

# In AUDIT page, after the audit table:
<|Export|section|
<|Export CSV|button|on_action=on_audit_export_csv|>
<|Export JSON|button|on_action=on_audit_export_json|>
|>

# In PIPELINE page, after "All Cards" table:
<|Export Pipeline Data|section|
<|Export All CSV|button|on_action=on_pipeline_export_csv|>
<|Export All JSON|button|on_action=on_pipeline_export_json|>
|>
```

**Note:** This is reconstructed pseudo-code based on memory descriptions. The actual lost implementation may have differed.

---

**Document Maintenance:**
- Update this file when implementing backlog stories
- Mark stories as done when completed
- Add new stories to appropriate section
- Keep priority/status current
- Cross-reference with feature-parity.md

**Version History:**
- v1.0 (2026-03-06): Initial comprehensive inventory, identified lost export functionality
