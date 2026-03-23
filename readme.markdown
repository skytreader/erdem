# erdem

## Instructions

1. Generate an index using the indexer (`python3 indexerdem.py`) and save this to the `backend`
directory.
2. Run the backend.
3. Run the React frontend via `npm start`.

## TUI flags

There is a command line user interface available and is the frontend currently
in active development. It is created with
[Textual](https://github.com/textualize/textual/) so developer features for it
apply. This has only been extensively tested under Linux Ubuntu.

To run, set-up an appropriate virtualenv and then

```
python -m indexer.tui
```

Or to get Textual developer options,

```
textual run --dev indexer.tui
```

Additionally, the following environment variables are also available:

`ERDEM_CSS_DEBUG` when set it shows bounding boxes of all elements in the
interface.
