# KOLBE

[![CI](https://github.com/JakubSmy/kolbe-dataset/actions/workflows/ci.yml/badge.svg)](https://github.com/JakubSmy/kolbe-dataset/actions/workflows/ci.yml)

A synthetic payables and receivables dataset for the Nanzen dataset challenge: one company, Kolbe Industrietechnik GmbH, that is both a supplier and a customer of Meridian. Four problems, eight decoys, an answer key.

**The submission is [`KOLBE/`](KOLBE/)**, also attached to the [latest release](../../releases/latest) as `KOLBE.zip`. Start with [`KOLBE/README.md`](KOLBE/README.md).

## Layout

```
KOLBE/              the dataset: README, CSVs, documents/, mail.csv, expected.json
tools/              generators (build_csv, build_mail, build_key) and checks (validate, check_key)
docs/adr/           design decisions
docs/blind-runs.md  what agents with only the data found
CLAUDE.md           instructions for the coding agent
```

## Usage

Python 3.10+, standard library only.

```
make build   # regenerate the CSVs, mail and answer key from tools/
make check   # validate against the brief, check every reference in the key, rebuild and diff
make zip     # build dist/KOLBE.zip
```

`KOLBE/README.md` and `KOLBE/documents/` are edited directly, not generated (Claude drafted them, I reviewed every change); everything else in `KOLBE/` is generated. CI runs `make check` and a lint on every push to main and every pull request; a tag builds the release.

## How it was built

I chose the cases; Claude Code wrote the generators and drafts from those choices, and I reviewed every case against its clause by hand. `make check` makes sure every invoice, mail and amount the answer key cites exists in the data. Agents that saw only the data were used as a sanity check ([docs/blind-runs.md](docs/blind-runs.md)). I iterated locally and squashed the work into a few commits before publishing.
