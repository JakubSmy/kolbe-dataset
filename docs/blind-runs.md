# Blind runs

A blind run is a fresh Claude agent that sees only the CSVs, `documents/` and `mail.csv`: no README, no `expected.json`. Every run gets the same prompt ([docs/blind-run-prompt.md](blind-run-prompt.md)). I marked each report against `expected.json` myself, so read the numbers as a sanity check of the data, not as a benchmark. The models are Claude Haiku, Sonnet and Opus as Claude Code offered them in November 2026.

## Result

Six runs on these four problems: Haiku 3, Sonnet 2, Opus 1. All six found all four problems with the right amount and next step, and none raised a decoy. So with this prompt the set does not separate the models. What it tests is whether an agent stops at p1, and whether it applies the contract's rule rather than the ledger's obvious reading in p2 to p4.

Every run stopped the payment to the Lithuanian IBAN and named the Section 11 number, found the second invoice for delivery note LS-2026-1187, deducted only the issued credit note and billed 475.00 on a separate invoice. Every run explained the June set-off (s6) and the 1 May holiday (s8).

## What earlier runs changed in the data

| What a run did | What I changed |
|---|---|
| Deducted the disputed 210.00 together with the credit note | The key names "paying 690.00" as a miss |
| Asked whether the June auditor users already existed on 1 June | Every user mail now says the day of the change |
| Read a quoted mail that differed from the original as a fraud sign | The quote in mail 67 now matches mail 57 word for word |

## What I take from it

- At about 40 invoices every model reads every row. A case that a model misses would need hidden evidence, and then the answer key would be unfair.
- The decoys do not trick a model that reads the contract. They catch a check that only looks at the ledger: s1 and s5 to s8 look wrong to one.
- The strongest case is p1. Every run had to overrule Meridian's own mail, which says a letter, a call and a bank name check all passed.
