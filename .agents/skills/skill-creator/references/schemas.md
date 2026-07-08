# Skill Evaluation Schemas

This document defines the schemas used by the Antigravity evaluation harness (`scripts/run_eval.py`) to run tests.

---

## 1. Trigger Evaluation Set Schema

Used to verify that a skill's description triggers the agent correctly when relevant, and does not trigger when irrelevant.

Save as `<skill-folder>/evals/trigger_eval.json` (or any path).

```json
[
  {
    "query": "I need to parse this PDF and find the invoice total",
    "should_trigger": true
  },
  {
    "query": "Print out a hello world program in python",
    "should_trigger": false
  }
]
```

### Fields:
* `query` (string): A realistic query, prompt, or command that a user might enter.
* `should_trigger` (boolean): `true` if this query should activate the skill (read `SKILL.md`); `false` otherwise.

---

## 2. Task Execution Evaluation Set Schema

Used to verify that a skill produces the correct outputs and follows structural workflows.

Save as `<skill-folder>/evals/task_eval.json` (or any path).

```json
{
  "skill_name": "pdf-parser",
  "evals": [
    {
      "id": 1,
      "prompt": "Parse the document at 'sample.pdf' and extract all table data to a markdown table.",
      "expected_output": "A markdown table containing invoice line items.",
      "expectations": [
        "Invoice",
        "Total Due",
        "|"
      ]
    }
  ]
}
```

### Fields:
* `skill_name` (string): The identifier of the skill being tested.
* `evals` (array): A list of test cases.
  * `id` (integer): A unique identifier for the test case.
  * `prompt` (string): The prompt to execute.
  * `expected_output` (string): Human-readable success criteria description.
  * `expectations` (array of strings): A list of substrings that MUST be present in the output for the test case to pass.
