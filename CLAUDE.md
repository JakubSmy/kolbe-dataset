# How to work in this repo

This repo builds one dataset for the Nanzen challenge. Read this before you change anything.

## Rules

- `KOLBE/` is generated. Never edit its CSVs or `expected.json` by hand. Change `tools/build_*.py`, then rebuild.
- `KOLBE/documents/*.md` and `KOLBE/README.md` are edited directly, not generated. Claude drafts them; I review every change.
- The brief's shape is fixed: exact CSV headers, `inbound`/`outbound` on invoices and mail, `in`/`out` on transactions. Never use "vendor", "creditor", "payee" or "client", and use "account" only for a bank account. `validate.py` fails on both.
- Every amount in `expected.json` is computed or asserted in `tools/build_key.py`, and `tools/check_key.py` checks it again against the data.
- IDs in `expected.json` follow the order of `KOLBE/README.md`: the problems (p1, p2, ...), then the decoys (s1, s2, ...).

## Build and check

```
make build     # rebuild CSVs, mail and key from the scripts
make check     # validate against the brief, check every reference in the key, rebuild and diff
make lint      # ruff check and format check on tools/
make zip       # build dist/KOLBE.zip
```

`make check` and `make lint` must pass before a commit to main. CI runs both on every push to main and every pull request.

## Changes

- Commit messages say what changed and which checks passed.
- A design decision gets a short ADR in `docs/adr/` (context, decision, consequences).
- After a change to a case, run blind runs: agents that see only the data, contracts and mail. Record the result in `docs/blind-runs.md`.
