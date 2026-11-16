"""Ask for a paper backtest in one sentence."""

from __future__ import annotations

import argparse

from tradecopilot import __version__
from tradecopilot.engine import narrate, parse_request, run_backtest, synthetic_closes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tradecopilot",
        description="Turn a plain-English strategy into a paper backtest. Not financial advice.",
    )
    parser.add_argument("--version", action="version", version=f"tradecopilot {__version__}")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("request", nargs="*", help="Example: sma crossover fast 10 slow 30")
    return parser


def answer(text: str) -> str:
    spec = parse_request(text)
    result = run_backtest(synthetic_closes(), spec)
    return narrate(spec, result)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = "sma crossover fast 10 slow 30" if args.demo else " ".join(args.request)
    if not text:
        build_parser().print_help()
        return 0
    try:
        print(answer(text))
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
