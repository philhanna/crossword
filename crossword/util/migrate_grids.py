""" Loads and then saves all grids
to ensure they are saved in the current JSON format """
import os

from crossword import Configuration, Grid


def grid_load(filename):
    with open(filename) as fp:
        jsonstr = fp.read()
    grid = Grid.from_json(jsonstr)
    return grid


def grid_save(filename, grid):
    with open(filename, "w") as fp:
        jsonstr = grid.to_json()
        fp.write(jsonstr)
    pass


def main(rootdir):
    nmigrated = 0
    for entryname in os.listdir(rootdir):
        filename = os.path.join(rootdir, entryname)
        grid = grid_load(filename)
        print(f"Converting {entryname}")
        grid_save(filename, grid)
        nmigrated += 1
    print(f"{nmigrated} grids migrated")


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    DEFAULT_ROOT = Configuration.get_grids_root()
    import argparse
    parser = argparse.ArgumentParser(description='Migrate all grid data in a directory')
    parser.add_argument('rootdir', nargs='?', default=DEFAULT_ROOT, help=f'Root directory name (default={DEFAULT_ROOT})')
    args = parser.parse_args()
    main(args.rootdir)
