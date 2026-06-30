"""
CLI: uv run python -m tests.simulation [--scenario SIM-01] [--verbose] [--all]

Runs one or all simulation scenarios and prints a transcript + summary.
"""

import argparse
import sys

from .scenarios import SCENARIOS, SCENARIOS_BY_ID
from .simulator import run_simulation

_USE_COLOR = sys.stdout.isatty()
def _c(code, t): return f"\033[{code}m{t}\033[0m" if _USE_COLOR else t
BOLD   = lambda t: _c("1",  t)
GREEN  = lambda t: _c("32", t)
YELLOW = lambda t: _c("33", t)
RED    = lambda t: _c("31", t)
DIM    = lambda t: _c("2",  t)

STOP_ICONS = {
    "resolved":  GREEN("✓ resolved"),
    "handover":  YELLOW("⬆ handover"),
    "user_done": GREEN("✓ user satisfied"),
    "max_turns": RED("⏱ max turns"),
}


def run_one(scenario: dict, verbose: bool) -> None:
    print(f"\n{BOLD('─' * 68)}")
    print(f"  {BOLD(scenario['id'])}  {scenario['title']}")
    print(f"  {DIM(scenario['persona'][:90])}…")
    print(BOLD('─' * 68))

    result = run_simulation(scenario, verbose=verbose)

    if not verbose:
        # Print compact transcript
        for t in result.turns:
            print(f"\n  {BOLD(f'Turn {t.index + 1}')}")
            print(f"  Customer : {t.user_msg}")
            print(f"  Bot      : {t.bot_response[:200]}{'…' if len(t.bot_response) > 200 else ''}")
            intents  = [f"{i['intent']}({i['status']})" for i in t.intents]
            tools    = [tc['tool_name'] for tc in t.tool_calls]
            flags    = []
            if t.requires_handover:      flags.append(RED("handover"))
            if t.awaiting_clarification: flags.append(YELLOW("awaiting"))
            meta = f"intents={intents}  tools={tools}"
            if flags: meta += "  " + " ".join(flags)
            print(f"  {DIM(meta)}")

    stop_icon = STOP_ICONS.get(result.stop_reason, result.stop_reason)
    print(f"\n  {stop_icon}  in {len(result.turns)} turns  (session {result.session_id[:8]}…)")


def main() -> None:
    parser = argparse.ArgumentParser(description="CS Chatbot multi-turn simulator")
    parser.add_argument("--scenario", help="Run a single scenario by ID, e.g. SIM-01")
    parser.add_argument("--all", action="store_true", help="Run all scenarios sequentially")
    parser.add_argument("--verbose", action="store_true", help="Print each turn as it happens")
    parser.add_argument("--base-url", default="http://localhost:8080", help="API base URL")
    args = parser.parse_args()

    import httpx
    try:
        httpx.get(f"{args.base_url}/health", timeout=5).raise_for_status()
    except Exception as e:
        print(RED(f"Server not reachable at {args.base_url}: {e}"))
        print("Run:  make run")
        sys.exit(1)

    if args.scenario:
        s = SCENARIOS_BY_ID.get(args.scenario)
        if not s:
            avail = list(SCENARIOS_BY_ID)
            print(RED(f"Unknown scenario '{args.scenario}'. Available: {avail}"))
            sys.exit(1)
        run_one(s, verbose=args.verbose)
    elif args.all:
        print(BOLD(f"\n  Running {len(SCENARIOS)} simulation scenarios"))
        summary = []
        for s in SCENARIOS:
            result = run_simulation(s, verbose=False)
            icon = STOP_ICONS.get(result.stop_reason, result.stop_reason)
            print(f"  {result.scenario_id:<8} {s['title']:<42} {icon}  ({len(result.turns)} turns)")
            summary.append(result)
        resolved = sum(1 for r in summary if r.resolved)
        print(f"\n  {GREEN(str(resolved))} / {len(summary)} resolved  "
              f"(stop reasons: { {r.stop_reason for r in summary} })")
    else:
        # Default: run SIM-01 as a quick demo
        run_one(SCENARIOS[0], verbose=args.verbose)
        print(DIM("\n  Tip: --all to run all scenarios, --scenario SIM-04 to pick one\n"))


if __name__ == "__main__":
    main()
