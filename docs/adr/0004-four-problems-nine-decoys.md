# 0004. Four problems, nine decoys

Status: accepted.

## Context

The aim: problems that happen in real books, each clear to a person in one sentence, each with one right answer in the contract or the mail.

## What I tried

Blind runs on earlier candidate cases; the runs on the final set are in [docs/blind-runs.md](../blind-runs.md). At about 40 invoices a model reads every row, so the hard part is rarely finding a case. It is applying the right rule: which users count, which hours count, which amount may be deducted.

## Decision

- **p1:** a bank change "confirmed" by calling the number in the fraudster's mail, not the Section 11 number. A person must decide.
- **p2:** a return credited at the new list price, not the price of the purchase order.
- **p3:** users above 250, counted on the 1st of each month, never billed (EUR 475.00). The hardest case: the counts are only in the support mails.
- **p4:** Kolbe's ERP move invoices one delivery a second time under a new number (EUR 3,200.00). It is a different kind of case from p3: a charge billed twice, not a charge never billed.
- **Decoys:** each looks wrong to a plain check and is fine under a written rule, and each tests a different check: a valid bank change (s1), the old price on an older order (s2), a user peak between two counts (s3), Q2 hours before the platform fault is taken out (s4), a cash discount on the last valid day (s5), a set-off agreed in writing (s6), equal invoices that are part deliveries (s7), a due date on a public holiday (s8) and an invoice reissued with a full credit note, the twin of p4 (s9).
- **Key:** a problem counts as found with the right amount and the right next step. Each entry names the wrong amounts it expects.

## Consequences

- A rule-based check of the ledger raises s1 (two IBANs), s5 to s8 (a deduction, an unpaid-looking invoice, equal amounts, a late-looking payment) and s9 (two equal invoices); s2 to s4 need the price list, user counts and work logs from the mail. An agent has to read the contract and the mail before it raises an alarm.
- p1 tests what Nanzen sells: when an agent must stop and let a person decide.
