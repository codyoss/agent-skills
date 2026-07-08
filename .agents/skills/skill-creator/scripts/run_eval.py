#!/usr/bin/env python3
"""
Automated Skill Evaluation Runner (Agnostic & Optimized for AGY)

Tests both skill triggering (trigger accuracy) and task execution (assertions).
"""

import os
import sys
import json
import re
import time
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_AGY_PATH = "/home/codyoss/.local/bin/agy"
DEFAULT_APP_DATA_DIR = "/home/codyoss/.gemini/antigravity-cli"

def get_conversation_id_from_log(log_content: str) -> str:
    """Parses the agy CLI log to extract the created conversation ID."""
    match = re.search(r"Created conversation ([a-f0-9-]+)", log_content)
    if match:
        return match.group(1)
    return ""

def load_transcript(app_data_dir: Path, conversation_id: str) -> list[dict]:
    """Loads the jsonl transcript file for the conversation."""
    transcript_path = app_data_dir / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    if not transcript_path.exists():
        return []
    
    steps = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    steps.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return steps

def check_skill_triggered(transcript: list[dict], skill_name: str) -> bool:
    """
    Checks if the skill was triggered during the conversation.
    A skill is triggered if the agent invoked view_file on the skill's SKILL.md.
    """
    skill_marker = f"{skill_name}/SKILL.md"
    for step in transcript:
        tool_calls = step.get("tool_calls", [])
        # Also check inside planner content just in case of formatting variations
        content = step.get("content", "")
        if skill_marker in content:
            # Check if view_file was called on the skill path
            for call in tool_calls:
                if call.get("name") == "view_file" or "view_file" in call.get("toolAction", "").lower():
                    args = call.get("parameters", {})
                    path = args.get("AbsolutePath", "") or args.get("Target", "")
                    if skill_name in path and "SKILL.md" in path:
                        return True
    return False

def run_single_eval_query(
    query: str,
    skill_name: str,
    agy_path: Path,
    app_data_dir: Path,
    run_id: str,
    results_dir: Path
) -> dict:
    """Runs a single query via agy and checks if the skill was triggered."""
    log_file = results_dir / f"run_{run_id}.log"
    cmd = [
        str(agy_path),
        "--dangerously-skip-permissions",
        "--log-file", str(log_file),
        "-p", query
    ]
    
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, timeout=180)
        stdout = result.stdout
        stderr = result.stderr
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return {
            "query": query,
            "error": "Timeout expired",
            "triggered": False,
            "elapsed_seconds": elapsed,
            "stdout": "",
            "stderr": ""
        }
    
    log_content = ""
    if log_file.exists():
        log_content = log_file.read_text(errors="replace")
    
    conversation_id = get_conversation_id_from_log(log_content)
    transcript = []
    triggered = False
    
    if conversation_id:
        transcript = load_transcript(app_data_dir, conversation_id)
        triggered = check_skill_triggered(transcript, skill_name)
    
    return {
        "query": query,
        "conversation_id": conversation_id,
        "triggered": triggered,
        "elapsed_seconds": elapsed,
        "stdout": stdout,
        "stderr": stderr,
        "transcript_length": len(transcript)
    }

def run_trigger_evaluation(
    eval_set: list[dict],
    skill_name: str,
    agy_path: Path,
    app_data_dir: Path,
    results_dir: Path,
    num_workers: int
) -> dict:
    """Runs parallel trigger evaluations."""
    print(f"Starting trigger evaluation for skill '{skill_name}' with {len(eval_set)} queries...")
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for idx, item in enumerate(eval_set):
            query = item["query"]
            should_trigger = item.get("should_trigger", True)
            future = executor.submit(
                run_single_eval_query,
                query,
                skill_name,
                agy_path,
                app_data_dir,
                f"trigger_{idx}",
                results_dir
            )
            futures[future] = item
        
        for future in as_completed(futures):
            item = futures[future]
            should_trigger = item.get("should_trigger", True)
            try:
                res = future.result()
                triggered = res["triggered"]
                passed = triggered == should_trigger
                res["should_trigger"] = should_trigger
                res["pass"] = passed
                results.append(res)
                status = "PASS" if passed else "FAIL"
                print(f"  [{status}] Should Trigger: {should_trigger} | Actually Triggered: {triggered} | Query: {res['query'][:60]}...")
            except Exception as e:
                print(f"  [ERROR] Running query: {item['query']} | Exception: {e}")
                results.append({
                    "query": item["query"],
                    "should_trigger": should_trigger,
                    "triggered": False,
                    "pass": not should_trigger,
                    "error": str(e)
                })

    passed_count = sum(1 for r in results if r.get("pass", False))
    total_count = len(results)
    
    return {
        "skill_name": skill_name,
        "type": "trigger",
        "results": results,
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": passed_count / total_count if total_count > 0 else 0.0
        }
    }

def run_task_evaluation(
    eval_set: list[dict],
    skill_name: str,
    agy_path: Path,
    app_data_dir: Path,
    results_dir: Path,
    num_workers: int
) -> dict:
    """Runs parallel task execution evaluations and evaluates expectations/assertions."""
    print(f"Starting task execution evaluation for skill '{skill_name}' with {len(eval_set)} test cases...")
    results = []
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for idx, item in enumerate(eval_set):
            prompt = item["prompt"]
            future = executor.submit(
                run_single_eval_query,
                prompt,
                skill_name,
                agy_path,
                app_data_dir,
                f"task_{idx}",
                results_dir
            )
            futures[future] = item
            
        for future in as_completed(futures):
            item = futures[future]
            expectations = item.get("expectations", [])
            try:
                res = future.result()
                stdout = res.get("stdout", "")
                
                # Check expectations against the stdout response (basic substring or regex matching)
                graded_expectations = []
                passed_expectations = 0
                for exp in expectations:
                    # Simple case-insensitive match
                    is_met = exp.lower() in stdout.lower()
                    graded_expectations.append({
                        "text": exp,
                        "passed": is_met,
                        "evidence": "Found in output" if is_met else "Not found in output"
                    })
                    if is_met:
                        passed_expectations += 1
                
                res["expectations"] = graded_expectations
                res["pass"] = len(expectations) == 0 or passed_expectations == len(expectations)
                res["expected_output"] = item.get("expected_output", "")
                results.append(res)
                
                status = "PASS" if res["pass"] else "FAIL"
                print(f"  [{status}] Checked {passed_expectations}/{len(expectations)} expectations | Prompt: {res['query'][:60]}...")
            except Exception as e:
                print(f"  [ERROR] Running prompt: {item['prompt']} | Exception: {e}")
                results.append({
                    "query": item["prompt"],
                    "pass": False,
                    "error": str(e)
                })
                
    passed_count = sum(1 for r in results if r.get("pass", False))
    total_count = len(results)
    
    return {
        "skill_name": skill_name,
        "type": "task",
        "results": results,
        "summary": {
            "total": total_count,
            "passed": passed_count,
            "failed": total_count - passed_count,
            "pass_rate": passed_count / total_count if total_count > 0 else 0.0
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Evaluate triggering and task execution for Antigravity Agent Skills")
    parser.add_argument("--eval-set", required=True, help="Path to evaluation JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to the skill directory")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of concurrent workers")
    parser.add_argument("--output", default="eval_results.json", help="Path to output JSON results file")
    parser.add_argument("--agy-path", default=DEFAULT_AGY_PATH, help="Path to agy executable")
    parser.add_argument("--app-data-dir", default=DEFAULT_APP_DATA_DIR, help="Path to App Data directory where brain transcripts are stored")
    args = parser.parse_args()
    
    eval_set_path = Path(args.eval_set)
    skill_path = Path(args.skill_path)
    agy_path = Path(args.agy_path)
    app_data_dir = Path(args.app_data_dir)
    
    if not eval_set_path.exists():
        print(f"❌ Error: Evaluation set not found at {eval_set_path}")
        sys.exit(1)
        
    if not skill_path.exists() or not (skill_path / "SKILL.md").exists():
        print(f"❌ Error: Invalid skill directory at {skill_path}")
        sys.exit(1)
        
    # Read eval set
    with open(eval_set_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
        
    skill_name = skill_path.name
    results_dir = Path("./eval_workspaces") / skill_name
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Check format of eval set to determine whether it is a trigger eval or task eval
    if isinstance(eval_data, list):
        # List of queries with should_trigger
        output = run_trigger_evaluation(eval_data, skill_name, agy_path, app_data_dir, results_dir, args.num_workers)
    elif isinstance(eval_data, dict) and "evals" in eval_data:
        # Task evaluations
        output = run_task_evaluation(eval_data["evals"], skill_name, agy_path, app_data_dir, results_dir, args.num_workers)
    else:
        print("❌ Error: Invalid evaluation JSON format. Must be a list of trigger queries or a dictionary with 'evals' key.")
        sys.exit(1)
        
    # Save output
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
        
    print(f"\n✅ Evaluation complete. Results saved to {output_path.resolve()}")
    summary = output["summary"]
    print(f"Summary: {summary['passed']}/{summary['total']} passed ({summary['pass_rate']:.1%})")

if __name__ == "__main__":
    main()
