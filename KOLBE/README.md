# KOLBE: Kolbe Industrietechnik GmbH

## Who this is

Kolbe (Dortmund) makes IoT gateways. It is on both sides:

- **Supplier:** Kolbe invoices (`inbound`), Meridian pays (`out`). Framework agreement KOL-MDS-FWA-2025-001.
- **Customer:** Meridian invoices (`outbound`), Kolbe pays (`in`). Platform agreement MDS-KOL-SUB-2025-001: EUR 5,000.00 a month, 250 users and 20 support hours a quarter included.

## The data

| File | Rows | Content |
|---|---|---|
| company.csv | 1 | Kolbe |
| invoices.csv | 40 | 13 platform, 27 hardware |
| transactions.csv | 40 | 34 payments, 3 credit notes, 3 deductions |
| contracts.csv | 2 | Both agreements |
| documents/ | 2 | The agreement texts |
| mail.csv | 70 | Orders, invoices, returns, payment advices, support tickets |

- **Time span:** 22 September 2025 to 22 October 2026.
- **"Now":** Thursday 2026-10-22, the date of mail 70. Meridian pays on Fridays, so the next payment is tomorrow.
- **Money:** EUR, Net 30. No VAT: EU goods delivery (framework 4.1) and reverse charge (platform 3.2).
- **IBANs:**
  - Kolbe old, DE04440944400047113580: framework 7.1, mail 12, invoices up to RE-2026-0156, payment advices up to April.
  - Kolbe new, DE07440995700047113580: mails 12, 13, 57, 61, 65, invoices from RE-2026-0174, payment advices from May.
  - Meridian, ES4399173305310002184466: platform 5.1, platform invoices.
  - Fraud, LT733999000012847561: mail 69 only.

## The problems

**p1. Bank change confirmed on the fraudster's number** (`cross_source`, a person decides). EUR 17,745.00.
Mail 69 comes from Sabine Wörner's real mailbox, but a fraudster wrote it. It asks Meridian to pay 9000010427 (4,480.00) and 9000010571 (13,265.00) to a Lithuanian IBAN and to confirm on +49 231 000 3175. Her real number ends 3157. In mail 70, Meridian called 3175, the bank's name check matched, and the payment goes out tomorrow.
Rule: framework 7.2: confirm only by calling the Section 11 number, +49 231 000 3141. 7.3: only payment to DE07440995700047113580 pays the debt.
Next step: stop the payment. Call 3141. Set the IBAN back to DE07440995700047113580 and warn Kolbe. Pay 9000010427 only to the new IBAN: 900.00 if the p2 credit is deducted, 4,480.00 if Kolbe refunds it.

**p2. Credit note at the wrong price** (`contract`). EUR 210.00.
Meridian returned 2 gateways from RE-2026-0318 (mails 47, 51). Kolbe's late credit note uses the new list price: 2 × 1,790.00 = 3,580.00 (mail 67). RE-2026-0318 was paid in full, so it shows -3,580.00. That balance is part of p2.
Rule: framework 6.3: the order price applies, 2 × 1,895.00 = 3,790.00.
Next step: deduct 3,580.00 from 9000010427 (mail 67 allows it) or ask for a refund. Claim the missing 210.00 in writing. Do not deduct it before Kolbe agrees (framework 8).

**p3. Extra users not invoiced** (`collections`). EUR 475.00.
Kolbe had 262 users on 1 September and 257 on 1 October (mails 49, 58). MDS-2026-09 and MDS-2026-10 charge only the fee.
Rule: platform 2.2: 25.00 a month per user above 250, counted on the 1st. 12 × 25.00 + 7 × 25.00 = 475.00.
Next step: invoice Kolbe 475.00.

**p4. One delivery invoiced twice** (`payables`). EUR 3,200.00.
After its new invoicing system (mail 57), Kolbe sent 9000010498 for delivery note LS-2026-1187 (mail 65). RE-2026-0379 already charged it (mail 59), paid on 9 October. The order has 12 hubs: 5 on RE-2026-0379, 7 on 9000010427 (mail 63).
Rule: framework 5.1: one invoice per delivery; 5.3: the amount is owed only once.
Next step: do not pay 9000010498. Dispute it in writing before the due date, 5 November (framework 5.5), and ask for a credit note.

## The decoys

- **s1.** New IBAN from 1 April with no amendment. Correct: framework 7.2 needs only a signed letter and a call to 3141, and both happened (mails 12, 13). The March invoices were paid to the old IBAN (mails 18, 20); the bank forwards these until 30 September.
- **s2.** 9000010571 uses the old price, 1,895.00. Correct: the new prices are for orders from 1 October (mail 57); this order is from 10 September (mail 56). Not 735.00 too much.
- **s3.** 257 users in June. Correct: only 3 to 26 June (mails 29, 36); 232 on 1 June and 1 July. Not 175.00 due.
- **s4.** Q2 support hours are 23.5. Correct: 12 hours were a Meridian platform fault (mail 22) and do not count (platform 2.3), so Q2 is 11.5. Not 420.00 due. Q3 is 17.0; ticket MDS-SUP-26-0650 (mail 64) books its 4.5 hours on 1 October, in Q4.
- **s5.** Kolbe paid only 4,900.00 on MDS-2026-08. Correct: 2% discount, paid on day 10 (platform 4.5; 11 August; mail 45).
- **s6.** Kolbe paid only 900.00 on MDS-2026-06, and Meridian never paid RE-2026-0270. Correct: both agreed in writing to offset 4,100.00 (mails 33 to 35).
- **s7.** Two invoices of 1,560.00 and two of 4,100.00. Correct: part deliveries of one order each (mails 19, 21).
- **s8.** MDS-2026-04 paid three days late. Correct: 1 May is a Barcelona holiday, then a weekend; platform 4.2 allows the next work day.
- **s9.** Two invoices of 4,480.00 for the same 7 hubs (LS-2026-1342), like p4. Correct: 9000010412 had no PO number, Meridian returned it (mails 61, 62; framework 5.2), Kolbe cancelled it with credit note 9000000109 and reissued it as 9000010427 (mail 63). 0.00 open.

## Clean on purpose

- All other invoices are paid in full and on time. RE-2025-0402: 8,400.00 paid plus a 1,200.00 credit note (mails 3, 4).
- Open on "now", none overdue: 9000010427 (due 29 October), MDS-2026-10 (31 October), 9000010498 (p4), 9000010571 (12 November).
- The discount and the offset are `deduction` rows with their own `external_ref`. A shared `external_ref` means one transfer.

## How I made it

I chose the problems and decoys. Claude Code wrote the scripts, agreements and mails from my choices. A script checks every ID and amount. By hand I checked each case against its contract section, the weekday of every date named, and that nothing is overdue on 22 October. p2 comes from my own reselling business: a refund lower than agreed.
