# Hardcoded Value Audit (v2_anonymous-studio)

Date: 2026-03-05
Scope: full repository static scan for hardcoded secrets, infra/runtime constants, filesystem paths, and style literals.

## Summary

- Secrets detected: **none** (no API keys/private keys/token patterns found in source).
- Hardcoded runtime/config values detected: **yes**.
- Hardcoded style/theme literals detected: **yes** (substantial, mainly in CSS and chart config).
- Remediation status:
  - High finding #1: **fixed** (host/port now env-driven in `app.py`).
  - High finding #2: **fixed** (absolute `/tmp/...` defaults removed from code).

## Findings (ordered by severity)

### High

1. Hardcoded server bind host and port in runtime launch. **(Resolved)**
   - Previous location: `app.py` launch args.
   - Current: bind values are read from `TAIPY_HOST` and `TAIPY_PORT`/`PORT`.
   - Residual risk: if env vars are unset, Taipy defaults are used.

2. Hardcoded filesystem temp paths used as defaults. **(Resolved)**
   - Previous locations:
     - `core_config.py` `ANON_STORAGE` default `"/tmp/anon_studio"`
     - `pii_engine.py` blank fallback `"/tmp/anon_studio_blank_en"`
   - Current:
     - `ANON_STORAGE` default derived from `tempfile.gettempdir()`
     - blank fallback path uses `ANON_SPACY_BLANK_PATH` or `tempfile.gettempdir()`

### Medium

3. Hardcoded chart theme literals in code.
   - `app.py:282-291` (chart background/font/colorway/grid/hover colors)
   - Impact: visual behavior tied to source code, not centralized runtime config.
   - Recommended: move to config file/env-driven theme object and load once.

4. Hardcoded entity color map in PII engine.
   - `pii_engine.py:125-141` (`ENTITY_COLORS`)
   - `pii_engine.py:371` fallback color
   - Impact: color palette embedded in business-layer module.
   - Recommended: move to UI/theme config and pass in at render boundary.

5. Hardcoded inline style strings in highlight HTML renderer.
   - `pii_engine.py:359-385`
   - Impact: styling mixed into rendering logic, harder to theme/maintain.
   - Recommended: prefer CSS classes or template-based renderer.

### Low

6. Large volume of hardcoded CSS colors/values in stylesheet.
   - `app.css` (design tokens + direct hex usage throughout)
   - Impact: expected for static theme design, but still hardcoded.
   - Recommended: keep only token variables; reduce direct hex declarations outside `:root`.

7. Docs/examples include literal local URIs/paths.
   - `README.md:175`, `README.md:190`, `README.md:193`, `README.md:207`
   - `store/mongo.py:36`, `store/mongo.py:40`, `store/mongo.py:84`
   - `.env.example:31-33`
   - Impact: low; documentation examples are acceptable.

## Secret Scan Result

Pattern scan covered common token/key signatures (`AKIA`, `ghp_`, `sk-`, private key headers, Slack tokens, Mongo URI with creds format). No concrete credential strings were detected in tracked source files.

## Recommended Remediation Plan

1. Parameterize runtime bind:
   - Replace hardcoded host/port in `app.py` with env-backed values.
2. Parameterize filesystem defaults:
   - Remove `/tmp/...` literals from code paths; require env/config.
3. Centralize UI theme:
   - Move chart/colors/entity palette into one config module or TOML section.
4. Convert inline renderer styles:
   - Replace `style="..."` with classes or markdown-safe structured output.
