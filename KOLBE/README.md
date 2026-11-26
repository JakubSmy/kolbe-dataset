# KOLBE: Kolbe Industrietechnik GmbH

## Who this is

Kolbe (Dortmund) makes IoT gateways and sensors. It is on **both sides**:

- **Supplier** (`inbound`, `out`): framework agreement KOL-MDS-FWA-2025-001. Amendment A1 changed the bank details in March 2026.
- **Customer** (`outbound`, `in`): platform agreement MDS-KOL-SUB-2025-001, EUR 5,000.00 a month, including 250 users and 20 support hours a quarter.

## The data at a glance

| File | Rows | What it holds |
|---|---|---|
| company.csv | 1 | Kolbe |
| invoices.csv | 39 | 13 platform invoices, 26 hardware invoices |
| transactions.csv | 39 | 34 payments, 2 credit notes, 3 deductions |
| contracts.csv | 3 | Framework agreement, Amendment A1, platform agreement |
| mail.csv | 68 | Orders, invoices, returns, payment advices, support tickets |

- **Time span:** 22 September 2025 (first agreement) to 22 October 2026.
- **"Now":** Thursday 2026-10-22, the date of mail 68 (mail numbers are the `seq` column). Meridian pays Kolbe in Friday payment runs, so the next run is tomorrow.
- **Currency, terms, VAT:** EUR, Net 30, no VAT. Goods: intra-EU supplies (framework Section 4.1). Platform: reverse charge (platform Section 3.2).
- **IBANs:**
  - Kolbe old, DE04440944400047113580: framework Section 7.1, A1 Section 7.1a, mail 12 (which gives both IBANs), invoices up to RE-2026-0156.
  - Kolbe new, DE07440995700047113580: A1 Section 7.1, mails 12, 13, 57, 63, invoices from RE-2026-0174.
  - Meridian, ES4399173305310002184466: platform Section 5.1, all platform invoices.
  - Fraudulent, LT733999000012847561: only mail 67.

## The problems

**p1. Bank change confirmed on the fraudster's number** (`cross_source`; a person must decide). EUR 17,745.00 at risk.
A reply from Sabine Wörner's real but compromised mailbox asks Meridian to pay 9000010427 and 9000010571 (4,480.00 + 13,265.00) to a Lithuanian IBAN and to confirm on +49 231 000 3175 (mail 67; her real number is 3157). Meridian called that number, saw a matching bank name check, and will pay tomorrow (mail 68). A1 Section 7.2(b) allows only a call to the Managing Director's number in Section 11, +49 231 000 3141; a name check does not replace it. Section 7.3: only a payment to DE07440995700047113580 settles the debt. Next step: stop the payment, call +49 231 000 3141, let a person decide; restore DE07 in Meridian's records and warn Kolbe.

**p2. Return credited at the wrong price** (`contract`). EUR 210.00 short.
Meridian returned two gateways from RE-2026-0318 (mails 47, 51). The late credit note uses the new list price: 2 × 1,790.00 = 3,580.00 (mail 65). A1 Section 6.3 requires the order price: 2 × 1,895.00 = 3,790.00. RE-2026-0318 was already paid in full, so it shows 3,580.00 overpaid: that is this credit, waiting to be deducted. Next step: deduct it (pay 900.00 on 9000010427) or ask for a refund, and claim the 210.00 in writing. Do not deduct the 210.00 before Kolbe agrees (A1 Section 8).

**p3. Users above the plan never billed** (`collections`). EUR 475.00.
Platform Section 2.2: 25.00 a month for each user above 250, counted on the 1st. Kolbe had 262 users on 1 September and 257 on 1 October (mails 49, 58): 12 × 25.00 + 7 × 25.00. MDS-2026-09 and MDS-2026-10 bill only the fee. Next step: send a separate invoice for 475.00.

**p4. One delivery invoiced twice** (`payables`). EUR 3,200.00.
Kolbe's new ERP (mail 57) billed delivery note LS-2026-1187 again, as 9000010498 (mail 63). RE-2026-0379 billed it first (mail 59), and Meridian paid RE-2026-0379 on 9 October. The order has 12 hubs: 5 on RE-2026-0379, 7 on 9000010427 (mail 61). Next step: do not pay 9000010498. Dispute it in writing before 5 November and ask for a cancelling credit note.

## The decoys

**s1. Kolbe's IBAN changed for invoices from 1 April.** Fine: the Managing Director sent a signed letter, and Meridian called his Section 11 number in March (mails 12, 13). The March invoices on the old IBAN were paid by 24 April. A1 Section 7.1a allows that until 30 September.

**s2. 9000010571 uses the old gateway price.** Fine: the new price list (mail 57) is for orders from 1 October. This order is from 10 September (mail 56). No 735.00 overcharge.

**s3. 257 users in June.** Fine: only from 3 to 26 June (mails 29, 36). The count was 232 on 1 June and 1 July. No 175.00 due.

**s4. Q2 work logs add up to 23.5 hours.** Fine: 12 of them were a fault of Meridian's platform (mail 22) and do not count, so Q2 is 11.5 hours; Q3 is 19 hours. No 420.00 due (3.5 × 120.00).

**s5. Only 4,900.00 paid on MDS-2026-08.** Fine: Kolbe paid on the last valid day and took the 2% cash discount (platform Section 4.7, mail 45).

**s6. Only 900.00 paid on MDS-2026-06; RE-2026-0270 never paid.** Fine: a set-off of 4,100.00, agreed in writing with both invoices named (mails 33 to 35).

**s7. Two invoices of 1,560.00 and two of 4,100.00.** Fine: part deliveries of two orders (mails 19, 21).

**s8. MDS-2026-04 paid 3 days after its due date.** Fine: 1 May is a public holiday in Barcelona, then a weekend. Platform Section 4.2: a payment on the next business day is on time.

## What is deliberately clean

- Every other invoice is paid in full by its due date, on both sides.
- RE-2025-0402: 8,400.00 paid plus a 1,200.00 credit note for a returned gateway (mails 3, 4).
- Open on "now", none overdue: 9000010427 (due 29 October), 9000010571 (due 12 November), 9000010498 (p4), MDS-2026-10 (due 31 October).
- How the rows model it: the cash discount (s5) and both sides of the set-off (s6) are `deduction` rows; SETOFF-KOL-2026-06 links the two set-off rows, and no money moved.

## How I made it

I chose the four problems and eight decoys; Claude Code wrote the generators, the agreement text and the mails from those choices. A script checks every ID and sum. By hand I checked each case against its clause, the weekday of every named date, and that nothing is overdue on 22 October. p2 is from my own reselling business: a refund lower than agreed.
