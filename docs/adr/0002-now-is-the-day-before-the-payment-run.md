# 0002. "Now" is 2026-10-22, the day before the payment run

Status: accepted.

## Context

Nanzen sets "now" to the latest date in the data. That date decides what is overdue and what needs a decision today. An unpaid invoice past its due date reads as overdue, whether it was meant or not.

## Decision

The latest row is mail seq 70, sent on Thursday 2026-10-22 at 08:53 +02:00: Meridian's own mail that confirms the fraudulent bank change and says it will pay on Friday 2026-10-23. Meridian pays Kolbe in Friday runs (the `MDS-PAYRUN` references).

## Consequences

- p1 needs a person today: the payment run is tomorrow, and EUR 17,745.00 would go to the wrong bank.
- Four invoices are open on purpose, and none is overdue: 9000010427 (due 2026-10-29), MDS-2026-10 (due 2026-10-31), 9000010498 (due 2026-11-05, the duplicate of p4) and 9000010571 (due 2026-11-12).
- The duplicate 9000010498 is not due yet, so p4 is a dispute to send before 2026-11-05, not a payment to recover.
