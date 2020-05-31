import io
import os

from configuration import Configuration
from puzzle import Puzzle
from to_svg import PuzzleToSVG


class NYTimesOutput:
    """ Creates an HTML file with the puzzle and clues """

    def __init__(self, filename, puzzle: Puzzle, configfile="~/.crossword_config.ini"):
        # Consider just the base name, with path but without extension
        self.filename = os.path.splitext(os.path.expanduser(filename))[0]
        self.puzzle = puzzle
        self.config = Configuration()
        self.svg = PuzzleToSVG(self.puzzle)

    def get_svg_width(self):
        return self.svg.gridsize

    def get_svg_height(self):
        return self.svg.gridsize

    def generate_svg(self):
        """ Generates an image of the puzzle in an SVG file """
        xmlstr = self.svg.generate_xml()
        svg_filename = self.filename + ".svg"
        with open(svg_filename, "wt") as fp:
            print(xmlstr, file=fp)

    def generate_html(self):
        """ Generates the wrapper HTML """
        fp = io.StringIO()

        # Write the header

        boilerplate = r'''<html>
<head>
<style>
td { vertical-align: top; }
h1 { text-align: center; }
tr.ds {
   height: 8mm
}
</style>
</head>
<body>
        '''
        print(boilerplate, file=fp)

        # Write the author name and address block

        author_name = self.config.get_author_name()
        author_addr = self.config.get_author_address()
        author_csz = self.config.get_author_city_state_zip()
        author_email = self.config.get_author_email()

        boilerplate = fr'''
<!-- Name and address -->
<div style="font-family: 'sans serif'; font-size: 16pt">
<table>
<tr><td>{author_name}</td></tr>
<tr><td>{author_addr}</td></tr>
<tr><td>{author_csz}</td></tr>
<tr><td>{author_email}</td></tr>
</table>
</div>
'''
        print(boilerplate, file=fp)


        # Write the SVG calling lines

        svg_file_name = os.path.basename(self.filename) + '.svg'
        boilerplate = fr'''
<img src="{svg_file_name}" width="{self.get_svg_width()}" height="{self.get_svg_height()}"/>
'''
        print(boilerplate, file=fp)

        # Write the across clues

        boilerplate = r'''
<!-- Across clues -->
<div style="page-break-before: always">
<table width="95%">
<tr class="ds">
<th width="80%" align="left">ACROSS</th>
<th width="20%">&nbsp;</th>
</tr>        
'''
        print(boilerplate, file=fp)

        for seq in sorted(self.puzzle.across_words):
            across_word = self.puzzle.across_words[seq]
            across_text = across_word.get_text()
            across_clue = across_word.get_clue()

            boilerplate = fr'''
<tr class="ds">
<td>{seq} {across_clue}</td>
<td style="font-family: monospace">{across_text}</td>
</tr>
'''
            print(boilerplate, file=fp)

        print('</table>', file=fp)

        # Write the down clues

        boilerplate = r'''
<!-- Down clues -->
<div style="page-break-before: always">
<table width="95%">
<tr class="ds">
<th width="80%" align="left">DOWN</th>
<th width="20%">&nbsp;</th>
</tr>        
'''
        print(boilerplate, file=fp)

        for seq in sorted(self.puzzle.down_words):
            down_word = self.puzzle.down_words[seq]
            down_text = down_word.get_text()
            down_clue = down_word.get_clue()

            boilerplate = fr'''
<tr class="ds">
<td>{seq} {down_clue}</td>
<td>{down_text}</td>
</tr>
'''
            print(boilerplate, file=fp)

        print('</table>', file=fp)

        print('</html>', file=fp)

        htmlstr = fp.getvalue()
        fp.close()
        html_filename = self.filename + ".html"
        with open(html_filename, "wt") as fp:
            print(htmlstr, file=fp)
