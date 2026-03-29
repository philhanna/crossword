"""
Rank puzzle slots by structural importance for fill order.

Usage:
    python tools/user/rank_fill_order.py <puzzle_name> [--user-id N] [--top N]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crossword import dbfile
from crossword.domain.fill_priority import FillPriorityAnalyzer
from crossword.ports.persistence_port import PersistenceError
from crossword.wiring import make_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank puzzle slots by structural importance for fill order."
    )
    parser.add_argument("name", help="Puzzle name")
    parser.add_argument("--user-id", type=int, default=1, help="Puzzle owner user id")
    parser.add_argument("--top", type=int, default=20, help="Maximum rows to print")
    return parser


def format_priority(priority) -> str:
    critical = "yes" if priority.critical else "no"
    return (
        f"{priority.location:<4} "
        f"score={priority.score:<3} "
        f"critical={critical:<3} "
        f"components={priority.component_count:<2} "
        f"sizes={list(priority.component_sizes)} "
        f"len={priority.length:<2} "
        f'text="{priority.text}"'
    )


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        app = make_app({"dbfile": dbfile()})
        puzzle = app.puzzle_uc.load_puzzle(args.user_id, args.name)
    except (PersistenceError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    analyzer = FillPriorityAnalyzer()
    priorities = analyzer.rank_slots(puzzle)

    print(f"Fill priority for puzzle '{args.name}':")
    for priority in priorities[:args.top]:
        print(format_priority(priority))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
