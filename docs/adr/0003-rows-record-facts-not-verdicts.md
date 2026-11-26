# 0003. Rows record what happened; the agent judges it

Status: accepted.

## Context

The brief allows facts only: no status, no balance, and transactions are never edited. Three situations have no exact `kind`: a cash discount, a set-off between the two agreements, and a credit note on an invoice that is already paid.

## Decision

- **Cash discount (s5):** a `deduction` row of EUR 100.00 on MDS-2026-08, next to the payment of EUR 4,900.00 (external_ref KOL-ZA-26-08-11, Kolbe's payment advice). The deduction has its own external_ref, DISCOUNT-MDS-2026-08.
- **Set-off (s6):** two `deduction` rows of EUR 4,100.00, one on MDS-2026-06 (`in`, external_ref SETOFF-MDS-2026-06) and one on RE-2026-0270 (`out`, SETOFF-RE-2026-0270). The mail thread SETOFF-KOL-2026-06 names both. Kolbe pays the rest of MDS-2026-06, EUR 900.00. Both books stay exact.
- **Credit note on a paid invoice (p2):** a `credit_note` row on RE-2026-0318. RE-2026-0318 then shows EUR 3,580.00 overpaid: that is the credit Meridian has to deduct, not a separate problem.
- Deductions have no `origin_tx`. The brief defines it as an earlier transaction; these fall on the same day as their payment.
- The brief says a shared `external_ref` is one transfer. So a row that moves no money never shares one: a credit note carries its credit note number, a deduction `<KIND>-<invoice>`.

## Consequences

- The ledger alone cannot tell a valid deduction from an invalid one. The agent has to read the contract and the mail.
- `validate.py` gives five warnings, and all are planted: the overpayment (p2), the late-looking payment (s8), two invoices of 4,480.00 in one month (s9), a warning about two IBANs on Kolbe's invoices (s1) and one about four IBANs in the data (s1, p1). It lists the pairs of equal invoices (s7, p4) as information.
