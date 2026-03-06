# Story Recovery Summary

This directory contains comprehensive documentation of all stories (pipeline cards and feature requests) for the Anonymous Studio project. This documentation was created to recover stories that may have been lost when the repository was archived.

## Quick Links

- **[Complete Story Inventory](all-stories.md)** — Detailed documentation of all 15 pipeline cards with acceptance criteria, implementation notes, and status
- **[GitHub Issues Templates](github-issues-template.md)** — Ready-to-use issue templates for creating GitHub issues for backlog stories
- **[Feature Parity Tracking](feature-parity.md)** — Comparison of v2 implementation vs. original PoC features

## What Was Found

### Total Stories: 15 Pipeline Cards

**✅ Done (6 stories):**
- card-001: Q1 Customer Export Anonymization
- card-002: HR Records PII Scrub
- card-003: Research Dataset Anonymization (attested)
- card-006: Allowlist / Denylist Support
- card-008: ORGANIZATION Entity Support
- card-009: REST API for PII Detection
- card-010: MongoDB Persistence Layer

**⚠️ In Progress (1 story):**
- card-007: Encrypt Operator Key Management (backend done, UI missing)

**📋 Backlog (5 stories):**
- card-004: Patient Records HIPAA Compliance
- card-005: Vendor Contract Data Review
- card-011: Export Audit Logs as CSV/JSON (**LOST IMPLEMENTATION**)
- card-012: Image PII Detection via OCR
- card-013: Role-Based Authentication
- card-014: Compliance Review Notifications
- card-015: File Attachments on Pipeline Cards

**🔍 Lost (1 story):**
- card-011 export functionality was supposedly implemented but code is missing from repository

## Critical Finding: Lost Export Functionality

**Story:** card-011 - Export Audit Logs as CSV/JSON

**Evidence of Loss:**
Repository memories from previous agent sessions referenced specific implementation locations:
- `app.py:5008-5072` — Export callback functions (DOES NOT EXIST)
- `pages/definitions.py:593-602` — Export UI buttons (DOES NOT EXIST)
- `docs/export-functionality.md` — Documentation (FILE DOES NOT EXIST)

**Current Reality:**
- `app.py` is only 5409 lines
- `pages/definitions.py` is only 835 lines
- No export functionality exists in the codebase

**Impact:**
This suggests that either:
1. The implementation was in a branch that was never merged
2. The code was lost during repository archiving (as mentioned in the issue)
3. The feature was never actually implemented (memories are incorrect)

**Recovery Action:**
See `all-stories.md` Appendix for reconstructed pseudo-code based on memory descriptions. The feature needs to be re-implemented from scratch.

## How to Use This Documentation

### For Project Managers
1. Review `all-stories.md` for complete story inventory
2. Check status summary above to understand what's done vs. backlog
3. Use `github-issues-template.md` to create GitHub issues for backlog items
4. Prioritize: card-013 (RBAC), card-011 (Export), card-007 (complete encrypt)

### For Developers
1. Pick a backlog story from `all-stories.md`
2. Review acceptance criteria and technical notes
3. Copy issue template from `github-issues-template.md`
4. Create GitHub issue or start implementation directly
5. Update card status in `store/memory.py` when done
6. Update `feature-parity.md` to reflect completion

### For Creating GitHub Issues
**Option 1: Manual (recommended for review)**
1. Open `github-issues-template.md`
2. Copy the issue template for your story
3. Go to https://github.com/cpsc4205-group3/anonymous-studio/issues/new
4. Paste title and body
5. Add labels manually

**Option 2: Automated (requires GitHub token)**
```bash
# Install PyGithub
pip install PyGithub

# Set your GitHub token
export GITHUB_TOKEN=ghp_your_token_here

# Dry run (see what would be created)
python scripts/create_github_issues.py --dry-run

# Actually create issues
python scripts/create_github_issues.py

# Or specify repo and token directly
python scripts/create_github_issues.py \
  --repo cpsc4205-group3/anonymous-studio \
  --token ghp_your_token_here
```

The script will:
- Create any missing labels (feature, security, compliance, ocr, pipeline)
- Create 6 GitHub issues (one for each backlog story)
- Print URLs to created issues
- Skip issues that already exist (by title match)

## Story Priority Recommendations

### Immediate (Next Sprint)
1. **card-007:** Complete Encrypt Operator (in progress, finish it)
2. **card-011:** Export Audit Logs (LOST, high compliance value)
3. **card-013:** Role-Based Authentication (security foundation)

### Medium Priority (Sprint +1)
4. **card-014:** Compliance Notifications (extends existing scheduler)
5. **card-015:** File Attachments (workflow improvement)
6. **card-004:** Patient HIPAA Records (high-value use case)

### Low Priority (Future)
7. **card-012:** Image OCR (new capability, requires Tesseract)
8. **card-005:** Vendor Contracts (low priority use case)

## File Organization

```
docs/
├── all-stories.md                  # Complete story inventory (main reference)
├── github-issues-template.md       # Copy-paste issue templates
├── feature-parity.md               # v2 vs. PoC feature comparison
├── STORY_RECOVERY_README.md        # This file
└── [other docs...]

scripts/
├── create_github_issues.py         # Automated issue creation
└── [other scripts...]

store/
└── memory.py                       # Demo cards source (lines 269-415)
```

## Verification Checklist

Use this to verify that all stories are accounted for:

- [x] card-001: Q1 Customer Export (status: review)
- [x] card-002: HR Records PII Scrub (status: in_progress)
- [x] card-003: Research Dataset (status: done, attested)
- [ ] card-004: Patient HIPAA (status: backlog)
- [ ] card-005: Vendor Contracts (status: backlog)
- [x] card-006: Allowlist/Denylist (status: done)
- [ ] card-007: Encrypt Operator (status: in_progress, needs completion)
- [x] card-008: ORGANIZATION Entity (status: done)
- [x] card-009: REST API (status: done)
- [x] card-010: MongoDB Persistence (status: done)
- [ ] card-011: Export Audit Logs (status: backlog, **LOST**)
- [ ] card-012: Image OCR (status: backlog)
- [ ] card-013: Role-Based Auth (status: backlog, HIGH priority)
- [ ] card-014: Notifications (status: backlog)
- [ ] card-015: File Attachments (status: backlog)

**Total:** 15 cards found and documented

## Additional Resources

- **Original PoC:** https://github.com/cpsc4205-group3/anonymous-studio (Streamlit demo)
- **Presidio Docs:** https://microsoft.github.io/presidio/
- **Taipy Docs:** https://docs.taipy.io/
- **spaCy Models:** https://spacy.io/models/en

## Investigation Timeline

- **2026-03-06:** Issue opened about lost stories
- **2026-03-06:** Investigation completed, 15 cards documented
- **2026-03-06:** Lost export functionality identified (card-011)
- **2026-03-06:** Comprehensive documentation created (this directory)

## Next Actions

1. **Immediate:** Review and approve this PR
2. **Create Issues:** Use `scripts/create_github_issues.py` or manual copy-paste
3. **Sprint Planning:** Prioritize card-007, card-011, card-013
4. **Re-implement card-011:** Use pseudo-code in `all-stories.md` as starting point
5. **Update Memories:** Store fact about card-011 being lost and needing re-implementation

## Questions?

If you have questions about any story:
1. Check `all-stories.md` for detailed acceptance criteria
2. Review `store/memory.py` lines 269-415 for demo card definitions
3. Check `feature-parity.md` for implementation status
4. Look at related test files in `tests/` for examples

## Maintenance

**When implementing a story:**
1. Update status in `store/memory.py` (e.g., `status="backlog"` → `status="done"`)
2. Update `feature-parity.md` to move from "Backlog" to "Done" section
3. Update `all-stories.md` to mark story as ✅ Done
4. Close the GitHub issue (if created)
5. Add tests in `tests/` directory

**Document Version:** 1.0 (2026-03-06)
