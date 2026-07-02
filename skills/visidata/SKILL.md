---
name: visidata
description: Use VisiData CLI (`vd`) for terminal dataset exploration, cleanup, conversion, joins, profiling, exports, and `.vdj` replay workflows. Trigger for unknown/messy CSV, TSV, JSONL, XLSX, SQLite, Parquet, GeoJSON, fixed-width, or HTML table data. Not for VisiData Python API/plugin development.
---

# VisiData CLI Skill

VisiData is a terminal multiplexer for investigating and manipulating tabular data. It reads CSV, TSV, JSON, Excel, SQLite, and dozens of other formats, and provides vim-like keybindings for interactive exploration.

## High-Value Patterns

- Convert unfamiliar datasets between formats with `vd -b input -o output`.
- Generate `.vdj` command logs for guided interactive exploration or repeatable cleanup.
- Triage unknown data: inspect columns, set types, find nulls/outliers, summarize categories.
- Clean messy CSV/Excel exports with quoting, Unicode, dates, currencies, and mixed types.
- Join, diff, append, or reconcile two datasets interactively before saving.
- Use `vd` in pipelines when a human should visually select/filter rows.

## Installation

### macOS (Homebrew — recommended)

```bash
brew install visidata
```

### All platforms (pip)

Requires Python 3.8+.

```bash
pip3 install visidata
```

If `vd` is not found after pip install, check that `~/.local/bin` (Linux) or the Python scripts directory is on `$PATH`.

### Conda

```bash
conda install --channel conda-forge visidata
```

### Linux (distribution package managers)

```bash
# Debian/Ubuntu
sudo apt install visidata

# Fedora
sudo dnf install visidata

# Arch Linux
sudo pacman -S visidata

# NixOS
nix-env -i visidata
```

### Windows

Use [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/) (WSL) or [MSYS2's Python](https://www.msys2.org/docs/python/), then install via pip inside that environment.

### Upgrade

```bash
pip install --upgrade visidata
# or
brew upgrade visidata
```

### Verify

```bash
vd --version
```

## CLI Usage

### Basic launch

```bash
vd data.csv                  # open a file
vd a.tsv b.json c.xlsx      # open multiple files (last one displayed on top)
vd .                         # open DirSheet to browse filesystem
```

### Piping data

```bash
ps aux | vd                  # pipe into vd
vd - < data.tsv              # redirect from file
cat query.sql | mysql | vd   # chain with other tools
```

### Key CLI flags

| Flag | Purpose |
|------|---------|
| `-f TYPE` | Force input filetype (e.g. `-f csv`, `-f sqlite`, `-f fixed`) |
| `-o FILE` | Output to FILE (extension determines format) |
| `-of TYPE` | Force output filetype |
| `-b` | Batch mode (non-interactive, for scripts) |
| `-p FILE.vdj` | Replay a command log |
| `-d` | Dump format (output to stdout on quit) |
| `--header N` | Number of header rows (default: 1; use `--header=0` for headerless) |
| `-f ""` | Reset to extension-based detection after a `-f` flag |

**Important**: `-f` applies to all subsequent input paths on the command line, not just the one immediately following. Use `-f ""` to reset.

### Format conversion

```bash
vd -b input.csv -o output.json          # convert csv → json
vd -b data.fixed -of csv -o data.txt    # force output format
```

Not all loader formats support saving. Check `vd --help` or the formats reference for supported output types.

## Core Keybindings

### Navigation

| Key | Action |
|-----|--------|
| `↑↓←→` / `PgUp/PgDn` / `Home/End` | Move cursor |
| `h j k l` | Move one cell (vim-style) |
| `gh gj gk gl` | Move to edge of sheet |
| `<` / `>` | Jump to next different value in column |
| `{` / `}` | Jump to next/prev selected row |
| `Ctrl+^` | Jump to previous sheet |
| `q` | Quit current sheet |
| `gq` | Quit all sheets (global quit) |

### Search

| Key | Action |
|-----|--------|
| `/` / `?` | Search current column (regex, forward/back) |
| `g/` / `g?` | Search all visible columns |
| `n` / `N` | Next/previous match |
| `z/` / `z?` | Search by Python expression |

### Selection

| Key | Action |
|-----|--------|
| `s` / `t` / `u` | Select / toggle / unselect current row |
| `gs` / `gt` / `gu` | Select / toggle / unselect all rows |
| `\|` / `\` | Select/unselect rows matching regex in current column |
| `g\|` / `g\` | Select/unselect rows matching regex in any visible column |
| `z\|` / `z\` | Select/unselect by Python expression |
| `,` | Select rows matching current cell |
| `g,` | Select rows matching entire current row |

### Sorting

| Key | Action |
|-----|--------|
| `[` / `]` | Sort ascending/descending by current column |
| `g[` / `g]` | Sort by all key columns |
| `z[` / `z]` | Add to existing sort criteria |
| `!` | Toggle key column status |

### Column Operations

| Key | Action |
|-----|--------|
| `-` | Hide current column |
| `gv` | Unhide all columns |
| `H` / `L` | Slide column left/right |
| `^` | Rename column |
| `!` | Pin column as key column |
| `Shift+C` | Open Columns sheet |

### Column Types

| Key | Type |
|-----|------|
| `~` | string |
| `#` | int |
| `%` | float |
| `$` | currency |
| `@` | date |
| `z#` | vlen (value length) |
| `z~` | anytype |

### Editing

| Key | Action |
|-----|--------|
| `e` | Edit current cell |
| `ge TEXT` | Set current column for selected rows to TEXT |
| `g* regex TAB subst` | Find/replace in selected rows |
| `g= expr` | Evaluate Python expression on selected rows |
| `Enter` | Accept input |
| `Ctrl+C` / `Esc` | Abort input |
| `Ctrl+O` | Open cell in external `$EDITOR` |

### Derived Columns

| Key | Action |
|-----|--------|
| `=` | Create column from Python expression (`name=expr` or just `expr`) |
| `g=` | Set column value for selected rows |
| `z=` | Set column value for current row |

Available variables in expressions: column names (typed value), `vd`, `sheet`, `col`, `row`, `curcol`, `cursorCol`, `currow`.

### Aggregation & Grouping

| Key | Action |
|-----|--------|
| `+ agg` | Add aggregator to current column |
| `z+ agg` | Show aggregator result for selected rows |
| `Shift+F` | Open frequency table for current column |
| `g Shift+F` | Frequency table by all key columns |
| `Shift+I` | Open describe sheet (descriptive stats) |
| `Shift+W` | Open pivot table |

Available aggregators: `min`, `max`, `avg`/`mean`, `mode`, `median`, `sum`, `distinct`, `count`, `stdev`, `list`, `q3`/`q4`/`q5`/`q10`.

### Sheets

| Key | Action |
|-----|--------|
| `Shift+S` | Open Sheets sheet (all opened sheets) |
| `z Shift+S` | Open Sheets stack (active sheets) |
| `o` | Open a file from within vd |
| `Enter` | Jump to sheet from Sheets sheet |

### Joining & Combining

| Key | Action |
|-----|--------|
| `&` | Open join chooser (inner, outer, full, diff, extend, merge, append, concat) |
| `"` | Open duplicate sheet with selected rows |
| `g"` | Duplicate sheet with all rows, selected ones stay selected |
| `z"` | Copy of sheet with copies of selected rows (no source link) |

### Saving

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save current sheet |
| `Shift+D` | Open CommandLog sheet |
| `Ctrl+D` | Save command log |

### Graphs

| Key | Action |
|-----|--------|
| `.` | Graph current column (requires numeric x-axis set with `!`) |
| `g.` | Graph all visible numeric columns |

### Other

| Key | Action |
|-----|--------|
| `Shift+A` | New blank sheet |
| `za` / `gza N` | Add 1 / N blank columns |
| `a` / `ga N` | Add 1 / N blank rows |
| `v` | Toggle multi-line rows |
| `Ctrl+H` | Help / Commands sheet |
| `Shift+O` | Options sheet |
| `z Ctrl+S` | Save options to config |
| `Space longname` | Execute command by longname |

## Typical Workflows

### Explore → filter → save

```
vd data.csv
```
1. `!` on a column to mark it as key
2. `/` or `z|` to filter/select rows
3. `"` to open a duplicate with selected rows
4. `Ctrl+S` to save

### Format conversion (batch)

```bash
vd -b input.csv -o output.json
vd -b data.fixed -of tsv -o data.txt
```

### Batch replay a command log

```bash
vd -b -p transform.vdj input.csv -o output.csv
```

The `.vdj` file records keystrokes. To make it file-independent, remove the `open-file` line and blank all `"sheet"` values in the `.vdj`.

### Pipe processing

```bash
ps aux | vd | awk '{print $2}'            # visually inspect processes, then print selected PIDs
mysql < query.sql | vd | awk '{print $1}' # manually filter/query results
```

Use `Ctrl+Q` to output current sheet to stdout (keeps top sheet on stack). Use `q`/`gq` to quit without outputting.

## Gotchas

- **`q` vs `gq`**: `q` quits the current sheet. `gq` quits all sheets. If you just want to output data via pipe, use `Ctrl+Q`.
- **`-f` scope**: `-f csv data.txt` applies csv parsing to ALL subsequent input paths until you reset with `-f ""`.
- **File format inference**: Unknown extensions load as Text sheets. Use `-f` to force a loader.
- **Column types matter**: Sorting/filtering numerical data requires setting the column type first (`#` for int, `%` for float, `@` for date). Default is `anytype` (string-like).
- **Edits propagate**: Changes to rows on derived sheets (duplicates, frequency tables) propagate back to source sheets. Use `z"` for an independent copy.
- **`-b` is non-interactive**: Batch mode disables all UI. Use for scripted conversion and replay only.
- **Selection is global**: Selecting rows on a frequency table also selects them on the source sheet.
- **`Ctrl+Q` vs `q` in pipes**: `Ctrl+Q` outputs the current sheet to stdout. `q`/`gq` outputs nothing.
- **No undo for some operations**: Column hiding, sort changes, and some edits cannot be undone.

## Reference Files

For deep dives on specific topics, load the relevant reference from `references/`. See `references/INDEX.md` for a topic-grouped index.
