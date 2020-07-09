""" Handles requests having to do with publishing a puzzle
"""
import logging
import os
import re
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import request, make_response

from crossword import Puzzle, dbfile, PuzzleToSVG


def puzzle_publish_acrosslite():
    """ Publishes a puzzle in across lite form """

    def get_indent():
        """ Amount by which to indent each line of input """
        return " " * 5

    def get_author_name():
        """ Formatted string with author's name and email """
        fullname = None
        with sqlite3.connect(dbfile()) as con:
            try:
                c = con.cursor()
                userid = 1  # TODO Replace hard-coded user ID
                c.execute("""
                    SELECT      author_name
                    FROM        users
                    WHERE       id = ?
                """, (userid,))
                row = c.fetchone()
                name = row[0]
                fullname = f"by {name}"
            except sqlite3.Error as e:
                msg = (
                    f"Unable to read profile for user {userid}"
                    f", error={e}"
                )
                logging.warning(msg)
            pass
        return fullname

    class PuzzlePublishAcrossLite:
        """ Creates a text file with the puzzle and clues

        Format is documented here:
        https://www.litsoft.com/across/docs/AcrossTextFormat.pdf
        """

        def __init__(self, puzzle: Puzzle, basename: str):
            """ Constructor """
            self.puzzle = puzzle
            self.basename = basename
            self.txtstr = self.generate_txt()

        def get_txt(self):
            """ Returns the completed text """
            return self.txtstr

        def get_size(self):
            """ Returns the size of the puzzle as nxn """
            n = self.puzzle.n
            size = f"{n}x{n}"
            return size

        def get_title(self):
            """ Returns the puzzle title or blank """
            title = self.puzzle.get_title()
            if not title:
                title = ""
            return title

        def get_gridlines(self):
            """ Generator that returns the rows of the puzzle """
            puzzle = self.puzzle
            n = puzzle.n
            for r in range(1, n + 1):
                rowstr = ""
                for c in range(1, n + 1):
                    if puzzle.is_black_cell(r, c):
                        rowstr += "."
                    else:
                        cell = puzzle.get_cell(r, c)
                        rowstr += cell
                yield rowstr

        def get_across_clues(self):
            """ Generator that returns the across clues """
            puzzle = self.puzzle
            for seq in sorted(puzzle.across_words):
                word = puzzle.across_words[seq]
                clue = word.get_clue()
                if not clue:
                    clue = ""
                yield clue

        def get_down_clues(self):
            """ Generator that returns the across clues """
            puzzle = self.puzzle
            for seq in sorted(puzzle.down_words):
                word = puzzle.down_words[seq]
                clue = word.get_clue()
                if not clue:
                    clue = ""
                yield clue

        def generate_txt(self):
            """ Generates the AcrossLite text format"""
            with StringIO() as fp:
                # ACROSS PUZZLE
                fp.write("<ACROSS PUZZLE>" + "\n")

                # TITLE
                fp.write("<TITLE>" + "\n")
                fp.write(get_indent() + self.get_title() + "\n")  # Blank line

                # AUTHOR
                fp.write("<AUTHOR>" + "\n")
                fp.write(get_indent() + get_author_name() + "\n")

                # COPYRIGHT
                fp.write("<COPYRIGHT>" + "\n")
                fp.write("\n")  # Blank line

                # SIZE nxn
                fp.write("<SIZE>" + "\n")
                fp.write(get_indent() + self.get_size() + "\n")

                # GRID the rows of the puzzle
                fp.write("<GRID>" + "\n")
                for gridline in self.get_gridlines():
                    fp.write(get_indent() + gridline + "\n")

                # ACROSS - the across clues
                fp.write("<ACROSS>" + "\n")
                for clue in self.get_across_clues():
                    fp.write(get_indent() + clue + "\n")

                # DOWN - the down clues
                fp.write("<DOWN>" + "\n")
                for clue in self.get_down_clues():
                    fp.write(get_indent() + clue + "\n")

                # NOTEPAD - describe the tool
                fp.write("<NOTEPAD>" + "\n")
                fp.write("Created with Crossword Puzzle Editor, by Phil Hanna" + "\n")
                fp.write("See https://github.com/philhanna/crossword" + "\n")

                # Get the full string (before you close the file)
                txtstr = fp.getvalue()

            # Return the body of the file
            return txtstr

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    userid = 1      # TODO replace the hard-coded user ID
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    publisher = PuzzlePublishAcrossLite(puzzle, puzzlename)

    # Text file
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".txt")
    txt_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_txt() + "\n")

    # JSON
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".json")
    json_filename = filename
    with open(filename, "wt") as fp:
        fp.write(jsonstr + "\n")

    # Create an in-memory zip file
    with BytesIO() as fp:
        with ZipFile(fp, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.write(txt_filename, puzzlename + ".txt")
            zf.write(json_filename, puzzlename + ".json")
        zipbytes = fp.getvalue()

    # Return it as an attachment
    zipfilename = f"acrosslite-{puzzlename}.zip"
    resp = make_response(zipbytes)
    resp.headers['Content-Type'] = "application/zip"
    resp.headers['Content-Disposition'] = f'attachment; filename="{zipfilename}"'
    return resp


def puzzle_publish_nytimes():
    """ Publishes a puzzle in New York Times format (PDF) """

    class PuzzlePublishNYTimes:
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

        @staticmethod
        def get_author_text():
            text_list = []
            with sqlite3.connect(dbfile()) as con:
                con.row_factory = sqlite3.Row
                try:
                    c = con.cursor()
                    userid = 1  # TODO Replace hard-coded user ID
                    c.execute("""
                        SELECT      *
                        FROM        users
                        WHERE       id = ?
                    """, (userid,))
                    row = c.fetchone()

                    # Author name
                    name = row['author_name']
                    text_list.append(name)

                    # Address lines 1 and 2
                    addr1 = row['address_line_1']
                    addr2 = row['address_line_2']
                    addr1 = addr1.strip() if addr1 else ""
                    addr2 = addr2.strip() if addr2 else ""
                    address = f"{addr1} {addr2}".strip()
                    text_list.append(address)

                    # City, state, zip
                    city = row['address_city']
                    state = row['address_state']
                    zip = row['address_zip']
                    csz = f"{city}, {state} {zip}"
                    text_list.append(csz)

                    # Email
                    email = row['email']
                    text_list.append(email)

                except sqlite3.Error as e:
                    msg = (
                        f"Unable to read profile for user {userid}"
                        f", error={e}"
                    )
                    logging.warning(msg)
                pass

            return text_list

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

            for author_text in self.get_author_text():
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

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    userid = 1      # TODO replace the hard-coded user ID
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    publisher = PuzzlePublishNYTimes(puzzle, puzzlename)

    # SVG
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".svg")
    svg_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_svg() + "\n")

    # HTML
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".html")
    html_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_html() + "\n")

    # JSON
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".json")
    json_filename = filename
    with open(filename, "wt") as fp:
        fp.write(jsonstr + "\n")

    # Create an in-memory zip file
    with BytesIO() as fp:
        with ZipFile(fp, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.write(svg_filename, puzzlename + ".svg")
            zf.write(html_filename, puzzlename + ".html")
            zf.write(json_filename, puzzlename + ".json")
        zipbytes = fp.getvalue()

    # Return it as an attachment
    zipfilename = f"nytimes-{puzzlename}.zip"
    resp = make_response(zipbytes)
    resp.headers['Content-Type'] = "application/zip"
    resp.headers['Content-Disposition'] = f'attachment; filename="{zipfilename}"'
    return resp


def puzzle_load_common(userid, puzzlename):
    """ Loads the JSON string for a puzzle """
    with sqlite3.connect(dbfile()) as con:
        try:
            con.row_factory = sqlite3.Row
            c = con.cursor()
            c.execute('''
                SELECT  jsonstr
                FROM    puzzles
                WHERE   userid=?
                AND     puzzlename=?''', (userid, puzzlename))
            row = c.fetchone()
            jsonstr = row['jsonstr']
        except sqlite3.Error as e:
            msg = (
                f"Unable to load puzzle"
                f", userid={userid}"
                f", puzzlename={puzzlename}"
                f", error={e}"
            )
            jsonstr = None
        return jsonstr
