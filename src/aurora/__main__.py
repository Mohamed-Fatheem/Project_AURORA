"""Command-line Stage 1 simulator."""

import argparse

from aurora.simulator import run, scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="AURORA synthetic observation simulator")
    parser.add_argument("--scenario", choices=scenarios(), required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--truth", action="store_true", help="include PRIVATE evaluation truth")
    args = parser.parse_args()
    trace, truth = run(scenarios()[args.scenario], args.seed)
    print(trace.to_json())
    if args.truth:
        print(f"SIMULATOR TRUTH—NOT AVAILABLE TO AGENT: {truth}")


if __name__ == "__main__":
    main()
