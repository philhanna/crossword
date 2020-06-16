# Crossword utilities

from datetime import datetime
import os.path

def list_puzzles(puzzles_root):
    for filename in sorted(
            [
                os.path.join(puzzles_root, entry)
                for entry in os.listdir(puzzles_root)
            ],
            key=lambda p: os.path.getmtime(p),
            reverse=True):
        mtime = datetime.fromtimestamp(os.path.getmtime(filename))
        mtimestr = mtime.strftime("%Y-%m-%d %H:%M:%S")
        basename = os.path.basename(filename)
        puzzlename = os.path.splitext(basename)[0]
        line = f"{mtimestr} {puzzlename}"
        print(line)
    
