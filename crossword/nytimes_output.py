import os
import re
import xml.etree.ElementTree as ET

from crossword.configuration import Configuration
from crossword.puzzle import Puzzle
from crossword.to_svg import PuzzleToSVG


class NYTimesOutput:
    """ Creates an HTML file with the puzzle and clues """

    def __init__(self, puzzle: Puzzle, basename: str):
        self.puzzle = puzzle
        self.basename = basename
        self.svg = PuzzleToSVG(self.puzzle)
        self.svgstr = self.svg.generate_xml()
        self.htmlstr = self.generate_html()

    def get_svg(self):
        return self.svgstr

    def get_html(self):
        return self.htmlstr

    def get_svg_width(self):
        return self.svg.gridsize

    def get_svg_height(self):
        return self.svg.gridsize

    def generate_html(self):
        """ Generates the wrapper HTML """

        # Create the <html> root element

        elem_root = ET.Element("html")

        # Create the <head> element

        elem_head = ET.SubElement(elem_root, "head")
        elem_style = ET.SubElement(elem_head, "style")
        elem_style.text = r'''
td { vertical-align: top; }
h1 { text-align: center; }
tr.ds {
   height: 8mm
}
'''
        # Create the <body> element

        elem_body = ET.SubElement(elem_root, "body")

        # Write the author name and address block

        elem_body.append(ET.Comment(" Name and address "))
        elem_div = ET.SubElement(elem_body, "div")
        elem_div.set("style", "font-family: 'sans serif'; font-size: 16pt;")
        elem_table = ET.SubElement(elem_div, "table")

        for author_text in [
            Configuration.get_author_name(),
            Configuration.get_author_address(),
            Configuration.get_author_city_state_zip(),
            Configuration.get_author_email(),
        ]:
            elem_tr = ET.SubElement(elem_table, "tr")
            elem_td = ET.SubElement(elem_tr, "td")
            elem_td.text = author_text

        # Write the SVG calling lines

        elem_body.append(ET.Comment(" SVG image of the puzzle "))
        svg_file_name = os.path.basename(self.basename) + '.svg'
        elem_img = ET.SubElement(elem_body, "img")
        elem_img.set("src", svg_file_name)
        elem_img.set("width", str(self.get_svg_width()))
        elem_img.set("height", str(self.get_svg_height()))

        # Write the across clues

        elem_body.append(ET.Comment(" Across clues "))
        elem_div = ET.SubElement(elem_body, "div")
        elem_div.set("style", "page-break-before: always;")
        elem_table = ET.SubElement(elem_div, "table")
        elem_table.set("width", "95%")
        elem_tr = ET.SubElement(elem_table, "tr")

        elem_tr.set("class", "ds")
        elem_th = ET.SubElement(elem_tr, "th")
        elem_th.set("width", "80%")
        elem_th.set("align", "left")
        elem_th.text = "ACROSS"

        elem_th = ET.SubElement(elem_tr, "th")
        elem_th.set("width", "20%")

        for seq in sorted(self.puzzle.across_words):
            across_word = self.puzzle.across_words[seq]
            across_text = across_word.get_text()
            if not across_text:
                across_text = ""
            across_clue = across_word.get_clue()
            if not across_clue:
                across_clue = ""

            elem_tr = ET.SubElement(elem_table, "tr")
            elem_tr.set("class", "ds")

            elem_td = ET.SubElement(elem_tr, "td")
            elem_td.text = f"{seq} {across_clue}"

            elem_td = ET.SubElement(elem_tr, "td")
            elem_td.set("style", "font-family: monospace")
            elem_td.text = re.sub(' ', '.', across_text)

        # Write the down clues

        elem_body.append(ET.Comment(" Down clues "))
        elem_div = ET.SubElement(elem_body, "div")
        elem_div.set("style", "page-break-before: always;")
        elem_table = ET.SubElement(elem_div, "table")
        elem_table.set("width", "95%")
        elem_tr = ET.SubElement(elem_table, "tr")

        elem_tr.set("class", "ds")
        elem_th = ET.SubElement(elem_tr, "th")
        elem_th.set("width", "80%")
        elem_th.set("align", "left")
        elem_th.text = "DOWN"

        elem_th = ET.SubElement(elem_tr, "th")
        elem_th.set("width", "20%")

        for seq in sorted(self.puzzle.down_words):
            down_word = self.puzzle.down_words[seq]
            down_text = down_word.get_text()
            if not down_text:
                down_text = ""
            down_clue = down_word.get_clue()
            if not down_clue:
                down_clue = ""

            elem_tr = ET.SubElement(elem_table, "tr")
            elem_tr.set("class", "ds")

            elem_td = ET.SubElement(elem_tr, "td")
            elem_td.text = f"{seq} {down_clue}"

            elem_td = ET.SubElement(elem_tr, "td")
            elem_td.set("style", "font-family: monospace")
            elem_td.text = re.sub(' ', '.', down_text)

        # Return the HTML as a string
        htmlstr = ET.tostring(element=elem_root, encoding="utf-8").decode()
        htmlstr = re.sub("><", ">\n<", htmlstr)
        return htmlstr
