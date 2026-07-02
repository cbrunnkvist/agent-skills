# VisiData References Index

Grouped by topic. Load only the files relevant to the user's current task.

## Loading & Formats
- `loading.md` — How to open files, pipe stdin, force filetype with `-f`, load multiple files, convert formats
- `formats.md` — Full list of supported filetypes, loader/saver status, format-specific options (csv, json, tsv, sqlite, postgres, etc.)
- `usage.md` — Basic CLI invocation, quitting, piping basics

## Navigation & Viewing
- `navigate.md` — Scrolling, searching within sheets, moving between sheets, input history
- `columns.md` — Hide/unhide columns, set column types, format columns, split columns, expand nested data, create derived columns, batch column operations
- `rows.md` — Select/filter rows, sort, move/copy/remove rows, null handling, multi-line row display

## Editing
- `edit.md` — Edit cells, bulk corrections with `ge`, rename columns, cell navigation while editing, readline shortcuts

## Grouping & Statistics
- `group.md` — Aggregators, frequency tables, pivot tables, descriptive statistics, filter grouped/described rows
- `freq.md` — Frequency table internals: binning (discrete/numeric), commands on freq table, selection propagation, options

## Combining Data
- `join.md` — Join types (inner, outer, full, diff, extend, merge, append, concat), append datasets, identify source rows

## Visualization
- `graph.md` — Graph single/multiple columns, keyboard and mouse interaction with graphs

## Saving & Replaying
- `save-restore.md` — Save/replay sessions with cmdlogs (.vd, .vdj, .vdx), replay on different files, batch replay

## Customization
- `customize.md` — Configure keybindings, create commands, custom aggregators, save options, .visidatarc, XDG config

## Piping
- `pipes.md` — stdin/stdout pipe/redirect behavior, Ctrl+Q vs q output, pipeline workflows

## CRUD
- `crud.md` — Create sheets, add rows/columns, fill ranges, edit cells, cursor movement after edit
