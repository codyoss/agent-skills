---
name: adversarial-testing
description: >
  Methodology and test harness patterns for writing adversarial stress tests, mock harnesses, and edge-case challengers.
  Use when auditing implementations, designing stress test suites, verifying race conditions, testing error recovery, or building rigorous verification loops.
  Don't use for simple unit test boilerplate.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# Adversarial Testing & Challenger Verification

This skill provides a systematic approach to adversarial verification: writing test harnesses that actively try to break code, expose race conditions, test boundary failure modes, and guarantee resilient error recovery.

## Core Mindset

* **Assume Code Will Fail**: Do not write tests just to confirm the happy path. Act as a hostile challenger finding edge cases, race conditions, memory leaks, and unhandled errors.
* **Hermetic & Deterministic**: Stress tests must run deterministically in isolated sandboxes without external network dependencies.
* **Clean State Recovery**: Systems must cleanly recover and report structured errors without panicking, hanging, or corrupting internal state.

## 4 Categories of Adversarial Tests

### 1. Concurrency & Race Condition Stress
* **Burst Testing**: Hammer endpoints/channels with rapid, concurrent requests (100–1000 tasks).
* **Rapid Cancellation**: Cancel tasks or drop channels immediately before, during, and after critical operations to ensure no deadlocks or leaked goroutines/threads.
* **Out-of-Order Execution**: Feed async events in unexpected order (e.g. stop event before start event, multiple duplicate initialization calls).

### 2. Malformed & Boundary Payloads
* **Empty / Extreme Inputs**: Test 0-byte streams, max-sized payloads, negative integers, null characters, deeply nested objects.
* **Corrupted Payloads**: Truncate JSON/Protobuf/audio streams halfway through transmission.
* **Encoding Faults**: Pass invalid UTF-8, unexpected content-types, or invalid header combinations.

### 3. Failure Injection & Mock Harms
* **Network & API Drops**: Use local mock servers (e.g. WireMock or fake local endpoints) to inject HTTP 500s, dropped sockets, latency spikes, and rate-limit headers (HTTP 429).
* **Filesystem & Permission Failures**: Mock or configure read-only filesystem paths, missing config directories, and unexpected file locks.

### 4. Crash Recovery & State Integrity
* **Persistence Under Crash**: Verify state files and keyrings retain integrity or safely roll back after simulated power cuts / interrupted writes.
* **Idempotency**: Repeated operations (retries) must yield identical state without side-effect accumulation.

## Workflow

1. **Audit Attack Surface**: Identify all I/O boundaries, concurrency locks, state transitions, and background loops.
2. **Design the Challenger Harness**: Write dedicated test files (e.g. `tests/adversarial_stress_tests.rs` or `cli_adversarial_test.go`).
3. **Execute & Stress**: Run tests under race detection (e.g. `go test -race` or `cargo test --test stress_suite`).
4. **Report & Harden**: Detail exact failure modes, stack traces, and remediations.

## References

* [references/test-patterns.md](references/test-patterns.md) — Code templates for Rust and Go stress harnesses, mock servers, and concurrency runners.
