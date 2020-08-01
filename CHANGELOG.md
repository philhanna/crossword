# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Table of contents
- [Version 2.4.0 - 2020/08/01](#version-240---20200801)
- [Version 2.3.0 - 2020/07/12](#version-230---20200712)
- [Version 2.2.0 - 2020/06/30](#version-220---20200630)
- [Version 2.1.4 - 2020/06/23](#version-214---20200623)
- [Version 2.0.0 - 2020/06/21](#version-200---20200621)
- [Version 1.4.0 - 2020/06/14](#version-140---20200614)

## Version 2.4.0 - 2020/08/01

Major overhaul of HTML files.  Now using templates with inheritance.
Made two common modal dialogs to replace all the individual ones.

## Version 2.3.0 - 2020/07/12

Starting with this release, grids, puzzles, configuration,
and words are stored in a database, rather than files in
the filesystem.  The database is an SQLite database
`crossword.db`.

The sample grids and puzzles are now distributed in
the `samples.db` database, which is used by default
for new installations.

Added a `users` database table, but only with a
single hard-coded user.  Will be expanded when I
add authentication and login.

The configuration file is simpler (just two options)
and renamed `.crossword.ini`.

### Added

- Issue #103: Added toolbar to word edit screen
- Issue #104: Scroll to the last used row in clues
- Issue #108: Switched to tabbed view in word edit screen
- Issue #111: Switch from files to sqlite3 database
- Issue #115: Switch database usage to SQLAlchemy
- Issue #116: Moved Flask secret key into environment variable
- Issue #117: Refactored app routing into blueprint classes
- Enabled logging in the UI classes
- SHA-1 encoding for JSON strings and passwords
- Bumped the version number to 2.3.0

### Changed

- Raised test coverage to 93%
- Refactored imports
- Moved `<style>` bits into common file
- Moved classes to more logical packages (issue #114)
- Removed unused classes
    - Configuration
    - crossword/util programs
- Updated README with better install instructions

### Fixed

- Issue #97: Added preview icon to PuzzleNew dialog
- Issue #98: Do not clear clue if word is blank

## Version 2.2.0 - 2020/06/30

The main feature of this release is the UI upgrade to the `puzzle.html`
screen, which now shows the clues on the same screen when the puzzle
editing is done (see Issue #99).

### Added

- Issue #90: JSON representation of puzzles and grids is no longer indented
- Added this **CHANGELOG.md**
- Added ability to scale the SVG (for preview)
- Added ability to have multiple actions in grid and puzzle choosers
- Issue #94: Added preview to grid chooser
- Issue #95: Added preview to puzzle chooser
- Issue #99: Show clues on puzzle screen
- Bumped the version number to 2.2.0

### Changed

- Refactored attribute names in `NumberedCell` (Issue #91)
- Use list comprehension in wordlist.lookup
- Added word count to preview screens (Issue #96)
- Moved clue import and export visitors to `util` subdirectory

### Fixed

- Issue #97: Added preview icon to PuzzleNew dialog
- Issue #98: Do not clear clue if word is blank

## Version 2.1.4 - 2020/06/23

### Added

- Added setup instructions to README.md
- Added LICENSE
- Bumped the version number to 2.1.4

### Changed

- Switched the NYTimes and AcrossLite menu option order
- Moved unit tests into crossword.tests package
- Fix for issue #89
- Fix for issue #88
- Fix for issue #87

## Version 2.0.0 - 2020/06/21

### Added

- Issue #88: Remove WordLookup menu item
- Issue #62: Make utilities directory
- Issue #63: Utility to create a word list and split it by length
- Issue #64: Add grid cells to grid.json
- Issue #66: Toolbar for puzzle screen
- Issue #67: Add undo/redo
- Issue #69: Show existing puzzle title in set title dialog
- Issue #71: Change save / save as workflow in Puzzle
- Issue #72: Change save / save as workflow in Grid
- Issue #74: Add toolbar to grid editor screen
- Issue #76: Add "rotate" to the grid editor toolbar
- Issue #80: Remove save and replace puzzle grid
- Issue #84: Refactor names of functions, HTML files, webapp methods for consistency

### Changed

- Added normalize_wordlist.py
- Added normalize_wordlist utility
- Added unit test for word.is_complete()
- Added Word.ACROSS and Word.DOWN enumeration
- Allow simple package name to be used in imports
- Made statistics dialog not as wide
- Refactored directory structure
- Refactored directory structure to use packages
- Removed instructions under the toolbar
- Removed puzzle stats and title from menu
- Removed unclosed quotes from puzzle.html
- Replace special characters with blanks
- Undo/redo text only, not clues or titles
- Use my class name for toolbar icons

### Fixed

- Issue #61: Add duplicate word check to puzzle statistics
- Issue #65: Edit word does not accept blanks
- Issue #68: After edit word, delete puzzle is not enabled
- Issue #70: Delete puzzle should not be enabled until the puzzle has been named
- Issue #75: "Save puzzle" is not enabled on new puzzles
- Issue #77: Delete grid fails if the object is named but unsaved
- Issue #78: Delete puzzle fails if the object is named but unsaved
- Issue #79: Check for existing file when doing "Save As" or "Rename"
- Issue #81: Puzzle title sometimes lost
- Issue #82: Limit undo/redo to word text, not clues and titles
 

## Version 1.4.0 - 2020/06/14

### Added

- Issue #46: Show grid and puzzle statistics and error checks
- Issue #51: Separate sections for the three grid validation checks
- Issue #53: Made grid and puzzle chooser dialogs scrollable
- Issue #54: Refactored display of suggested words
- Issue #55: Publish in AcrossLite format
- Issue #56: Added JSON source to publish .zip file
- Issue #58: Sort puzzle and grid lists by date of last save
- Issue #59: Added puzzle title

### Fixed

- Issue #47: Doubled display of statistics
- Issue #50: Double-click vs single-click broken
