# Blind runs

A blind run is a fresh Claude agent that sees only the CSVs, `documents/` and `mail.csv`: no README, no `expected.json`. Read the numbers as a sanity check of the data, not as a benchmark. The models are Claude Haiku, Sonnet and Opus as Claude Code offered them in November 2026.

## Result

Nine runs on release v1.1, the data of this release before its last wording fixes: three each for Haiku, Sonnet and Opus, each with a different prompt (short, AP clerk, auditor). Two separate Claude Opus agents marked every report against `expected.json`, and they agreed on every run.

- All nine runs found all four problems with the right amount.
- 32 of 36 next steps matched the key. The misses were soft: for example, leaving open whether to bill the 475.00 in p3.
- One Haiku run raised one false alarm, about the Q2 fault hours (s4). No other run raised a decoy.

So the set does not separate the models. What it tests is whether an agent stops at p1, and whether it applies the contract's rule rather than the ledger's obvious reading in p2 to p4. Earlier runs used one fixed prompt ([docs/blind-run-prompt.md](blind-run-prompt.md)) and changed the data as below.

## What earlier runs changed in the data

| What a run did | What I changed |
|---|---|
| Deducted the disputed 210.00 together with the credit note | The key names "paying 690.00" as a miss |
| Asked whether the June auditor users already existed on 1 June | Every user mail now says the day of the change |
| Read a quoted mail that differed from the original as a fraud sign | The quote in mail 69 now matches mail 57 word for word |

## What I take from it

- At about 40 invoices every model reads every row. A case that a model misses would need hidden evidence, and then the answer key would be unfair.
- The decoys do not trick a model that reads the contract. They catch a check that only looks at the ledger: s1, s5 to s8 and s9 look wrong to one.
- The strongest case is p1. Every run had to overrule Meridian's own mail, which says a letter, a call and a bank name check all passed.
