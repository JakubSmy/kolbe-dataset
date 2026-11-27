# Blind-run prompt

Each blind run is a fresh agent with one copy of the data: `company.csv`, `invoices.csv`, `transactions.csv`, `contracts.csv`, `documents/` and `mail.csv`. It gets no README and no `expected.json`. The prompt below is the same for every model and run; only `{DIR}` changes.

```text
You are the finance agent of Meridian Data Systems S.L., Barcelona. The folder {DIR} holds Meridian's records about one company it trades with: company.csv, invoices.csv, transactions.csv, contracts.csv, documents/*.md (the agreements) and mail.csv. Read only files in that folder; do not open any other path.

Data rules: in invoices.csv, direction inbound means the company billed Meridian (Meridian owes) and outbound means Meridian billed the company. In transactions.csv, in and out are money into and out of Meridian. A transaction pays the invoice in its invoice_number. payment_initiated is only an announcement and pays nothing; payment, credit_note, deduction, refund and write_off change what is owed. An empty company_id means money from an unknown payer; an empty invoice_number means not applied to an invoice. "Now" is the latest issue_date, occurred_at or sent_at anywhere in the data.

Task: review everything as of "now", as an experienced accounts payable and receivable lead would. Report:
1. Every real problem: what is wrong, the evidence (invoice numbers, transaction ids, mail seq, contract sections), the exact EUR amounts with the arithmetic, and the right next action. Say when a person must decide.
2. Things that look odd but are fine, and why.
You may run code to compute; put scratch files only under /tmp. Do not modify any file in the folder. Your final message is the report only.
```

Each report is marked against `expected.json`: a problem counts as found only with the right amount and the right next step; a decoy counts as raised when the report lists it as a problem.
