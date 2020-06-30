# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Table of contents
- [Version 2.2.0 - 2020/06/30](#version-220---20200630)
- [Version 2.1.4 - 2020/06/23](#version-214---20200623)
- [Version 2.0.0 - 2020/06/21](#version-200---20200621)
- [Version 1.4.0 - 2020/06/14](#version-140---20200614)

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

7d01c2a - Phil Hanna, 2020-06-30 4 hours ago : Pad empty clues with x'A0' so they are clickable
262e98f - Phil Hanna, 2020-06-30 6 hours ago : Fix for issue #99
4e94b38 - Phil Hanna, 2020-06-29 20 hours ago : Added imports for ClueExportVisitor and ClueImportVisitor
03b8d20 - Phil Hanna, 2020-06-29 21 hours ago : Merge branch 'dev'
8f27267 - Phil Hanna, 2020-06-29 31 hours ago : Refactored import/export clues
db6c5b2 - Phil Hanna, 2020-06-29 31 hours ago : Refactored import/export clues












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
