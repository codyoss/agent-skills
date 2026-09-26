# Dependency Audit Guide

Use this reference during Pass 3 of a design review to systematically evaluate every dependency listed in a design document.

---

## Audit Process

For each dependency, answer these questions in order. Stop and flag the dependency as soon as you hit a failure condition.

### 1. Is it actually used?

Map every dependency to a specific implementation detail in the document. If you cannot find where it is used, flag it for removal.

> **Anti-pattern:** "We might need this later." If it has no concrete use in V1, cut it. It can always be added.

### 2. Does an existing dep already cover this?

Before accepting a dep, check whether any already-listed dependency provides the same capability — even as a secondary feature.

**Common overlap patterns:**
| Dep A (already listed) | Dep B (proposed) | Likely overlap |
|---|---|---|
| OpenAPI parser library | Separate JSON Schema validator | OpenAPI parsers often include schema validation |
| OpenAPI parser library | Separate JSON Schema serializer | OpenAPI schema types typically implement `json.Marshaler` |
| HTTP client library | Retry/backoff library | Most HTTP client libraries include retry logic |
| Full-featured CLI framework | Flag-parsing library | CLI frameworks include flag parsing |
| YAML config library | JSON config library | Most YAML libs handle JSON too (`gopkg.in/yaml.v3` does) |

**How to check:** Look at the dep's documentation for secondary features. Search for the function/method name you need — it may already exist in a dep you have.

### 3. Can the stdlib do it?

Before accepting any external dependency, ask if the standard library covers the need. Commonly covered by stdlib:

| Need | Go | Python | Node.js | Rust |
|---|---|---|---|---|
| HTTP client | `net/http` | `urllib.request` (most projects still add `requests`/`httpx`) | `fetch` (Node 18+) | ❌ needs `reqwest`/`ureq` |
| JSON | `encoding/json` | `json` | `JSON` | ❌ needs `serde_json` |
| File I/O / paths | `os`, `io`, `path/filepath` | `pathlib`, `shutil` | `fs`, `path` | `std::fs`, `std::path` |
| URL encoding | `net/url` | `urllib.parse` | `URL`, `URLSearchParams` | ❌ needs `url` |
| CLI flags | `flag` (basic) | `argparse` | `util.parseArgs` (Node 18.3+) | ❌ needs `clap` |
| Structured logging | `log/slog` | `logging` | ❌ (console only) | ❌ needs `tracing`/`log` |
| YAML | ❌ | ❌ | ❌ | ❌ |

### 4. Is it maintained?

Check for:
- Last commit date (>1 year stale = concern)
- Open issues vs. closed issues ratio
- Number of maintainers (single-maintainer projects carry bus-factor risk)
- Whether the library is widely adopted in the ecosystem

### 5. What does it bring transitively?

A dep with 10+ transitive dependencies adds supply-chain risk and build bloat. Prefer deps that are:
- Self-contained (no or few transitive deps)
- Explicit about what they pull in

---

## Decision Matrix

| Situation | Recommendation |
|---|---|
| Dep is unused in the design | ❌ Remove |
| Two deps cover the same concern | ❌ Remove the less capable one |
| Stdlib covers the need directly (same API surface, no glue code) | ❌ Remove; use stdlib |
| Stdlib covers it with ~20 lines of glue code | ⚠️ Consider removing; weigh against the dep's maintenance and supply-chain cost |
| Dep has no maintained alternative and provides real value | ✅ Keep |
| Dep is listed but its role is vague ("might be useful") | ⚠️ Require a concrete use case or remove |

---

## Common Mistakes

**Listing deps for social proof.** Some library names signal quality (e.g., "Robust HTTP client with retry logic"). Challenge the noun. Ask: "Does the design actually require retry logic? Is that scope?" If no, the dep is over-specced.

**Keeping two schema libraries.** It's common to add a dedicated schema validator when the parser library already validates. Always check the parser library first.

**Not listing a required dep.** Config parsing, YAML reading, and structured logging are commonly forgotten. After auditing for removals, do a forward pass: for every feature in the design, ask "what library does this?". If the answer isn't in the dep list, add it.

---

## Missing Dep Detection Checklist

Walk through the design and ask: "What library implements this?"

- [ ] Config file parsing (YAML/TOML/JSON) → often needs a dep
- [ ] Structured logging → check if there's a logging dep or if stdlib `log/slog` suffices
- [ ] CLI flag parsing → covered by CLI framework dep?
- [ ] HTTP client → covered by stdlib or explicit dep?
- [ ] JSON encode/decode → stdlib `encoding/json` (no dep needed)
- [ ] Schema validation → covered by OpenAPI parser or separate dep?
- [ ] Output filtering/transformation → jq or similar?
- [ ] Authentication token handling → custom or oauth2 library?
- [ ] File path expansion (`~`) → stdlib `os.UserHomeDir()` (no dep needed)
