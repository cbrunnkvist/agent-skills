# | VisiData

# Save and Restore

## How to save and replay a VisiData session

This example creates and then uses the file [pivot.vdj](https://raw.githubusercontent.com/saulpw/visidata/stable/tests/pivot.vdj).

To save and restore a session in VisiData:

1. Save the cmdlog using _one_ of the following options:

   a. Press `Ctrl+D` to save the cmdlog to a `fn.vdj` file.

   _or_

   b. Press `Shift+D` to view the `CommandLog Sheet`, then press `Ctrl+S` and save it with a `.vdj` suffix.

2. Press `gq` to quit VisiData.

3. Replay the cmdlog, on the commandline: `vd -p fn.vdj`.


* * *

## How to replay a cmdlog on a different file

Cmdlogs record the exact filename and sheet names from the original session. To reuse a cmdlog with a different input file, you need to make the cmdlog filename-independent.

### Method: Edit the `.vd`/ `.vdj` to remove hardcoded references

1. Save your cmdlog as usual ( `Shift+D` to open the cmdlog, `Ctrl+S` to save).
2. Edit the `.vdj` file:

   - **Remove** the `open-file` line (the line with `"longname": "open-file"`).
   - **Erase all `"sheet"` values** (for instance with `gs gzd`). A blank sheet name means "use the current sheet", so commands operate on whatever is on top of the stack.
3. Replay on a new file:

`vd -b -p cmdlog.vdj newfile.csv -o output.tsv`

The new file is passed as a positional argument, and `-p` replays the cmdlog against it. Use `-b` for batch (non-interactive) mode and `-o` to write the result.

**Limitations:** Blank sheet names only work for linear workflows where you never switch between sheets. If your analysis involves joining sheets or switching back to a previous sheet, you'll need to either keep the sheet names, or use stack-relative commands like `jump-prev` ( `Ctrl+^`, jump to previous sheet) or `jump-first` ( `gCtrl+^`, jump to first sheet) to navigate between sheets without relying on their names.

### Cmdlog formats

VisiData supports several cmdlog formats:

- **`.vd`** (TSV) — original format with tab-separated columns
- **`.vdj`** (JSONL) — JSON objects, one per line; fields include `sheet`, `col`, `row`, `longname`, `input`, `keystrokes`, `comment`
- **`.vdx`** (simplified) — human-readable, one command per line; only emits `sheet`/ `col`/ `row` lines when they change

When replaying from stdin ( `vd -p -`), VisiData uses the `.vdx` loader, which accepts all three formats.

* * *