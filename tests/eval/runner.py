"""
Evaluation runner for the CS Chatbot POC.

Runs test cases against the live API and produces a structured report.

Usage:
    # Run all cases
    uv run python tests/eval/runner.py

    # Run a specific category
    uv run python tests/eval/runner.py --category order_tracking

    # Run a specific case
    uv run python tests/eval/runner.py --case OT-01

    # Save JSON report
    uv run python tests/eval/runner.py --output results/eval_report.json

    # Verbose — print full response text for each turn
    uv run python tests/eval/runner.py --verbose
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: uv add httpx --dev")
    sys.exit(1)

from .cases import ALL_CASES, CASES_BY_CATEGORY

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8080"
REQUEST_TIMEOUT = 60.0
DELAY_BETWEEN_TURNS = 0.3   # seconds, to avoid hammering

# ── Colours (ANSI, skipped on non-TTY) ───────────────────────────────────────
_USE_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

GREEN  = lambda t: _c("32", t)
RED    = lambda t: _c("31", t)
YELLOW = lambda t: _c("33", t)
BOLD   = lambda t: _c("1",  t)
DIM    = lambda t: _c("2",  t)

# ── Check helpers ─────────────────────────────────────────────────────────────

def _check_turn(turn_expected: dict, api_response: dict) -> list[str]:
    """Return a list of failure messages. Empty list = all checks passed."""
    failures = []
    exp = turn_expected

    # awaiting_clarification
    if "awaiting_clarification" in exp:
        got = api_response.get("awaiting_clarification", False)
        if got != exp["awaiting_clarification"]:
            failures.append(
                f"awaiting_clarification: expected {exp['awaiting_clarification']}, got {got}"
            )

    # requires_handover
    if "requires_handover" in exp:
        got = api_response.get("requires_handover", False)
        if got != exp["requires_handover"]:
            failures.append(
                f"requires_handover: expected {exp['requires_handover']}, got {got}"
            )

    # intents — check each expected intent appears (by intent name and optional status)
    if "intents" in exp:
        actual_intents = {i["intent"]: i for i in api_response.get("intents", [])}
        for ei in exp["intents"]:
            intent_name = ei["intent"]
            if intent_name not in actual_intents:
                failures.append(f"intent '{intent_name}' not detected (got: {list(actual_intents)})")
            elif "status" in ei:
                got_status = actual_intents[intent_name].get("status", "")
                if got_status != ei["status"]:
                    failures.append(
                        f"intent '{intent_name}' status: expected '{ei['status']}', got '{got_status}'"
                    )

    # entities_contain — check specific entity values
    if "entities_contain" in exp:
        all_entities: dict[str, str] = {}
        for intent in api_response.get("intents", []):
            all_entities.update(intent.get("entities", {}))
        for k, v in exp["entities_contain"].items():
            if all_entities.get(k, "").upper() != v.upper():
                failures.append(
                    f"entity '{k}': expected '{v}', got '{all_entities.get(k, '<missing>')}'"
                )

    # tool_calls — check all expected tool names were called
    if "tool_calls" in exp:
        actual_tools = [
            tc["tool_name"]
            for tc in (api_response.get("turn_debug") or {}).get("tool_calls", [])
        ]
        for tool in exp["tool_calls"]:
            if tool not in actual_tools:
                failures.append(f"tool '{tool}' not called (called: {actual_tools})")

    # response_contains — case-insensitive substring check
    if "response_contains" in exp:
        response = api_response.get("response", "")
        for fragment in exp["response_contains"]:
            if fragment.lower() not in response.lower():
                failures.append(f"response_contains: '{fragment}' not found in response")

    # response_not_contains — should NOT appear in response
    if "response_not_contains" in exp:
        response = api_response.get("response", "")
        for fragment in exp["response_not_contains"]:
            if fragment.lower() in response.lower():
                failures.append(f"response_not_contains: '{fragment}' found in response")

    return failures


# ── Runner ────────────────────────────────────────────────────────────────────

class TurnResult:
    def __init__(self, turn_idx: int, user_msg: str, api_response: dict | None,
                 failures: list[str], error: str | None, latency_ms: float):
        self.turn_idx = turn_idx
        self.user_msg = user_msg
        self.api_response = api_response
        self.failures = failures
        self.error = error
        self.latency_ms = latency_ms

    @property
    def passed(self) -> bool:
        return not self.failures and self.error is None


class CaseResult:
    def __init__(self, case: dict, turn_results: list[TurnResult]):
        self.case = case
        self.turn_results = turn_results

    @property
    def passed(self) -> bool:
        return all(t.passed for t in self.turn_results)

    @property
    def total_latency_ms(self) -> float:
        return sum(t.latency_ms for t in self.turn_results)

    def to_dict(self) -> dict:
        return {
            "id": self.case["id"],
            "category": self.case["category"],
            "description": self.case["description"],
            "passed": self.passed,
            "total_latency_ms": round(self.total_latency_ms, 1),
            "turns": [
                {
                    "turn": t.turn_idx + 1,
                    "user": t.user_msg,
                    "passed": t.passed,
                    "failures": t.failures,
                    "error": t.error,
                    "latency_ms": round(t.latency_ms, 1),
                    "response": (t.api_response or {}).get("response", ""),
                    "intents": (t.api_response or {}).get("intents", []),
                    "tool_calls": ((t.api_response or {}).get("turn_debug") or {}).get("tool_calls", []),
                    "awaiting_clarification": (t.api_response or {}).get("awaiting_clarification", False),
                    "requires_handover": (t.api_response or {}).get("requires_handover", False),
                }
                for t in self.turn_results
            ],
        }


def run_case(client: httpx.Client, case: dict, verbose: bool = False) -> CaseResult:
    session_id = str(uuid.uuid4())
    turn_results: list[TurnResult] = []

    for i, turn in enumerate(case["turns"]):
        user_msg = turn["user"]
        expected = turn.get("expected", {})

        t0 = time.perf_counter()
        api_response = None
        error = None
        try:
            resp = client.post(
                "/chat",
                json={"message": user_msg, "session_id": session_id},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            api_response = resp.json()
            session_id = api_response.get("session_id", session_id)
        except httpx.HTTPStatusError as e:
            error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        except httpx.RequestError as e:
            error = f"Request error: {e}"
        latency_ms = (time.perf_counter() - t0) * 1000

        failures = _check_turn(expected, api_response or {}) if not error else []
        tr = TurnResult(i, user_msg, api_response, failures, error, latency_ms)
        turn_results.append(tr)

        if verbose and api_response:
            intent_names = [x["intent"] for x in api_response.get("intents", [])]
            tools = [tc["tool_name"] for tc in (api_response.get("turn_debug") or {}).get("tool_calls", [])]
            print(DIM(f"      Turn {i+1}: intents={intent_names}  tools={tools}  {latency_ms:.0f}ms"))
            print(DIM(f"      Bot: {api_response.get('response','')[:120]}…"))

        if i < len(case["turns"]) - 1:
            time.sleep(DELAY_BETWEEN_TURNS)

    return CaseResult(case, turn_results)


# ── Report ────────────────────────────────────────────────────────────────────

def print_report(results: list[CaseResult]) -> None:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_lat = sum(r.total_latency_ms for r in results) / max(total, 1)

    print()
    print(BOLD("─" * 72))
    print(BOLD(f"  Results: {GREEN(str(passed)+' passed')}  {RED(str(failed)+' failed')}  / {total} total   avg {avg_lat:.0f}ms/case"))
    print(BOLD("─" * 72))

    # Category breakdown
    by_cat: dict[str, list[CaseResult]] = {}
    for r in results:
        cat = r.case["category"]
        by_cat.setdefault(cat, []).append(r)

    print()
    print(BOLD(f"  {'Category':<25} {'Pass':>5}  {'Fail':>5}  {'Cases':>6}"))
    print("  " + "─" * 48)
    for cat, cat_results in by_cat.items():
        p = sum(1 for r in cat_results if r.passed)
        f = len(cat_results) - p
        bar = GREEN("●") * p + RED("○") * f
        print(f"  {cat:<25} {GREEN(str(p)):>5}  {RED(str(f)) if f else DIM('0'):>5}  {len(cat_results):>6}  {bar}")

    # Failed case details
    failed_results = [r for r in results if not r.passed]
    if failed_results:
        print()
        print(BOLD(f"  Failed cases ({len(failed_results)}):"))
        for r in failed_results:
            print(f"\n  {RED('✗')} {BOLD(r.case['id'])}  {DIM(r.case['description'])}")
            for tr in r.turn_results:
                if not tr.passed:
                    prefix = f"    Turn {tr.turn_idx+1}:"
                    if tr.error:
                        print(f"  {prefix} {RED('ERROR')} — {tr.error}")
                    for fail in tr.failures:
                        print(f"  {prefix} {YELLOW(fail)}")
    print()


def save_report(results: list[CaseResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / max(total, 1) * 100, 1),
            "avg_latency_ms": round(sum(r.total_latency_ms for r in results) / max(total, 1), 1),
        },
        "by_category": {
            cat: {
                "total": len(cr),
                "passed": sum(1 for r in cr if r.passed),
            }
            for cat, cr in {
                c: [r for r in results if r.case["category"] == c]
                for c in dict.fromkeys(r.case["category"] for r in results)
            }.items()
        },
        "cases": [r.to_dict() for r in results],
    }
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"  Report saved → {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="CS Chatbot eval runner")
    parser.add_argument("--category", help="Run only cases in this category")
    parser.add_argument("--case", help="Run only this case ID (e.g. OT-01)")
    parser.add_argument("--output", help="Save JSON report to this path")
    parser.add_argument("--verbose", action="store_true", help="Print response text per turn")
    parser.add_argument("--base-url", default=API_BASE, help="API base URL")
    args = parser.parse_args()

    base_url = args.base_url

    # Select cases
    if args.case:
        cases = [c for c in ALL_CASES if c["id"] == args.case]
        if not cases:
            print(f"Case '{args.case}' not found.")
            sys.exit(1)
    elif args.category:
        cases = CASES_BY_CATEGORY.get(args.category, [])
        if not cases:
            avail = list(CASES_BY_CATEGORY)
            print(f"Category '{args.category}' not found. Available: {avail}")
            sys.exit(1)
    else:
        cases = ALL_CASES

    # Health check
    try:
        r = httpx.get(f"{base_url}/health", timeout=5.0)
        r.raise_for_status()
    except Exception as e:
        print(RED(f"Cannot reach {base_url}/health: {e}"))
        print("Start the server first:  make run")
        sys.exit(1)

    total_turns = sum(len(c["turns"]) for c in cases)
    print(BOLD(f"\n  CS Chatbot Eval — {len(cases)} cases, {total_turns} turns"))
    print(f"  Server: {base_url}")
    print(f"  {'─' * 60}")

    results: list[CaseResult] = []
    with httpx.Client(base_url=base_url) as client:
        for case in cases:
            icon = "  "
            result = run_case(client, case, verbose=args.verbose)
            icon = GREEN("✓") if result.passed else RED("✗")
            lat = f"{result.total_latency_ms:.0f}ms"
            desc_width = 46
            desc = case["description"]
            if len(desc) > desc_width:
                desc = desc[:desc_width - 1] + "…"
            print(f"  {icon}  {BOLD(case['id']):<8} {desc:<{desc_width}} {DIM(lat)}")
            results.append(result)

    print_report(results)

    if args.output:
        save_report(results, Path(args.output))

    # Exit non-zero if any failures
    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
