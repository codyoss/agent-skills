---
name: subagent-orchestration
description: Guidelines and agent templates for orchestrating a TDD-driven, multi-subagent development and verification loop.
---

# TDD Multi-Subagent Orchestration Workflow

Use this skill when implementing complex coding tasks that benefit from test-driven design, parallel verification, and separation of concerns. The parent agent acts as the **Architect**, directing three specialized subagents.

---

## 1. Subagent Roles & Templates

### Phase 1: The Tester Subagent (TDD)
Before any implementation begins, spawn a subagent to write failing unit and/or integration tests.

- **Role Description**: `TDD Tester Subagent`
- **Subagent Type**: `self`
- **Prompt Template**:
  ```text
  You are the TDD Tester Subagent.
  Your task is to write failing unit and integration tests (TDD) for the feature: <FEATURE_NAME>.

  Requirements to test:
  <LIST_OF_REQUIREMENTS>

  Steps:
  1. If target packages/files/types do not exist yet, create basic skeletons or empty stubs so that the test code can compile.
  2. Write comprehensive unit tests in the appropriate `*_test.go` (or language-equivalent) files covering all happy paths and edge cases.
  3. Write integration or end-to-end tests that verify CLI flags, environment variables, and overall output formats.
  4. Run the test suite (e.g., `go test ./...`) and verify that compilation succeeds but the newly written tests FAIL.
  5. Report the failing test results back to the parent agent.
  ```

---

### Phase 2: The Feature Implementer Subagent
Once failing tests are confirmed, spawn a subagent to implement the logic.

- **Role Description**: `Feature Implementer`
- **Subagent Type**: `self`
- **Prompt Template**:
  ```text
  You are the Feature Implementer Subagent.
  Your task is to implement the feature <FEATURE_NAME> to satisfy all requirements and make all tests pass.

  Failing Tests context:
  <FAILING_TESTS_SUMMARY>

  Steps:
  1. Write the code implementing the feature in a clean, modular style. Avoid long inline anonymous functions or redundant comments.
  2. Ensure the code compiles and runs.
  3. Run the test suite (e.g., `go test ./...`) to ensure all tests (including the new TDD tests) pass successfully.
  4. Update all relevant design documents and user READMEs to match the new implementation.
  5. Send a message to the parent agent reporting your success.
  ```

---

### Phase 3: The Verifier Subagent
After the implementer reports success, spawn a separate verifier subagent with a fresh context to check the work against requirements.

- **Role Description**: `Verifier Subagent`
- **Subagent Type**: `self`
- **Prompt Template**:
  ```text
  You are the Verifier Subagent.
  Your task is to verify the implementation of <FEATURE_NAME> against its requirements.

  Steps:
  1. Inspect the codebase changes and the test coverage.
  2. Verify that all requirements are fully met and all edge cases (such as limits, invalid input validation, formatting) are handled.
  3. Inspect documentation updates in design documents and README files.
  4. Run the full test suite (e.g., `go test ./...` with cache disabled) to verify everything compiles and passes.
  5. Report your findings. Explicitly state if you give the implementation a "clean bill of health". If not, detail the exact failures or deficiencies.
  ```

---

## 2. Orchestration Guidelines for the Architect (Parent Agent)

1. **Maintain the Loop**:
   - Do not write the code or tests yourself. Direct the subagents to do it.
   - If the Verifier identifies gaps, feed them back to the Implementer and repeat the loop until the Verifier grants a "clean bill of health".
2. **Cleanup**:
   - Once a clean bill of health is achieved, terminate all spawned subagents (via `manage_subagents` with action `kill` or `kill_all`) to clean up resources before finishing the session.
3. **Commit & Push**:
   - Perform a final git status check, stage changes, and commit using conventional commit prefixes (e.g. `feat: ...`, `fix: ...`, `docs: ...`). Push the commits.
