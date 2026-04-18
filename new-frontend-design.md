# New Frontend Design Plan

## Goal

Redesign the frontend so it feels like a focused crossword-construction workspace rather than a legacy admin tool, while keeping the current plain JavaScript architecture and existing backend APIs.

The redesign should:

- Preserve the existing application behavior and data flows
- Improve clarity, scanability, and editing speed
- Reduce dependence on hidden dropdown menus for common actions
- Make the grid feel like the primary object on the page
- Turn the right side into a stable, useful working sidebar
- Be implementable incrementally without a framework rewrite

## Design Direction

The target UI should feel like an "editor-first workbench."

Core principles:

- The grid is the center of attention
- Primary actions are always visible
- The current editing context is always obvious
- Supporting information lives in a persistent sidebar
- Visual hierarchy should come from layout, spacing, and contrast, not from clutter
- Puzzle mode and Grid mode should feel related, but clearly distinct

## Proposed Information Architecture

Replace the current experience with four persistent regions:

1. Top app bar
2. Secondary action bar
3. Main workspace
4. Overlay dialogs

### 1. Top App Bar

Purpose:

- Brand the app
- Show puzzle identity
- Surface global actions that matter at all times

Contents:

- App name and small logo
- Current puzzle name
- Optional puzzle title
- Save status text such as `Saved` or `Unsaved changes`
- Help link

Notes:

- Keep this visually compact
- This replaces the current oversized header plus menu bar split
- The app bar should feel modern and calm, not decorative

### 2. Secondary Action Bar

Purpose:

- Expose the high-frequency actions without forcing the user into menus

Contents in Puzzle mode:

- `Save`
- `Undo`
- `Redo`
- `Puzzle mode`
- `Grid mode`
- `Edit word`
- `Fill order`
- `Stats`
- `Export`

Contents in Grid mode:

- `Save`
- `Undo`
- `Redo`
- `Puzzle mode`
- `Grid mode`
- `Rotate`
- `Generate`
- `Stats`
- `Export`

Notes:

- The mode switch should be a visible toggle, not just menu items
- Keep the old dropdown menu only as a fallback for lesser-used actions like rename, delete, import, and title editing
- Primary buttons should be grouped by importance

### 3. Main Workspace

Purpose:

- Give the grid and the editing context a stable, legible home

Layout:

- Left: main grid canvas area
- Right: persistent sidebar

Recommended width behavior:

- Desktop: grid area about 60 to 68 percent, sidebar about 32 to 40 percent
- Mobile/narrow screens: stack vertically, with the sidebar below the grid

This is a better fit than the current rigid 45/55 split because the grid should visually dominate the workspace.

### 4. Overlay Dialogs

Keep overlays for:

- Confirmations
- Text input prompts
- Constraints
- Definitions
- Puzzle chooser

But restyle them to match the new system:

- Softer shadows
- Better spacing
- Consistent buttons
- More readable widths on large and small screens

## Main Workspace Details

## Grid Area

The left side should be treated as the primary editing surface.

Structure:

- Puzzle summary row above the grid
- Framed grid canvas
- Context hint area below the grid

### Puzzle Summary Row

Contents:

- Puzzle name
- Puzzle title
- Mode badge such as `Puzzle Mode` or `Grid Mode`
- Validation indicator such as `Valid` or `Needs attention`

This creates orientation without forcing the user to scan menus or side panels.

### Framed Grid Canvas

The grid should sit inside a dedicated panel/card with generous padding.

Design goals:

- Center the grid
- Increase whitespace around it
- Use a subtle panel background so the grid feels intentional
- Ensure the grid scales well for common puzzle sizes

SVG styling improvements:

- Slightly darker outer border
- Softer internal lines
- Clearer selected-word highlight
- Clearer active-cell highlight
- Better number/letter typography

In Puzzle mode:

- Selected word should be strongly visible
- Active cell should be distinct from the rest of the word
- Crossing words should still be easy to inspect

In Grid mode:

- Toggleable cells should feel interactive
- Hover state should preview the action
- A compact instructional note should explain the mode

### Context Hint Area

Show lightweight, mode-specific guidance:

- Puzzle mode: keyboard shortcuts, click behavior, selected clue
- Grid mode: "Click cells to toggle blocks", symmetry expectations, generate availability

This area should replace the current nearly empty Grid mode RHS experience.

## Sidebar

The right side should become a persistent contextual sidebar rather than a panel that radically changes shape each time.

Recommended top-level tabs:

- `Clues`
- `Word`
- `Stats`
- `Fill Order`

Behavior:

- The sidebar frame stays stable
- Only the inner content changes
- Switching tabs should feel lightweight

Default tab behavior:

- Puzzle mode with no selected word: `Clues`
- Puzzle mode with selected word: still `Clues`, but show selection summary at top
- Puzzle mode when editing a word: automatically switch to `Word`
- Grid mode: default to `Stats` or a `Grid` helper panel

## Sidebar Tab Details

### Clues Tab

Purpose:

- Make clue navigation fast and visually clear

Structure:

- Header row with clue counts and quick filters
- Two vertically stacked sections or segmented switch for `Across` and `Down`
- Search field for clue text or clue number

Recommended improvements:

- Show clue number and clue text with better spacing
- Make the selected clue clearly highlighted
- Mark clues missing text with a visible badge instead of relying only on scroll position
- Add a subtle completion indicator, for example counts like `Across 12/15 clued`

Preferred layout:

- On wide screens: Across and Down can remain side by side if they are readable
- Better default: one list with a segmented control for `Across` and `Down`, which improves vertical scanability

Reason:

The current two-column clue layout is compact, but it splits attention and makes scanning harder.

### Word Tab

Purpose:

- Turn the existing word editor into a guided editing panel

Structure:

- Selected entry header
- Pattern/answer input
- Clue input
- Suggestions section
- Secondary tools section
- Primary action row

#### Selected Entry Header

Show:

- Entry number and direction
- Length
- Pattern preview
- Small description like `3 crossing constraints`

This gives immediate context before the user starts typing.

#### Pattern/Answer Input

Redesign the answer field so it feels more crossword-specific:

- Monospace
- Larger letter spacing
- Strong uppercase presentation
- Optional per-cell segmentation styling for readability

If per-cell segmented input is too much for the current codebase, keep a single input but style it to resemble slots.

#### Clue Input

Make it more prominent and easier to edit:

- Full-width field
- Clear label
- Better spacing from answer input

#### Suggestions Section

The suggestions area should feel like a ranked assistant, not a raw list.

Add:

- Header with result count
- Sort label like `Best matches`
- Stronger hover and selected states
- Better score visualization
- Empty state text that explains what to try next
- Clicking a suggestion previews it in the answer field before commit

#### Secondary Tools Section

Keep:

- `Show constraints`
- `Show definitions`

But style them as secondary actions with less visual weight than `Apply` or `Save`.

#### Primary Action Row

Preferred buttons:

- `Apply`
- `Cancel`
- `Suggest`

If needed:

- Put `Suggest` above with the suggestion controls
- Keep `Apply` and `Cancel` pinned at the bottom of the panel

Reason:

The current placement mixes search and commit actions into one row, which muddies the flow.

### Stats Tab

Purpose:

- Make validation and puzzle health easy to assess

Structure:

- Status summary cards
- Error list
- Puzzle metrics
- Word length distribution table

Recommended improvements:

- Promote validity to a top-level status chip
- If invalid, show errors in a clearly separated warning area
- Show metrics in compact cards rather than only table rows

Suggested metrics:

- Size
- Word count
- Black cell count
- Validity

### Fill Order Tab

Purpose:

- Help constructors decide what to work on next

Structure:

- Intro text
- Sort/ranking explanation
- Table or list of suggested next slots

Recommended improvements:

- Highlight the top suggested slot
- Let each row feel actionable
- Use more spacing so the table does not feel like raw diagnostics
- Clicking a row should switch to the `Word` tab and load that slot directly

## Mode Design

## Puzzle Mode

This should feel like "content editing mode."

Visual cues:

- Warm neutral or lightly tinted workspace background
- Stronger clue and word emphasis
- Keyboard hints visible but subtle

Main priority:

- Fast movement among entries
- Clear selected word and active cell
- Smooth transition between clue browsing and word editing

## Grid Mode

This should feel like "structure editing mode."

Visual cues:

- Slightly different accent color from Puzzle mode
- Clear mode badge
- Dedicated helper panel in sidebar

Main priority:

- Make structural edits safe and understandable
- Show generation constraints and eligibility
- Keep stats close by

Suggested Grid mode sidebar content:

- Brief editing instructions
- Current grid size
- Symmetry reminder
- Generate button rationale
- Quick stats summary

This is stronger than the current blank RHS.

## Visual System

## Typography

Use a more intentional font stack than the current default-feeling mix.

Suggested approach:

- UI font: a modern, readable sans-serif with some personality
- Monospace font: for answers, patterns, and metrics

Examples:

- Sans: `IBM Plex Sans`, `Source Sans 3`, or `Public Sans`
- Mono: `IBM Plex Mono` or `JetBrains Mono`

The goal is not trendiness. It is to make the app feel editorial and precise.

## Color

Avoid the current heavy dependence on `w3-blue-gray` plus pale yellow/green blocks.

Use a small design token set:

- Background
- Surface
- Surface contrast
- Primary accent
- Secondary accent
- Border
- Success
- Warning
- Error
- Muted text

Possible direction:

- Soft paper-like neutrals
- Deep slate or ink for text
- Muted blue or teal for primary actions
- Warm gold for selected clue accents
- Green/red reserved for valid/error status only

## Spacing

Adopt a simple spacing scale, for example:

- 4
- 8
- 12
- 16
- 24
- 32

Use it consistently across:

- Panels
- Buttons
- List rows
- Form fields
- Dialog interiors

## Components To Introduce

Without changing frameworks, create reusable visual patterns in CSS:

- App bar
- Action bar
- Workspace panel
- Sidebar panel
- Tab strip
- Primary button
- Secondary button
- Badge
- Status chip
- Empty state
- Metric card
- List row

This is the minimum design system needed to replace the current mixture of W3CSS classes and inline styles.

## Responsive Plan

The current UI is not well structured for smaller screens. The redesign should explicitly handle mobile and narrow widths.

Behavior under narrow width:

- Stack grid above sidebar
- Let action bar wrap to multiple rows
- Collapse secondary actions into an overflow menu if necessary
- Keep the selected word context visible
- Make modal widths fluid

Behavior under medium width:

- Keep two columns
- Shrink sidebar intelligently
- Let clue lists switch from side-by-side to tabbed

## Accessibility And Interaction Improvements

The redesign should also improve usability beyond visual styling.

Recommended changes:

- Clear focus styles for buttons, clue rows, and form fields
- Larger click targets in clue lists and toolbars
- Strong contrast for selected states
- Better labels for icon buttons
- Avoid relying on color alone to signal missing clues or invalid state

Potential interaction improvements:

- Single-click selection behavior should remain, but direction switching could be made more discoverable
- Add visible shortcut hints for `Tab`, arrows, `Esc`, and typing behavior
- Consider replacing double-click for down-word selection with a small direction toggle or repeated click behavior if discoverability becomes a problem

## Implementation Plan

This should be done incrementally so the app stays usable throughout.

### Phase 1: Establish the visual system

Work:

- Expand `style.css` into a real design layer with variables and shared component classes
- Reduce inline styling in `index.html` and `app.js`
- Restyle header, menu, dialogs, buttons, cards, and notifications

Outcome:

- Immediate visual improvement without changing behavior

### Phase 2: Replace layout structure

Work:

- Rework `index.html` to create app bar, action bar, workspace, and sidebar shells
- Replace the rigid `w3-cell-row` split with a responsive layout
- Give the grid a framed main panel and the RHS a persistent sidebar shell

Outcome:

- Much stronger hierarchy and better screen use

### Phase 3: Redesign sidebar content

Work:

- Convert clue list into a more structured navigation panel
- Refactor word editor into the `Word` tab
- Restyle stats and fill-order panels into card-based layouts
- Add Grid mode helper content

Outcome:

- The sidebar becomes a real tool, not a placeholder area

### Phase 4: Improve interaction details

Work:

- Improve selected states and hover states in SVG and lists
- Add visible mode badges and save state indicators
- Add empty states and explanatory text
- Tune responsive behavior

Outcome:

- The app feels deliberate and polished instead of merely functional

## Files Likely To Change

- `frontend/index.html`
- `frontend/static/css/style.css`
- `frontend/static/js/app.js`

Potentially also:

- `docs/design/frontend.md`

## Recommended First Milestone

If we want the highest value with the lowest implementation risk, the first milestone should be:

1. Introduce a real app bar and visible action bar
2. Change the workspace to a grid-first responsive layout
3. Turn the RHS into a stable sidebar shell
4. Restyle clue list and word editor to match the new system

That would produce a major UX improvement even before deeper interaction refinements.

## Success Criteria

The redesign is successful if:

- A first-time user can tell what the main editing surface is within a few seconds
- Common actions no longer require menu hunting
- The selected word and current mode are always obvious
- Grid mode no longer feels empty
- The clue workflow is easier to scan and navigate
- The app still works with the current APIs and plain JavaScript structure

## Final Recommendation

Do not rewrite the frontend stack yet.

The current code can support a significantly better UI if we:

- improve the page structure
- introduce a lightweight design system
- make the grid dominant
- make the sidebar persistent and contextual

This is the best path because it meaningfully improves the product without paying the cost of a full framework migration.
