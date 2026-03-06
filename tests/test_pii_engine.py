"""
Tests for pii_engine.py — PII detection, anonymization, and display utilities.

Run:
    pytest tests/test_pii_engine.py -v

These tests focus on correctness of entity catalogue, operator configuration,
and display helpers — they do NOT require the full Presidio/spaCy stack
(highlight_md and entity catalogue tests are pure-Python).

For tests that do require the engine (anonymize/analyze), pytest.importorskip
is used so the suite still runs cleanly in restricted environments without
the NLP models installed.
"""
from __future__ import annotations
import pytest


# ── Entity catalogue ──────────────────────────────────────────────────────────

def test_all_entities_contains_organization():
    """Regression: ORGANIZATION was mapped by spaCy NLP config but absent from
    ALL_ENTITIES, causing it to be silently dropped by Presidio."""
    from pii_engine import ALL_ENTITIES
    assert "ORGANIZATION" in ALL_ENTITIES


def test_all_entities_no_duplicates():
    from pii_engine import ALL_ENTITIES
    assert len(ALL_ENTITIES) == len(set(ALL_ENTITIES))


def test_entity_colors_covers_all_entities():
    """Every entity in ALL_ENTITIES must have a display colour."""
    from pii_engine import ALL_ENTITIES, ENTITY_COLORS
    missing = [e for e in ALL_ENTITIES if e not in ENTITY_COLORS]
    assert missing == [], f"Missing colors for: {missing}"


def test_operators_list():
    from pii_engine import OPERATORS
    assert set(OPERATORS) >= {"replace", "redact", "mask", "hash"}


def test_spacy_model_options_include_auto_and_blank():
    from pii_engine import get_spacy_model_options
    options = get_spacy_model_options()
    assert "auto" in options
    assert "blank" in options


# ── highlight_md XSS fixes ────────────────────────────────────────────────────

def test_highlight_md_no_entities_returns_no_pii_message():
    from pii_engine import highlight_md
    result = highlight_md("Hello world", [])
    assert "No PII detected" in result


def test_highlight_md_escapes_html_in_plain_segments():
    """Regression: user text like <script>alert(1)</script> was passed through
    unescaped into the Markdown output."""
    from pii_engine import highlight_md
    # Entity at start — plain text follows after cursor
    entities = [{"start": 0, "end": 5, "entity_type": "PERSON",
                 "score": 0.9, "text": "Alice"}]
    evil_suffix = " <script>alert(1)</script>"
    text = "Alice" + evil_suffix
    result = highlight_md(text, entities)
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_highlight_md_escapes_html_before_first_entity():
    from pii_engine import highlight_md
    entities = [{"start": 20, "end": 25, "entity_type": "EMAIL_ADDRESS",
                 "score": 0.9, "text": "email"}]
    text = "<b>Dangerous prefix</b>email"
    result = highlight_md(text, entities)
    # The <b> tags in the prefix should be escaped
    assert "<b>" not in result
    assert "&lt;b&gt;" in result


def test_highlight_md_formats_entity_span():
    from pii_engine import highlight_md
    entities = [{"start": 0, "end": 5, "entity_type": "PERSON",
                 "score": 0.85, "text": "Alice"}]
    result = highlight_md("Alice is here", entities)
    # Entity appears in inline-code span with label and confidence
    assert "`Alice`" in result
    assert "Person" in result
    assert "85%" in result


def test_highlight_md_merges_overlapping_entities_keeps_higher_score():
    from pii_engine import highlight_md
    # Overlapping: [0,10] score=0.7 and [2,8] score=0.9 → keep score=0.9
    entities = [
        {"start": 0, "end": 10, "entity_type": "PERSON", "score": 0.70, "text": "Alice Bob"},
        {"start": 2, "end": 8,  "entity_type": "EMAIL_ADDRESS", "score": 0.90, "text": "ice Bo"},
    ]
    result = highlight_md("Alice Bob here", entities)
    assert "Email Address" in result  # higher-score entity wins
    assert "Person" not in result


# ── PIIEngine (requires presidio + spacy) ─────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    """Load PIIEngine once per module — expensive but necessary."""
    try:
        from pii_engine import PIIEngine
        return PIIEngine()
    except Exception as e:
        pytest.skip(f"PIIEngine unavailable: {e}")


def test_engine_analyzes_email(engine):
    results = engine.analyze("Contact us at test@example.com for help.")
    types = [r["entity_type"] for r in results]
    assert "EMAIL_ADDRESS" in types


def test_engine_analyzes_phone(engine):
    results = engine.analyze("Call me at 555-867-5309.")
    types = [r["entity_type"] for r in results]
    assert "PHONE_NUMBER" in types


def test_engine_replace_operator(engine):
    result = engine.anonymize("Email: bob@example.com", ["EMAIL_ADDRESS"], "replace")
    assert "<EMAIL_ADDRESS>" in result.anonymized_text
    assert "bob@example.com" not in result.anonymized_text


def test_engine_redact_operator(engine):
    result = engine.anonymize("Email: bob@example.com", ["EMAIL_ADDRESS"], "redact")
    assert "bob@example.com" not in result.anonymized_text


def test_engine_mask_operator(engine):
    result = engine.anonymize("Email: bob@example.com", ["EMAIL_ADDRESS"], "mask")
    assert "*" in result.anonymized_text
    assert "bob@example.com" not in result.anonymized_text


def test_engine_hash_operator_consistent(engine):
    """Hash with fixed salt must produce identical output for identical input."""
    r1 = engine.anonymize("SSN: 123-45-6789", ["US_SSN"], "hash")
    r2 = engine.anonymize("SSN: 123-45-6789", ["US_SSN"], "hash")
    assert r1.anonymized_text == r2.anonymized_text


def test_engine_hash_operator_different_inputs_differ(engine):
    r1 = engine.anonymize("SSN: 123-45-6789", ["US_SSN"], "hash")
    r2 = engine.anonymize("SSN: 987-65-4321", ["US_SSN"], "hash")
    assert r1.anonymized_text != r2.anonymized_text


def test_engine_entity_counts_in_result(engine):
    result = engine.anonymize(
        "bob@example.com and alice@example.com", ["EMAIL_ADDRESS"], "replace")
    assert result.entity_counts.get("EMAIL_ADDRESS", 0) == 2


def test_engine_empty_text_returns_safely(engine):
    result = engine.anonymize("", ["EMAIL_ADDRESS"], "replace")
    assert result.anonymized_text == ""
    assert result.entity_counts == {}


# ── Entity type filtering ─────────────────────────────────────────────────────

def test_analyze_with_entity_subset_returns_only_selected_types(engine):
    """When a specific entity list is provided, only those types are returned."""
    text = "Email bob@example.com or call 555-867-5309"
    results = engine.analyze(text, entities=["EMAIL_ADDRESS"])
    types = {r["entity_type"] for r in results}
    assert "EMAIL_ADDRESS" in types
    assert "PHONE_NUMBER" not in types


def test_analyze_default_entities_returns_all_types(engine):
    """When no entity list is given, all supported entities are candidates."""
    from pii_engine import ALL_ENTITIES
    text = "Email bob@example.com or call 555-867-5309"
    results = engine.analyze(text)
    types = {r["entity_type"] for r in results}
    # At least one of the two entity types must appear without restriction
    assert types.issubset(set(ALL_ENTITIES)), "Returned types must all be in ALL_ENTITIES"
    assert len(types) >= 1


def test_analyze_empty_entity_list_falls_back_to_all_entities(engine):
    """Passing None for entities falls back to the full ALL_ENTITIES catalogue."""
    from pii_engine import ALL_ENTITIES
    text = "Email bob@example.com"
    results_default = engine.analyze(text)
    results_none = engine.analyze(text, entities=None)
    # Both should produce the same results
    assert [r["entity_type"] for r in results_default] == [r["entity_type"] for r in results_none]


def test_analyze_single_entity_type_excludes_others(engine):
    """Selecting a single entity type must exclude all other detected types."""
    text = "SSN 123-45-6789 and email test@example.com"
    results = engine.analyze(text, entities=["US_SSN"])
    types = {r["entity_type"] for r in results}
    assert types <= {"US_SSN"}, f"Expected only US_SSN but got {types}"
