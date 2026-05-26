"""
Generate a random valid crossword grid and print it to stdout.

Wraps crossword.domain.grid_generator.GridGenerator, exposing every
constructor argument as a command-line option.

Usage:
    python3 tools/user/grid_generator.py -n 15 [--seed 42] [--min-black-pct 0.10]
                                              [--max-black-pct 0.20] [--max-attempts 256]
"""

import argparse
import sys

sys.path.insert(0, ".")
from crossword.domain.grid_generator import GeneratorSettings, GridGenerator


def main() -> None:
    """Parse CLI arguments, generate a grid, and print it."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-n",
        type=int,
        required=True,
        help="Grid size (odd integer >= 5)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    parser.add_argument(
        "--min-black-pct",
        type=float,
        default=GeneratorSettings.BLACK_CELL_PERCENT_MIN,
        help=f"Minimum fraction of black cells (default: {GeneratorSettings.BLACK_CELL_PERCENT_MIN})",
    )
    parser.add_argument(
        "--max-black-pct",
        type=float,
        default=GeneratorSettings.BLACK_CELL_PERCENT_MAX,
        help=f"Maximum fraction of black cells (default: {GeneratorSettings.BLACK_CELL_PERCENT_MAX})",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=GeneratorSettings.MAX_ITERATIONS,
        help=f"Number of top-level search attempts (default: {GeneratorSettings.MAX_ITERATIONS})",
    )
    args = parser.parse_args()

    generator = GridGenerator(
        n=args.n,
        seed=args.seed,
        min_black_pct=args.min_black_pct,
        max_black_pct=args.max_black_pct,
        max_attempts=args.max_attempts,
    )

    grid = generator.generate()
    if grid is None:
        print(f"Failed to generate a valid grid after {args.max_attempts} attempts.", file=sys.stderr)
        sys.exit(1)

    print(grid)


if __name__ == "__main__":
    main()
