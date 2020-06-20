#! /usr/bin/python3
import os
import re
import sys

sys.path.append("../..")

from crossword import Configuration


class NormalizeWordList:
    """ Utility to take a list of words and normalize them for the database

        - Make uppercase
        - Remove non-alphabetic characters
        - Split by spaces into multiple words
        - Sort and remove duplicates

        Writes the output files to a directory under the
        "wordlists" data directory (see Configuration)
    """

    def __init__(self, filename, output_dir):
        """ Creates a new NormalizeWordList object """
        # Get the file name
        filename = os.path.expanduser(filename)
        if not os.path.exists(filename):
            errmsg = f"'{filename}' file does not exist"
            raise FileNotFoundError(errmsg)
        self.filename = filename

        # Get the base name from the file name
        self.basename = os.path.splitext(os.path.basename(filename))[0]

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
        """ Creates the normalized word list """
        wordset = set()
        with open(self.filename) as fp:
            for line in fp:
                line = line.strip()
                line = line.upper()  # Make uppercase
                line = re.sub('[^A-Z ]', ' ', line)  # Remove special characters
                tokens = line.split()  # Split at blanks
                for token in tokens:
                    wordset.add(token)
                wordlist = list(wordset)
                wordlist = sorted(wordlist)

        # Write the output file
        outfile = os.path.join(self.output_dir, self.basename + ".txt")
        with open(outfile, "w") as fp:
            for word in wordlist:
                print(word, file=fp)


if __name__ == '__main__':
    import argparse

    description = r"""
Normalizes a word list:
- Makes all letters uppercase
- Strips all non-alphabetic characters (except blanks)
- Splits into individual words at blank boundaries
- Sorts and removes duplicates
- Writes to the output directory
"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('filename', help="Input file containing word list")
    parser.add_argument('-o', '--output-dir', help="Output root directory")
    args = parser.parse_args()

    try:
        app = NormalizeWordList(args.filename, args.output_dir)
        app.run()
    except Exception as e:
        errmsg = f"{e.__class__.__name__}: {e}"
        print(errmsg, file=sys.stderr)
        exit(-1)
