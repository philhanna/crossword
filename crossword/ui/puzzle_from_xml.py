import xml.etree.ElementTree as ET

from crossword.grids import Grid
from crossword.puzzles import Puzzle


class PuzzleFromXML:
    """ Creates a puzzle from an XML file """
    def __init__(self, xmlstr):
        self.puzzle = self.create_puzzle(xmlstr)

    def create_puzzle(self, xmlstr):
        ns = {
            'cc': 'http://crossword.info/xml/crossword-compiler',
            'rp': 'http://crossword.info/xml/rectangular-puzzle'
        }
        root = ET.fromstring(xmlstr)
        elem_rp = root.find('rp:rectangular-puzzle', ns)
        elem_crossword = elem_rp.find('rp:crossword', ns)
        elem_grid = elem_crossword.find('rp:grid', ns)

        # Grid size
        n = int(elem_grid.get('height'))
        grid = Grid(n)

        # Black cells
        for elem_cell in elem_grid.findall('rp:cell', ns):
            celltype = elem_cell.get('type')
            if celltype == 'block':
                r = int(elem_cell.get('y'))
                c = int(elem_cell.get('x'))
                grid.add_black_cell(r, c)

        # Title
        elem_title = elem_rp.find('rp:metadata/rp:title', ns)
        title = elem_title.text
        if not title:
            title = None

        # Puzzle
        puzzle = Puzzle(grid, title)

        # Add the cells
        for elem_cell in elem_grid.findall('rp:cell', ns):
            r = int(elem_cell.get('y'))
            c = int(elem_cell.get('x'))
            if puzzle.is_black_cell(r, c):
                continue
            letter = elem_cell.get('solution')
            if letter != ' ':
                puzzle.set_cell(r, c, letter)

        # Map the word ID to numbered cells
        wordmap = {}
        for elem_word in elem_crossword.findall('rp:word', ns):
            wordid = elem_word.get('id')
            r = int(elem_word.get('y').split('-')[0])
            c = int(elem_word.get('x').split('-')[0])
            nc = puzzle.get_numbered_cell(r, c)
            wordmap[wordid] = nc

        # Add the clues
        for elem_clues in elem_crossword.findall('rp:clues', ns):
            elem_b = elem_clues.find('rp:title/rp:b', ns)
            direction = elem_b.text[0]  # A or D
            for elem_clue in elem_clues.findall('rp:clue', ns):
                wordid = elem_clue.get('word')
                nc = wordmap[wordid]
                clue = elem_clue.text
                puzzle.set_clue(nc.seq, direction, clue)

        return puzzle
