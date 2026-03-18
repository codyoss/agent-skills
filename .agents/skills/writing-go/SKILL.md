---
name: writing-go
description: >
  Go (Golang) language expert enforcing Go best practices and standards. 
  Use when implementing Go features, scaffolding modules, or refactoring for idiomatic error handling and concurrency. 
  Don't use for non-Go code or general programming concepts.
metadata:
  version: 1.2.0
  author: "Cody Oss"
license: "MIT"
---

# Writing Go

This skill provides expert guidance for building idiomatic, high-performance Go applications. It transforms general coding requests into "The Go Way"—prioritizing simplicity, explicit error handling, and robust, table-driven testing.

## Core Principles

* **Simplicity > Cleverness**: If it's hard to read, it's not idiomatic.
* **Testing is Documentation**: Code and tests are a single unit of work.
* **Explicit is Better**: No hidden magic; handle every error and use clear variable naming.

## The Development Loop (Dev-Loop)

When asked to implement a feature or fix a bug, you must follow this lifecycle. Do not skip steps.

1. **Design & Types**: Define the structs and interfaces first. Data layout dictates algorithm structure.  
2. **Test Strategy**: Write a failing test, preferably a table-driven test style. See `references/table-driven-tests.md` for details.
3. **Implementation**: Write the code. Keep functions small. Handle errors immediately (no `_` for errors).  
4. **Verification**: Run tests and verify results. Run `go test ./...` 
5. **Refactor**: Run `goimports`. Check variable names (short names for small scopes).

## Critical Rules

> [!IMPORTANT]
> **Testing is Priority**: Never generate code without a corresponding `_test.go` file. All logic tests MUST use the table-driven pattern (see [table-driven-tests.md](file:///home/codyoss/workspace/agent-skills/.agents/skills/writting-go/references/table-driven-tests.md)).

> [!TIP]
> **Error Handling**: 
> * Return errors as the last return value.
> * Check if `err != nil` immediately.
> * Use `%w` to wrap errors when adding context.
> * **Never ignore go errors (`_ = ...`), even in tests.** The only exception is when using `defer`.

> [!NOTE]
> **Formatting & Concurrency**:
> * All code blocks MUST be syntactically correct (run `gofmt` equivalent).
> * Group imports: Standard lib, 3rd party, then local.
> * Share memory by communicating (channels); use `context.Context` for cancellation/timeouts.
> * Use `log/slog` for all logging; avoid `fmt.Print`.

## Common Tasks & Triggers

* **"Create a new module"**: Run the [scaffold.py](file:///home/codyoss/workspace/agent-skills/.agents/skills/writing-go/scripts/scaffold.py) script located in this skill folder.
* **"Add tests"**: Specifically look at the function signature and generate a table-driven test.
* **"Refactor"**: Look for long functions, global state, or lack of interfaces.

## Tooling & Setup

* **Linter**: Run `golangci-lint run ./...` for comprehensive static analysis.
* **Imports**: Use `goimports` to format and manage imports.
* **Project Layout**: Starts with a flat layout (`main.go` in root). Evolve to `cmd/`, `pkg/`, `internal/` only as complexity grows.

## References

For specific implementation details on testing and style, consult:

* [references/table-driven-tests.md](references/table-driven-tests.md)
* [references/best-practices.md](references/best-practices.md)