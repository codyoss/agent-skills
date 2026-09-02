---
name: writing-rust
description: >
  Rust language expert enforcing idiomatic Rust best practices, safety, error handling, and performance.
  Use when implementing Rust features, designing traits/types, writing async Tokio code, or working with Tauri v2 backends.
  Don't use for non-Rust code or general programming concepts.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# Writing Rust

This skill provides expert guidance for building idiomatic, high-performance, and type-safe Rust applications. It emphasizes robust error handling, minimal cloning, explicit ownership patterns, and structured concurrency.

## Core Principles

* **Explicit Ownership**: Design data structures around clear ownership hierarchies. Borrow when reading, take ownership only when storing or transforming.
* **Make Illegal States Unrepresentable**: Leverage algebraic data types (enums) and the type system to eliminate runtime errors at compile time.
* **Errors as Values**: Never panic in library or business logic. Treat every failure case as a typed `Result`.
* **Zero Warnings**: Treat compiler warnings and `clippy` lints as build-blocking errors.

## The Development Lifecycle

1. **Types & State Machine First**: Define structs, enums, and traits before writing functions. Model states explicitly as enums rather than boolean flags.
2. **Error Definitions**: Define domain errors using `thiserror` (see [references/error-handling.md](references/error-handling.md)).
3. **Implementation**: Implement logic with minimal allocations. Avoid premature `.clone()` calls.
4. **Verification & Testing**:
   - Write unit tests in `#[cfg(test)] mod tests` within the same file.
   - Write integration tests in `tests/`.
   - Run `cargo test --all-targets`.
5. **Linting & Formatting**:
   - Run `cargo clippy --all-targets --all-features -- -D warnings`.
   - Run `cargo fmt --check`.

## Critical Rules

> [!IMPORTANT]
> **No Unsafe Panics**:
> - Never use `.unwrap()` or `.expect()` in non-test production code unless preceded by an invariant proof comment.
> - Use the `?` operator, `unwrap_or_default()`, `ok_or_else()`, or exhaustive pattern matching instead.

> [!TIP]
> **Error Handling Pattern**:
> - **Domain / Internal Modules**: Use `thiserror` to define precise, strongly-typed error enums.
> - **Application / Top-Level CLI**: Use `anyhow::Result<T>` with `.context(...)` for rich error chains.
> - Detailed examples: see [references/error-handling.md](references/error-handling.md).

> [!NOTE]
> **Async & Concurrency**:
> - Use `tokio` for async runtimes.
> - Prefer channels (`tokio::sync::mpsc`, `broadcast`, `watch`) over shared mutable state.
> - When using `Arc<Mutex<T>>` or `Arc<RwLock<T>>`, keep locks short and avoid holding locks across `.await` points.
> - Detailed patterns: see [references/async-and-concurrency.md](references/async-and-concurrency.md).

## Tauri v2 Desktop Applications

When working in Tauri projects (e.g. `src-tauri`):
* **Commands**: Expose clean async IPC commands:
  ```rust
  #[tauri::command]
  pub async fn perform_action(
      state: tauri::State<'_, AppState>,
      payload: ActionPayload,
  ) -> Result<ActionResponse, String> {
      state.handle_action(payload).await.map_err(|e| e.to_string())
  }
  ```
* **State Management**: Wrap shared state in Tauri's managed state via `.manage(...)` during setup.

## References

* [references/error-handling.md](references/error-handling.md) — Idiomatic error modeling with `thiserror` and `anyhow`.
* [references/async-and-concurrency.md](references/async-and-concurrency.md) — Tokio async patterns, cancellation tokens, and channel architectures.
