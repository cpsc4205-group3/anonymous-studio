#!/usr/bin/env python3
"""
Script to create GitHub issues for all backlog stories.

Usage:
    python scripts/create_github_issues.py --token YOUR_GITHUB_TOKEN

Or set GITHUB_TOKEN environment variable:
    export GITHUB_TOKEN=ghp_...
    python scripts/create_github_issues.py

Requirements:
    pip install PyGithub
"""

import argparse
import os
import sys
from typing import Dict, List

try:
    from github import Github, GithubException
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


# Issue definitions - each dict represents one GitHub issue
ISSUES = [
    {
        "title": "Complete Encrypt Operator Key Management",
        "body": """## Story: card-007 - Encrypt Operator Key Management

As a **compliance officer**, I want to **encrypt PII data reversibly** so that **I can decrypt it later if needed for authorized purposes**.

### Current Status
⚠️ **In Progress** — Backend supports encrypt/decrypt but UI and key management are missing.

### What's Already Implemented
- ✅ Presidio library supports encrypt/decrypt operators
- ✅ Backend infrastructure ready

### What's Missing
- ❌ UI operator selector doesn't include 'encrypt' option
- ❌ No UI field for encryption key input
- ❌ OperatorConfig("encrypt", {"key": key}) not implemented in pii_engine.py
- ❌ No env var (ANON_ENCRYPT_KEY) support
- ❌ No DeanonymizeEngine integration

### Acceptance Criteria
- [ ] Add 'encrypt' to operator selector dropdown in pages/definitions.py
- [ ] Add encrypted text input field for AES key (128/192/256-bit) on PII Text page
- [ ] Validate key length (16/24/32 characters) in UI callback
- [ ] Read ANON_ENCRYPT_KEY from environment as default key
- [ ] Implement OperatorConfig("encrypt", {"key": key}) in pii_engine.py
- [ ] Add DeanonymizeEngine.deanonymize() capability for decrypt
- [ ] Write test: encrypt "john@example.com" → decrypt → assert original
- [ ] Document key management in README.md (env vars, security warnings)

### Technical Notes
```python
# AES key requirements:
# - 128-bit: 16 characters
# - 192-bit: 24 characters  
# - 256-bit: 32 characters

# Example from Presidio docs:
from presidio_anonymizer import DeanonymizeEngine
from presidio_anonymizer.entities import OperatorResult, OperatorConfig

operators = {
    "EMAIL_ADDRESS": OperatorConfig("encrypt", {"key": "WmZq4t7w!z%C&F)J"}),
}

# Later, to decrypt:
deengine = DeanonymizeEngine()
original = deengine.deanonymize(
    text=anonymized_text,
    entities=[OperatorResult(start=..., end=..., entity_type="EMAIL_ADDRESS")],
    operators={"DEFAULT": OperatorConfig("decrypt", {"key": encryption_key})},
)
```

### Definition of Done
- [ ] Code merged to main
- [ ] Encrypt operator works in UI
- [ ] Key can be provided via UI or env var
- [ ] Encrypt/decrypt round-trip test passes
- [ ] README documents ANON_ENCRYPT_KEY
- [ ] No hardcoded keys in source code
- [ ] Card status updated to "done" in store/memory.py

### Related Files
- `pii_engine.py` — Add encrypt operator config
- `pages/definitions.py` — Add UI field for key
- `app.py` — Update operator callbacks
- `store/memory.py` — Update card-007 status
- `tests/test_pii_engine.py` — Add encrypt/decrypt test

### References
- PoC Feature: card-007 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
""",
        "labels": ["feature", "security", "in-progress"],
        "milestone": None,
    },
    {
        "title": "Export Audit Logs as CSV/JSON",
        "body": """## Story: card-011 - Export Audit Logs as CSV/JSON

As a **compliance officer**, I want to **export audit logs and pipeline data as CSV/JSON** so that **I can share compliance documentation with auditors**.

### Context
⚠️ **IMPORTANT:** Repository memories suggest this was implemented but the code is LOST. The implementation was supposedly at:
- `app.py:5008-5072` (doesn't exist)
- `pages/definitions.py:593-602` (doesn't exist)

We need to re-implement from scratch.

### Acceptance Criteria

#### Audit Page Export
- [ ] Add "Export" section after audit log table in pages/definitions.py
- [ ] Add "Export CSV" button → calls `on_audit_export_csv`
- [ ] Add "Export JSON" button → calls `on_audit_export_json`
- [ ] CSV format: columns for timestamp, action, user, details, severity
- [ ] JSON format: array of audit entry objects

#### Pipeline Page Export
- [ ] Add "Export Pipeline Data" section after "All Cards" table
- [ ] Add "Export All CSV" button → calls `on_pipeline_export_csv`
- [ ] Add "Export All JSON" button → calls `on_pipeline_export_json`
- [ ] CSV format: columns for id, title, status, priority, assignee, dates, attested
- [ ] JSON format: array of card objects

#### Implementation
- [ ] Use pandas.to_csv() for CSV generation
- [ ] Use json.dumps() for JSON generation (NO pickle)
- [ ] Use taipy.gui.download() to trigger browser download
- [ ] Log all exports to audit trail (audit.export, pipeline.export actions)
- [ ] Show success notification with count of exported records
- [ ] Show error notification on failure

### Tasks
1. Add export buttons to pages/definitions.py
2. Implement on_audit_export_csv callback in app.py
3. Implement on_audit_export_json callback in app.py
4. Implement on_pipeline_export_csv callback in app.py
5. Implement on_pipeline_export_json callback in app.py
6. Test with sample data
7. Update card-011 status to "done"

### Code Template
```python
from taipy.gui import download, notify
import pandas as pd
import json

def on_audit_export_csv(state):
    try:
        entries = APP_CTX.store.list_audit()
        df = pd.DataFrame([
            {"timestamp": e.timestamp, "action": e.action, 
             "user": e.user, "details": e.details, "severity": e.severity}
            for e in entries
        ])
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        APP_CTX.store.log_user_action("audit.export", "admin", "CSV export")
        download(state, content=csv_bytes, name="audit_log.csv")
        notify(state, "success", f"Exported {len(entries)} audit entries")
    except Exception as e:
        notify(state, "error", f"Export failed: {e}")

# Similar for JSON, pipeline CSV, pipeline JSON
```

### Definition of Done
- [ ] All 4 export buttons working
- [ ] CSV files download correctly
- [ ] JSON files download correctly  
- [ ] Audit trail logs each export
- [ ] Success/error notifications shown
- [ ] Tested with empty and populated datasets
- [ ] Card status updated to "done"

### Related Files
- `pages/definitions.py` — Add UI buttons
- `app.py` — Add 4 callback functions
- `store/memory.py` — Update card-011 status

### References
- PoC Feature: card-011 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
- Lost Implementation: See docs/all-stories.md Appendix
""",
        "labels": ["feature", "compliance"],
        "milestone": None,
    },
    {
        "title": "Image PII Detection via OCR",
        "body": """## Story: card-012 - Image PII Detection via OCR

As a **researcher**, I want to **detect PII in scanned documents and images** so that **I can anonymize visual data sources**.

### Description
Accept PNG/JPG uploads, extract text via Tesseract OCR, then apply Presidio PII detection to the extracted text. Display annotated results.

### Acceptance Criteria
- [ ] Add file upload widget for images on PII Text page
- [ ] Accept PNG, JPG, JPEG formats (max 10MB)
- [ ] Integrate pytesseract for OCR
- [ ] Extract text from uploaded image
- [ ] Pass extracted text to PIIEngine.analyze()
- [ ] Display OCR text with PII highlighting
- [ ] Show detected entities table
- [ ] Handle errors gracefully (invalid format, OCR failure)
- [ ] Document Tesseract installation in README

### Technical Requirements
- **Python library:** `pytesseract` (add to requirements.txt)
- **System dependency:** Tesseract OCR binary must be installed
  - Ubuntu/Debian: `apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download installer from GitHub
- **Supported formats:** PNG, JPG, JPEG
- **Max file size:** 10MB (configurable)

### Tasks
1. Add pytesseract to requirements.txt
2. Add image upload widget to PII Text page UI
3. Implement on_image_upload callback
4. Call pytesseract.image_to_string()
5. Pass OCR text to existing PII analysis flow
6. Display results (same as text input)
7. Add error handling for OCR failures
8. Document installation in README
9. Test with sample images (ID cards, forms, documents)
10. Update card-012 status to "done"

### Definition of Done
- [ ] pytesseract integrated
- [ ] Image upload works in UI
- [ ] OCR extracts text correctly
- [ ] PII detection works on OCR text
- [ ] Error messages clear and helpful
- [ ] README documents Tesseract installation
- [ ] Tested with 3+ different image types
- [ ] Card status updated to "done"

### Related Files
- `requirements.txt` — Add pytesseract
- `pages/definitions.py` — Add image upload widget
- `app.py` — Add on_image_upload callback
- `README.md` — Document Tesseract installation
- `store/memory.py` — Update card-012 status

### References
- PoC Feature: card-012 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
""",
        "labels": ["feature", "ocr"],
        "milestone": None,
    },
    {
        "title": "Role-Based Authentication",
        "body": """## Story: card-013 - Role-Based Authentication

As a **system administrator**, I want to **implement role-based access control** so that **users only access features appropriate to their role**.

### Description
Implement user login with email/password and role-based access (Admin, Compliance Officer, Developer, Researcher). Store hashed passwords in MongoDB.

### Roles and Permissions
- **Admin:** Full access, user management, all features
- **Compliance Officer:** View/attest cards, export audit logs, view all data
- **Developer:** Create/edit pipeline cards, run jobs, view own data
- **Researcher:** Read-only access, view anonymized outputs only

### Acceptance Criteria

#### User Management
- [ ] User registration page (email, password, role)
- [ ] Password hashing using bcrypt or argon2
- [ ] Store users in MongoDB collection
- [ ] User listing/editing for admins
- [ ] Disable/enable user accounts

#### Authentication
- [ ] Login page with email/password form
- [ ] Session management (secure cookies or JWT)
- [ ] Logout functionality
- [ ] Password reset flow (optional)
- [ ] Failed login attempt tracking

#### Authorization
- [ ] Role-based access control middleware
- [ ] Protect Pipeline page (Developer+ only)
- [ ] Protect Audit page (Compliance Officer+ only)
- [ ] Protect Schedule page (Compliance Officer+ only)
- [ ] Protect Settings (Admin only)
- [ ] Researcher: read-only mode on Dashboard/Jobs

#### Security
- [ ] HTTPS required (document in README)
- [ ] Secure session storage
- [ ] Password complexity requirements
- [ ] Account lockout after N failed attempts
- [ ] Audit log all login/logout events

### Tasks
1. Design MongoDB users schema
2. Implement user registration endpoint
3. Add password hashing (bcrypt)
4. Create login page UI
5. Implement authentication middleware
6. Add session management
7. Implement RBAC decorator for pages
8. Protect sensitive pages
9. Add logout functionality
10. Update navigation menu based on role
11. Write tests for auth flows
12. Document in README
13. Update card-013 status to "done"

### Definition of Done
- [ ] User registration/login working
- [ ] Passwords securely hashed
- [ ] Sessions managed properly
- [ ] RBAC enforced on all pages
- [ ] Admin can manage users
- [ ] Audit logs capture auth events
- [ ] Tests for all auth flows
- [ ] README documents setup
- [ ] Card status updated to "done"

### Related Files
- `store/models.py` — Add User dataclass
- `store/base.py` — Add user CRUD methods
- `store/mongo.py` — Implement user persistence
- `pages/definitions.py` — Add login/register pages
- `app.py` — Add auth callbacks and middleware
- `requirements.txt` — Add bcrypt
- `README.md` — Document auth setup
- `store/memory.py` — Update card-013 status

### References
- PoC Feature: card-013 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
""",
        "labels": ["feature", "security"],
        "milestone": None,
    },
    {
        "title": "Compliance Review Notifications",
        "body": """## Story: card-014 - Compliance Review Notifications

As a **compliance officer**, I want to **receive notifications before scheduled appointments** so that **I don't miss important compliance reviews**.

### Description
Send email or in-app notifications 24 hours before scheduled review appointments. Include appointment details and linked pipeline card information.

### Acceptance Criteria

#### Notification Scheduling
- [ ] Background service checks appointments every hour
- [ ] Identify appointments in 24-hour window (not yet notified)
- [ ] Send notification for each upcoming appointment
- [ ] Mark appointment as notified (avoid duplicates)

#### Email Notifications
- [ ] SMTP integration (smtplib or SendGrid)
- [ ] Email template with appointment details
- [ ] Include: title, time, description, linked card
- [ ] HTML email with nice formatting
- [ ] Fallback to plain text

#### In-App Notifications
- [ ] Show banner/toast for logged-in users
- [ ] Notification persists until acknowledged
- [ ] Click notification → navigate to appointment
- [ ] Notification center (optional)

#### Configuration
- [ ] SMTP settings via env vars
- [ ] Toggle email vs. in-app notifications
- [ ] Graceful failure if email unavailable
- [ ] Retry logic for transient failures

### Tasks
1. Extend scheduler.py with notification daemon
2. Add notification checking function
3. Implement email sender (SMTP)
4. Create email template
5. Add notification_sent flag to Appointment model
6. Update store methods for notification tracking
7. Add in-app notification UI (optional)
8. Add env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
9. Test with test appointments
10. Document in README
11. Update card-014 status to "done"

### Definition of Done
- [ ] Notification daemon running
- [ ] Emails sent 24h before appointments
- [ ] Notifications include all details
- [ ] No duplicate notifications
- [ ] Graceful failure handling
- [ ] SMTP settings documented
- [ ] Tested with test appointments
- [ ] Card status updated to "done"

### Related Files
- `scheduler.py` — Add notification checking
- `store/models.py` — Add notification_sent field to Appointment
- `store/base.py` — Update appointment methods
- `store/mongo.py` — Persist notification_sent
- `requirements.txt` — Add email dependencies if needed
- `README.md` — Document SMTP setup
- `.env.example` — Add SMTP vars
- `store/memory.py` — Update card-014 status

### References
- PoC Feature: card-014 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
- Integration: scheduler.py (appointment scheduler already exists)
""",
        "labels": ["feature", "compliance"],
        "milestone": None,
    },
    {
        "title": "File Attachments on Pipeline Cards",
        "body": """## Story: card-015 - File Attachments on Pipeline Cards

As a **developer**, I want to **attach anonymized output files to pipeline cards** so that **results are stored with their corresponding task**.

### Description
Allow users to attach anonymized output files (CSV, TXT, JSON) to pipeline cards. Support multiple attachments per card with download capability.

### Acceptance Criteria

#### UI
- [ ] Add "Attachments" section to card detail dialog
- [ ] File upload widget for attachments (multiple files)
- [ ] Display list of attachments (filename, size, date)
- [ ] Download button for each attachment
- [ ] Delete button for each attachment (with confirmation)

#### File Storage
- [ ] Store files in local filesystem (ANON_STORAGE path)
- [ ] OR store in MongoDB GridFS (configurable)
- [ ] Support formats: CSV, TXT, JSON
- [ ] Max file size: 50MB per file (configurable)
- [ ] Generate unique storage paths (avoid collisions)

#### Data Model
- [ ] Add `attachments` field to PipelineCard
- [ ] Store metadata: filename, size, uploaded_at, stored_path, content_type
- [ ] Update store methods to handle attachments

#### Audit Trail
- [ ] Log attachment.upload events
- [ ] Log attachment.delete events
- [ ] Include filename and card_id in audit details

### Tasks
1. Update PipelineCard model with attachments field
2. Add file upload widget to card dialog
3. Implement on_attachment_upload callback
4. Save file to storage (filesystem or GridFS)
5. Update card with attachment metadata
6. Add attachments list display in UI
7. Implement on_attachment_download callback
8. Implement on_attachment_delete callback
9. Add audit logging for attachments
10. Write tests for attachment CRUD
11. Document in README
12. Update card-015 status to "done"

### Definition of Done
- [ ] File upload works in card dialog
- [ ] Multiple files can be attached
- [ ] Attachments display correctly
- [ ] Download works for all formats
- [ ] Delete removes file and metadata
- [ ] Audit trail captures all actions
- [ ] Max file size enforced
- [ ] Tests for CRUD operations
- [ ] README documents storage config
- [ ] Card status updated to "done"

### Related Files
- `store/models.py` — Update PipelineCard with attachments field
- `store/base.py` — Add attachment helper methods
- `store/mongo.py` — Implement GridFS option
- `pages/definitions.py` — Add attachments UI to card dialog
- `app.py` — Add attachment callbacks
- `README.md` — Document attachment storage
- `.env.example` — Document storage options
- `store/memory.py` — Update card-015 status

### References
- PoC Feature: card-015 in store/memory.py
- Docs: docs/all-stories.md
- Feature Parity: docs/feature-parity.md
""",
        "labels": ["feature", "pipeline"],
        "milestone": None,
    },
]


def create_issues(repo_name: str, token: str, dry_run: bool = False) -> None:
    """Create GitHub issues from ISSUES list.
    
    Args:
        repo_name: Full repository name (e.g., "owner/repo")
        token: GitHub personal access token
        dry_run: If True, print what would be created without creating
    """
    print(f"Connecting to GitHub repository: {repo_name}")
    
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        print(f"✓ Connected to {repo.full_name}")
    except GithubException as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)
    
    # Get existing labels
    existing_labels = {label.name for label in repo.get_labels()}
    print(f"✓ Found {len(existing_labels)} existing labels")
    
    # Create missing labels
    required_labels = set()
    for issue_def in ISSUES:
        required_labels.update(issue_def["labels"])
    
    missing_labels = required_labels - existing_labels
    if missing_labels:
        print(f"Creating {len(missing_labels)} missing labels...")
        for label_name in missing_labels:
            if not dry_run:
                try:
                    repo.create_label(
                        name=label_name,
                        color="0366d6",  # Default blue
                        description=f"Auto-created for backlog stories"
                    )
                    print(f"  ✓ Created label: {label_name}")
                except GithubException as e:
                    print(f"  ✗ Failed to create label '{label_name}': {e}")
            else:
                print(f"  [DRY RUN] Would create label: {label_name}")
    
    # Create issues
    print(f"\nCreating {len(ISSUES)} issues...")
    created_count = 0
    
    for i, issue_def in enumerate(ISSUES, 1):
        title = issue_def["title"]
        body = issue_def["body"]
        labels = issue_def["labels"]
        milestone = issue_def.get("milestone")
        
        if dry_run:
            print(f"\n[{i}/{len(ISSUES)}] [DRY RUN] Would create issue:")
            print(f"  Title: {title}")
            print(f"  Labels: {', '.join(labels)}")
            print(f"  Body length: {len(body)} characters")
        else:
            try:
                issue = repo.create_issue(
                    title=title,
                    body=body,
                    labels=labels,
                    milestone=milestone,
                )
                print(f"\n[{i}/{len(ISSUES)}] ✓ Created: #{issue.number} - {title}")
                print(f"  URL: {issue.html_url}")
                created_count += 1
            except GithubException as e:
                print(f"\n[{i}/{len(ISSUES)}] ✗ Failed to create '{title}': {e}")
    
    if dry_run:
        print(f"\n[DRY RUN] Would have created {len(ISSUES)} issues")
    else:
        print(f"\n✓ Successfully created {created_count}/{len(ISSUES)} issues")


def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub issues for Anonymous Studio backlog stories"
    )
    parser.add_argument(
        "--repo",
        default="cpsc4205-group3/anonymous-studio",
        help="GitHub repository (owner/repo)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be created without actually creating",
    )
    
    args = parser.parse_args()
    
    if not args.token:
        print("ERROR: GitHub token required. Provide via --token or GITHUB_TOKEN env var")
        print("\nTo create a token:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Click 'Generate new token (classic)'")
        print("3. Select scopes: 'repo' (all)")
        print("4. Generate and copy the token")
        sys.exit(1)
    
    create_issues(args.repo, args.token, args.dry_run)


if __name__ == "__main__":
    main()
