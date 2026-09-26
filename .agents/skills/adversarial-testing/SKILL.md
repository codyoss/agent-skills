---
name: adversarial-testing
description: >
  Methodology and test harness patterns for writing adversarial stress tests, fuzz/property tests, mock fault-injection harnesses, and edge-case challengers.
  Use when auditing implementations, designing stress test suites, hunting race conditions or deadlocks, fuzzing parsers, testing error recovery, or building rigorous verification loops.
  Don't use for simple unit test boilerplate.
metadata:
  version: 1.1.0
  author: "Cody Oss"
license: "MIT"
---

# Adversarial Testing & Challenger Verification

This skill provides a systematic approach to adversarial verification: writing test harnesses that actively try to break code, expose race conditions, test boundary failure modes, and guarantee resilient error recovery.

## Core Mindset

* **Assume Code Will Fail**: Do not write tests just to confirm the happy path. Act as a hostile challenger finding edge cases, race conditions, leaks, and unhandled errors.
* **Hermetic**: No external network or shared machine state. Use local mock servers, temp dirs, and injected clocks.
* **Reproducible, not falsely deterministic**: Concurrency and fuzz tests explore nondeterministic schedules and inputs by design. Make every failure *reproducible* instead: log/fix the random seed, save failing fuzz inputs as regression cases, and repeat race tests many times (`-count=N`) rather than trusting one green run.
* **Every test has a deadline**: A deadlock must fail the test, not hang CI. Wrap every stress test in a timeout.
* **Clean State Recovery**: Systems must recover and report structured errors without panicking, hanging, leaking goroutines/tasks, or corrupting internal state.

## Choosing What to Attack

Don't apply every category to every target. Map the code's features to categories:

| If the code has… | Prioritize |
|---|---|
| Shared mutable state, locks, channels, background loops | 1. Concurrency |
| Parsers, decoders, deserializers, user/CLI input | 2. Malformed payloads + fuzzing |
| Network calls, filesystem, subprocesses | 3. Failure injection |
| Persistent state, retries, multi-step writes | 4. Crash recovery & idempotency |

## 5 Categories of Adversarial Tests

### 1. Concurrency & Race Condition Stress
* **Burst Testing**: Hammer endpoints/channels with rapid, concurrent requests (100–1000 tasks).
* **Rapid Cancellation**: Cancel tasks or drop channels before, *during*, and after critical operations. Assert no deadlocks and no leaked goroutines/tasks.
* **Out-of-Order Execution**: Feed async events in unexpected order (e.g. stop before start, duplicate initialization calls).

### 2. Malformed & Boundary Payloads
* **Empty / Extreme Inputs**: 0-byte streams, max-sized payloads, negative integers, null characters, deeply nested objects.
* **Corrupted Payloads**: Truncate JSON/Protobuf/binary streams halfway through.
* **Encoding Faults**: Invalid UTF-8, unexpected content-types, invalid header combinations.

### 3. Fuzzing & Property-Based Testing
Hand-picked edge cases only find the bugs you imagined. For any parser or pure transformation, add a fuzz or property test:
* **Go**: native fuzzing, `func FuzzX(f *testing.F)` + `go test -fuzz=FuzzX -fuzztime=60s`.
* **Rust**: `cargo fuzz` (libFuzzer) for parsers; `proptest` for properties.
* **Python**: `hypothesis`. **TypeScript**: `fast-check`.

Good properties: round-trip (`decode(encode(x)) == x`), never panics/throws an untyped error on any input, idempotency (`f(f(x)) == f(x)`), invariants preserved.

### 4. Failure Injection & Mock Harnesses
* **Network & API Drops**: Use local mock servers (`httptest` in Go, the `wiremock` crate in Rust, `respx`/`responses` in Python) to inject HTTP 500s, dropped sockets, latency spikes, and 429s with `Retry-After`.
* **Filesystem & Permission Failures**: Read-only paths, missing config directories, full disks (inject via an interface), and unexpected file locks.

### 5. Crash Recovery & State Integrity
* **Persistence Under Crash**: Verify state files retain integrity or roll back after interrupted writes (kill the writer mid-operation, or inject a failure between write and rename).
* **Idempotency**: Repeated operations (retries) must yield identical state without side-effect accumulation.

## Workflow

1. **Audit Attack Surface**: Identify I/O boundaries, concurrency primitives, state transitions, and background loops. Use the table above to pick categories.
2. **Design the Challenger Harness**: Write dedicated test files (e.g. `tests/adversarial_stress.rs`, `adversarial_test.go`) following the project's test conventions. Start from [references/test-patterns.md](references/test-patterns.md).
3. **Execute & Stress** with the right detector:
   * **Go**: `go test -race -count=20 -run 'Adversarial|Fuzz' ./...`, plus `goleak` for goroutine leaks.
   * **Rust**: `loom` to exhaustively permute interleavings of custom sync primitives; ThreadSanitizer (`RUSTFLAGS="-Zsanitizer=thread" cargo +nightly test -Zbuild-std --target <host-triple>`) for data races in `unsafe`/FFI code; `cargo +nightly miri test` for undefined behavior. Safe Rust can't data-race, so for async code focus on deadlocks, cancellation safety, and logic races under repeated runs.
   * **Python/Node**: repeat runs (`pytest --count=50` via `pytest-repeat`) with a per-test timeout (`pytest-timeout`).
4. **Report & Harden**: Don't modify production code unless the user asked for fixes. Report each finding in this format:

```markdown
### [Severity: Critical|High|Medium|Low] <one-line failure>
- **Test**: `path/to/test::name` (seed / fuzz corpus file if applicable)
- **Repro**: exact command
- **Observed**: panic / hang / corrupted state / leak, with the relevant stack trace excerpt
- **Root cause**: file:line and why it fails
- **Remediation**: concrete fix
```

Keep the failing tests in the suite (marked as known-failing if the project supports it) so the fix can be verified against them.

## References

* [references/test-patterns.md](references/test-patterns.md) — Code templates for Rust, Go, and Python stress harnesses, fuzz targets, mock servers, and leak checks.
