#! /usr/bin/python3
import os
import re
import sys

from crossword.configuration import Configuration


class SplitWordList:
    """ Utility to take a list of words and create sublists by length

        - Removes non-alphabetic characters
        - Makes uppercase
        - Prepends length to each line
        - Splits the file into individual files by length

        Writes the output files to a directory under the
        "wordlists" data directory (see Configuration)
    """

    def __init__(self, filename, output_dir):
        """ Creates a new SplitWordList object """
        # Get the file name
        filename = os.path.expanduser(filename)
        if not os.path.exists(filename):
            errmsg = f"'{filename}' file does not exist"
            raise FileNotFoundError(errmsg)
        self.filename = filename

        # Get the list name from the file name
        self.listname = os.path.splitext(os.path.basename(filename))[0]

        # Get the output directory
        output_dir = output_dir if output_dir else Configuration.get_wordlists_root()
        if not os.path.exists(output_dir):
            errmsg = f"'{output_dir}' directory does not exist"
            raise FileNotFoundError(errmsg)
        if not os.path.isdir(output_dir):
            errmsg = f"'{output_dir}' is not a directory"
            raise NotADirectoryError(errmsg)
        self.output_dir = output_dir

    def run(self):
        """ Creates the split word list """

        # Create the directory that will receive the files
        splitdir = os.path.join(self.output_dir, self.listname)
        try:
            os.mkdir(splitdir)
        except FileExistsError:
            errmsg = f"'{splitdir}' directory already exists"
            raise FileExistsError(errmsg)

        length_map = self.get_length_map()
        for length, wordlist in length_map.items():
            filename = f"{self.listname}{int(length)}.txt"
            filename = os.path.join(splitdir, filename)
            with open(filename, "wt") as fp:
                for word in wordlist:
                    print(word, file=fp)
            pass

    def get_length_map(self):
        linelist = self.getlines()
        length_map = {}
        for line in linelist:
            length, word = line.split(' ', 2)
            if length not in length_map:
                length_map[length] = []
            length_map[length].append(word)
        return length_map

    def getlines(self):
        """ Sanitized the line and prepends length """
        linelist = []
        with open(self.filename) as fp:
            for line in fp:
                line = line.strip()

                # Convert to uppercase
                line = line.upper()

                # Remove non-alphabetic characters and compress
                line = re.sub(r'''[^A-Z]''', '', line)

                # Prepend length
                line = f"{len(line):04} {line}"

                linelist.append(line)
        linelist.sort()
        return linelist


if __name__ == '__main__':
    import argparse

    description = """
Splits a list of word into individual files by word length
"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--version', action='store_true', help='display version number')
    parser.add_argument('filename', help="Input file containing word list")
    parser.add_argument('-o', '--output-dir', help="Output root directory")
    args = parser.parse_args()

    try:
        app = SplitWordList(args.filename, args.output_dir)
        app.run()
    except Exception as e:
        errmsg = f"{e.__class__.__name__}: {e}"
        print(errmsg, file=sys.stderr)
        exit(-1)

