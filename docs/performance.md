# Anonymous Studio — Performance Notes

This document describes the performance characteristics of the application, the
optimizations that have been applied, and guidance for operating the system at scale.

---

## Quick benchmarks (reference hardware: quad-core laptop, `en_core_web_lg`)

| Workload | Typical latency |
|----------|----------------|
| First `anonymize()` call after cold start | 4–8 s (spaCy model load) |
| Subsequent `anonymize()` calls (interactive text) | 15–80 ms |
| Batch row (pre-warmed engine, `fast=True`) | 10–40 ms / row |
| 10 k-row CSV, pandas backend, 500-row chunks | 3–8 min |
| 10 k-row CSV, Dask backend (`ANON_DASK_MIN_ROWS=10000`) | 2–5 min |
| Dashboard refresh (`_refresh_dashboard`) | < 50 ms in-memory store |

---

## Implemented optimizations

### 1. `OperatorConfig` dict caching (`pii_engine.py`)

**Problem:** `PIIEngine.anonymize()` is called once per cell during batch
processing. The original code rebuilt a dict of 17+ `OperatorConfig` objects on
every single call — ~170 000 object constructions for a 10 k-row, one-column file.

**Fix:** A module-level `_OPS_CACHE` dict (keyed by `(operator, entities_tuple)`)
stores the built dict after the first call. Every subsequent call with the same
operator and entity set is a single dict lookup.

```python
# pii_engine.py
_OPS_CACHE: Dict[tuple, Dict] = {}

def _get_ops(operator: str, entities_key: tuple) -> Dict:
    cache_key = (operator, entities_key)
    cached = _OPS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    # ... build ops dict once ...
    _OPS_CACHE[cache_key] = ops
    return ops
```

**Impact:** For a 10 k-row batch with `replace` operator and all 17 entities,
construction drops from ~170 000 calls to 1.

---

### 2. Compiled denylist regex caching (`pii_engine.py`)

**Problem:** `_denylist_results()` called `re.compile()` for every denylist term
on every `anonymize()` invocation. Compiling a regex is a non-trivial operation.

**Fix:** A module-level `_DENYLIST_PATTERN_CACHE` dict maps each term string to
its compiled `re.Pattern`. Patterns are compiled once and reused.

```python
_DENYLIST_PATTERN_CACHE: Dict[str, re.Pattern] = {}

def _denylist_results(text, denylist):
    for term in denylist:
        pat = _DENYLIST_PATTERN_CACHE.get(term)
        if pat is None:
            pat = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)
            _DENYLIST_PATTERN_CACHE[term] = pat
        ...
```

**Impact:** First use of each term compiles the pattern; every subsequent call is
a dict lookup + `pat.finditer()`.

---

### 3. `get_spacy_model_options()` cached with `@lru_cache` (`pii_engine.py`)

**Problem:** The spaCy model selector dropdown calls `get_spacy_model_options()`
on every render. Internally this calls `spacy.util.get_installed_models()`, which
scans the Python environment for installed packages.

**Fix:** `@lru_cache(maxsize=1)` on the function — the scan happens once per
process lifetime.

```python
@lru_cache(maxsize=1)
def get_spacy_model_options() -> List[str]:
    ...
```

**Note:** If you install a new spaCy model while the app is running, the dropdown
will not reflect it until the process is restarted. This is intentional — model
installs require a restart anyway.

---

### 4. `store.stats()` — eliminated flat entity list (`store/memory.py`)

**Problem:** The original implementation built a flat list by calling
`all_entities.extend([etype] * cnt)` for every entity type in every session, then
counted it with `len(all_entities)`. With many sessions or large entity counts this
list could grow to millions of entries.

**Fix:** Accumulate counts directly into a dict and sum them numerically:

```python
# Before (O(total_entities) memory)
all_entities.extend([etype] * cnt)
total = len(all_entities)

# After (O(distinct_entity_types) memory)
entity_freq[etype] = entity_freq.get(etype, 0) + cnt
total = sum(entity_freq.values())
```

Also replaced the two O(n) list comprehensions for `pipeline_by_status` and
`attested_cards` with a single pass over the cards dict.

---

### 5. Hoisted `store.list_sessions()` in `_refresh_dashboard()` (`app.py`)

**Problem:** The dashboard refresh function called `store.list_sessions()` three
times in a single execution:

1. Entity totals counter (line ~1511)
2. Windowed sessions for trend chart (line ~1673)
3. Timing-sessions for the Engine Performance panel (line ~1809)

Each call sorts the sessions dict — O(n log n) — and returns a new list.

**Fix:** One call at the top of `_refresh_dashboard()` stored in `_dash_sessions`,
reused by all three sections:

```python
st = store.stats()
_dash_sessions = store.list_sessions()   # hoist — reused below
...
for sess in _dash_sessions: ...          # entity chart
sessions = [s for s in _dash_sessions if _in_window(...)]  # trend
timing_sessions = [s for s in _dash_sessions if ...]       # perf panel
```

**Impact:** 3 × O(n log n) sort → 1 × O(n log n) sort per dashboard render.
Dashboard is refreshed on page load, on job completion, and on manual poll.

---

### 6. `_refresh_pipeline()` — eliminated second `store.list_cards()` call (`app.py`)

**Problem:** `_refresh_pipeline()` called `store.cards_by_status()` to populate the
four Kanban columns, then immediately called `store.list_cards()` again for the
all-cards flat view, picker, and burndown chart.

`cards_by_status()` already iterates every card; `list_cards()` re-sorts them.

**Fix:** Flatten the `cards_by_status()` result instead:

```python
by_s = store.cards_by_status()
all_cards = sorted(
    [c for cards in by_s.values() for c in cards],
    key=lambda c: c.updated_at, reverse=True,
)
```

**Impact:** Saves one full dict iteration + sort on every pipeline page render and
after every background job completion.

---

## Tuning knobs

### Batch job performance

| Env var | Default | Effect |
|---------|---------|--------|
| `ANON_JOB_COMPUTE_BACKEND` | `auto` | `pandas` · `dask` · `auto` |
| `ANON_DASK_MIN_ROWS` | `250000` | Row threshold above which `auto` switches to Dask |
| `ANON_DASK_BLOCKSIZE` | `32MB` | Dask CSV partition size |
| `ANON_WORKERS` | `1` | Worker subprocesses in `standalone` mode |

### Reducing per-call Presidio overhead

* **Entity selection:** pass only the entities you need rather than all 17.
  Presidio runs all recognizers for every entity in the list.
  ```python
  entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"]
  ```
* **`fast=True`:** skips `return_decision_process` in the analyzer — removes the
  per-span explanation object. Already set in `tasks.py::_anonymize_series`.
* **Score threshold:** raise `threshold` (default `0.35`) to `0.5`–`0.7` to skip
  low-confidence candidates. Fewer candidates → faster anonymizer pass.

### spaCy model choice

| Model | Size | NER quality | Speed |
|-------|------|-------------|-------|
| `en_core_web_sm` | 12 MB | Good | Fastest |
| `en_core_web_md` | 43 MB | Better | Fast |
| `en_core_web_lg` | 742 MB | Best (recommended) | Moderate |
| `en_core_web_trf` | ~500 MB | Highest | Slowest (GPU recommended) |
| Blank fallback | — | Regex only | Very fast |

Set via `SPACY_MODEL` env var or the model selector in the UI. The engine is
re-initialized on model switch; expect a 4–8 s pause on first use.

---

## Known remaining bottlenecks

| Area | Issue | Mitigation |
|------|-------|------------|
| `_refresh_dashboard()` | Still calls `store.list_audit(limit=1000)` and `store.list_appointments()` separately | Acceptable at demo scale; add hoisting if audit log grows large |
| `store.list_sessions()` | Sorted on every call (`O(n log n)`) | Switch to sorted-insert (e.g. `SortedList`) if session count exceeds ~10 k |
| `PROGRESS_REGISTRY` | In-process dict — invisible to Dask worker subprocesses in `standalone` mode | Use Redis or poll `job_stats` DataNode for real-time progress in multi-process deployments |
| spaCy model load | First call always slow (4–8 s); warm-up thread fires at import time but may race | Pre-warm by hitting the PII Text page once before submitting batch jobs |
| `_anonymize_series` | Still sequential (one Presidio call per cell) | Batch with `BatchAnonymizerEngine` or `concurrent.futures.ThreadPoolExecutor` for parallelism within a chunk |
