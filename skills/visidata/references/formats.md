# | VisiData

# Supported Formats

filetypeformatVisiData\_loaderVisiData saverversion\_addedcreatedcreatorPyPI dependencies[csv](#csv)Comma-Separated Values0.28displayed text0.281972[json](#json)Javascript Object Notation (JSON)0.28typed0.282001Douglas Crockford[tsv](#tsv)Tab-Separated Values0.28displayed text0.28xlsxExcel spreadsheets0.280.281987MicrosoftopenpyxlzipZIP archive format0.280.281989PKWAREhdf5Hierarchical Data Format0.280.28199xNCSAh5py[sqlite](#sqlite)sqlite0.420.422000D. Richard HippxlsExcel spreadsheets0.420.421987Microsoftxlrd[fixed](#fixed)fixed width text0.970.97[postgres](#postgres)PostgreSQL database0.970.971996[imap](#imap)Internet Message Access Protocol2.122.121988[vd](#vd)VisiData command log (TSV)0.97yes0.972017VisiData[mbtiles](#mbtiles)MapBox Tileset0.980.982011MapBoxmapbox-vector-tilepbfProtocolbuffer Binary Format0.980.982011OpenStreetMap[shp](#shp)Shapefile geographic data0.980.981993ESRIpyshp[html](#html)HTML tables0.99displayed text0.991996Dave Raggettlxmlmdmarkdown tabledisplayed text1.12008[png](#png)Portable Network Graphics (PNG) image1.1from png1.11996PNG Development Grouppypng[ttf](#ttf)TrueType Font1.11.11991Applefonttools[dot](#pcap)Graphviz diagramfrom pcap1.21991dtaStata1.21.21985StataCorppandas[geojson](#shp)Geographic JSON2.2yes (from shp and geojson)2008http://geojson.org/sas7bdatStatistical Analysis System (SAS)1.21.21976SAS Institutesas7bdatsavSPSS statistics1.21.21968SPSS IncspssSPSS statistics1.21.21968SPSS IncsavReaderWriterxptStatistical Analysis System (SAS)1.21.21976SAS Institutexport[jsonl](#json)JSON Lines1.3typed1.32013Ian Ward[pandas](#pandas)all formats supported by pandas library1.31.32008Wes McKinneypandasparquetApache Parquet1.3yes3.02013Apache Software Foundationpyarrow or pandas[pcap](#pcap)network packet capture1.31.31988LBNLdpkt dnslibpyprofPython Profile data1.31.3[xml](#xml)eXtensible Markup Language (XML)1.3from xml1.31998W3ClxmlyamlYAML Ain't Markup Language (YAML)1.31.32001Clark EvansPyYAMLfrictionlessFrictionless Data2.02.0OpenKnowledge InstitutedatapackagejiraJIRA/Confluence table markupdisplayed text2.0AtlassiannpyNumPy array format2.0typed2.0numpytarUnix Tape Archive2.02.0usvUnicode-Separated Value2.0displayed text2.01993UnicodexlsbExcel binary format2.02.0Microsoftxlrd[vdj](#vd)VisiData command log (JSON)2.0yes2.02020VisiData[mysql](#mysql)MySQL2.01995MySQL ABMySQLdbpdfPortable Document Format2.01993Adobepdfminer.sixvcfVirtual Contact File (vCard)2.01995Versit Consortiumrecrecutils database file2.0displayed text2010Jose E. MarchesiemlMultipurpose Internet Mail Extensions (MIME)2.01996Nathaniel Borenstein and Ned Freed[vds](#vd)VisiData Sheet2.2yes2.22021VisiDataodsOpenDocument Spreadsheet2.72006[OASIS](https://en.wikipedia.org/wiki/OASIS_(organization))odfpylsvawk-like key-value line-separated values2.7v2.7arrowArrow IPC file format2.92016Apache Software FoundationpyarrowarrowsArrow IPC streaming format2.92016Apache Software Foundationpyarrow[vdx](#vd)VisiData command log (text)2.11yes2.112022VisiDatamailboxAll formats supported by mailbox3.01974mailboxjrnlCLI journal3.0yes3.02012Micah Jerome Ellison[reddit](#api)Reddit API3.02005praw[matrix](#api)Matrix API3.02014The Matrix.org Foundationmatrix\_client[zulip](#api)Zulip API3.02012Kandra Labs, Inczulip[airtable](#api)Airtable API3.02012pyairtableorgmodeEmacs Orgmode format3.0yes3.02003Carsten Dominiks3Amazon S3 paths and objects3.02006Amazons3fsfecFederal Election Commission3.0Federal Election Commissionfecfilef5logParser for f5 logs3.0f5tomlTom's Obvious Minimal Language3.0Tom Preston-WernertomllibconllCoNLL annotation scheme3.0Conference on Natural Language Learningpyconll[grep](#grep)grep command-line utility3.11973AT&T Bell Laboratories

# Extra notes about formats

## tsv (Tab Separated Values), as simple as it gets

- delimiter: field delimiter to use for tsv/usv filetype (default: .)
- row\_delimiter: row delimiter to use for tsv/usv filetype (default: \\n)
- tsv _safe_ newline: replacement for newline character when saving to tsv (default: )
- tsv _safe_ tab: replacement for tab character when saving to tsv (default: .)

Use `-f usv` for Unicode separators U+241F and U+241E. Use `-f tsv` for awk-like records. Use `--delimiter=` (an empty string) to make '\\0' the value separator. Use `--row-delimiter=` to make '\\0' the row separator.

## csv (Comma Separated Values) for maximum compatibility

.csv files are a scourge upon the earth, and still regrettably common. All `csv_*` options are passed unchanged into csv.reader() and csv.writer().

- csv\_dialect: dialect passed to csv.reader (default: excel)
- Accepted dialects are `excel-tab`, `unix`, and `excel`.
- csv\_delimiter: delimiter passed to csv.reader (default: ,)
- csv\_quotechar: quotechar passed to csv.reader (default: ")
- csv\_skipinitialspace: skipinitialspace passed to csv.reader (default: True)
- csv\_escapechar: escapechar passed to csv.reader (default: None)
- csv\_lineterminator: lineterminator passed to csv.writer (default: \\n)

## Saving TSV/CSV files

- save\_filetype: specify default file type to save as (default: tsv)
- safety\_first: sanitize input/output to handle edge cases, with a performance cost (default: False)

## Useful options for text formats in general

- regex\_skip: regex of lines to skip in text sources (default: )
- save\_encoding: encoding passed to codecs.open when saving a file (default: utf8)

## fixed

- loader-specific options
  - `fixed_rows` (default: 1000) number of rows to detect fixed width columns from
  - `fixed_maxcols` (default: 0) max number of fixed-width columns to create (0 is no max)

## json

- loader-specific options
  - `json_indent` (default: None) indent to use when saving json
  - `json_sort_keys` (default: False) sort object keys when saving to json
  - `default_colname` (default: '') column name to use for non-dict rows
- Cells containing lists (e.g. `[3]`) or dicts (e.g. `{3}`) can be expanded into new columns with `(` and unexpanded with `)`.
- All expanded subcolumns must be closed (with `)`) to retain the same structure.
- Support for jsonla was added in 3.0.

## xml

- `v` show only columns in current row attributes
- `za` add column for xml attributes

## pcap

- loader-specific options
  - `pcap_internet` (default: 'n') (y/s/n) if save\_dot includes all internet hosts separately (y), combined (s), or does not include the internet (n)

## postgres

- loader-specific options
  - `postgres_schema` (default: 'public') the desired schema for the Postgres database
- `vd postgres://` _username_ `:` _password_ `@` _hostname_ `:` _port_ `/` _database_ opens a connection to the given postgres database.

## imap

- `vd "imap://user@domain.com:passwordhere@imap-mailserver.com"` opens a connection to the IMAP server

  - e.g. `vd "imap://someone@hotmail.com:pass123@imap-mail.outlook.com:993"`
  - e.g. `vd "imap://someone@gmail.com@imap.gmail.com"`
    - note that you don't specify a password for gmail here -- instead, you will be prompted to follow some instructions

### using VisiData as a pager within psql

In psql:

```
\pset format csv
\pset pager always
\setenv PSQL_PAGER 'vd -f csv'
\pset pager_min_lines
```

## sqlite

- supports saving for CREATE/INSERT (not wholesale updates)
- `z Ctrl+S` to commit any `add-row`/ `edit-cell`/ `delete-row`

## mysql

- loader-specific requirements
  - working mysql / mariadb installation or at least the `libmysqlclient-dev` package (ubuntu; name might be different on other platforms)
  - `mysqlclient` python module in path or virtual environment ( `pip install mysqlclient`)
- `vd mysql://` _username_ `:` _password_ `@` _hostname_ `:` _port_ `/` _database_ opens a connection to the given mysql / mariadb database.

## html

- loader-specific options
  - `html_title` (default: `'<h2>{sheet.name}</h2>'`) table header when saving to html
- load all `<table>` s in a web page as VisiData sheets.

## shp

- Can be edited in raw data form. Images can be plotted with `.` (dot).
- **.shp** files can be saved as **geoJSON**.

## mbtiles

- Can be edited in raw data form. Images can be plotted with `.` (dot).

## png

- Can be edited in raw data form. Images can be plotted with `.` (dot).

## ttf

- Can be edited in raw data form. Images can be plotted with `.` (dot).

## pandas

VisiData has an adapter for **pandas**. To load a file format which is supported by **pandas**, pass `-f pandas data.foo`. This will call `pandas.read_foo()`.

For example:

```
vd -f pandas data.parquet
```

loads a parquet file. When using the **pandas** loader, the `.fileformat` file extension is mandatory.

To load a hierarchy of parquet files located in folder `data/`, run

```
vd -f parquet data/
```

or rename the directory to `data.parquet` and run

```
vd data.parquet -f pandas
```

This should similarly work for any format that has a `pandas.read_format()` function.

## [VisiData Internal Formats](../internal_formats) (.vd, .vdj, .vdx, .vds)

- .vd/vdj/.vdx are command log formats suitable for VisiData scripts and macros
- .vds is a multisheet save format that includes some sheet and column metadata

## API (reddit, matrix, zulip, airtable)

- loader-specific requirements
  - require setting authentication information in `~/.visidatarc` or on the CLI
  - launch the loader with `-f loadername` for steps to obtain and configure authentication credentials

## Grep

A .grep file is a JSON lines file. It can be in two formats: 1) A simple container with three fields: file - a string with the path to the file where the match was found (absolute or relative path) line _no - an integer with the line number in the file where the match was found, text - a string with the text of the line that matched. 2) ripgrep `grep_printer` format, described here: https://docs.rs/grep-printer/latest/grep_ printer/struct.JSON.html