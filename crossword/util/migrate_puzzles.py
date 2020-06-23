""" Loads and then saves all puzzles
to ensure they are saved in the current JSON format """
import os

from crossword import Puzzle, Configuration


def puzzle_load(filename):
    with open(filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)
    return puzzle


def puzzle_save(filename, puzzle):
    with open(filename, "w") as fp:
        jsonstr = puzzle.to_json()
        fp.write(jsonstr)
    pass


def main(rootdir):
    nmigrated = 0
    for entryname in os.listdir(rootdir):
        filename = os.path.join(rootdir, entryname)
        puzzle = puzzle_load(filename)
        print(f"Converting {entryname}")
        puzzle_save(filename, puzzle)
        nmigrated += 1
    print(f"{nmigrated} puzzles migrated")


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    DEFAULT_ROOT = Configuration.get_puzzles_root()
    import argparse
    parser = argparse.ArgumentParser(description='Migrate puzzle data in a directory')
    parser.add_argument('-v', '--version', action='store_true', help='display version number')
    parser.add_argument('rootdir', nargs='?', default=DEFAULT_ROOT, help=f'Root directory name (default={DEFAULT_ROOT})')
    args = parser.parse_args()
    main(args.rootdir)
