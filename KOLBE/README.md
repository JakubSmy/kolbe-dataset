# KOLBE: Kolbe Industrietechnik GmbH

## Who this is

Kolbe (Dortmund, Germany) makes IoT gateways and sensors. Kolbe is a supplier and a customer of Meridian:

- **Supplier:** Kolbe sends invoices (`inbound`), Meridian pays (`out`). Framework agreement KOL-MDS-FWA-2025-001. Kolbe changed its bank details by letter in March 2026.
- **Customer:** Meridian sends invoices (`outbound`), Kolbe pays (`in`). Platform agreement MDS-KOL-SUB-2025-001: EUR 5,000.00 a month, with 250 users and 20 support hours a quarter included.

## The data

| File | Rows | Content |
|---|---|---|
| company.csv | 1 | Kolbe |
| invoices.csv | 40 | 13 platform, 27 hardware |
| transactions.csv | 40 | 34 payments, 3 credit notes, 3 deductions |
| contracts.csv | 2 | Framework agreement, platform agreement |
| mail.csv | 70 | Orders, invoices, returns, payment advices, support tickets |

- **Time span:** 22 September 2025 to 22 October 2026.
- **"Now":** Thursday 2026-10-22, the date of mail 70. ("Mail 70" is the row with `seq` 70.) Meridian pays Kolbe on Fridays, so the next payment is tomorrow.
- **Money:** EUR. Due 30 days after the invoice date. No VAT: goods go between two EU countries (framework Section 4.1); the platform is reverse charge (platform Section 3.2).
- **IBANs:**
  - Kolbe old: DE04440944400047113580. Framework Section 7.1, mail 12, invoices up to RE-2026-0156, payment advices up to 24 April 2026.
  - Kolbe new: DE07440995700047113580. Mails 12, 13, 57, 61, 65, invoices from RE-2026-0174, payment advices from 8 May 2026.
  - Meridian: ES4399173305310002184466. Platform Section 5.1, all platform invoices.
  - Fraud: LT733999000012847561. Only mail 69.

## The problems

**p1. Fraud: bank change confirmed on the fraudster's phone number** (`cross_source`, a person must decide). EUR 17,745.00.
Mail 69 comes from Sabine Wörner's real Kolbe mailbox, but a fraudster wrote it. It asks Meridian to pay 9000010427 (4,480.00) and 9000010571 (13,265.00) to the Lithuanian IBAN and to confirm on +49 231 000 3175. Her real number is 3157. In mail 70, Meridian called 3175, the bank's name check matched, and Meridian will pay tomorrow.
Rule: framework Section 7.2: confirm a bank change only by a call to the Managing Director's number in Section 11, +49 231 000 3141. A name check does not replace the call. Section 7.3: only a payment to the last validly notified bank account, DE07440995700047113580 (mails 12, 13), pays the debt.
Next step: stop the payment. Call +49 231 000 3141. A person decides. Set the IBAN back to DE07440995700047113580 and warn Kolbe. Pay 9000010427 only to DE07440995700047113580: 900.00 if the p2 credit is deducted, 4,480.00 if Kolbe refunds it.

**p2. Credit note uses the wrong price** (`contract`). EUR 210.00.
Meridian returned 2 gateways from RE-2026-0318 (mails 47, 51). Kolbe's credit note came late and uses the new list price: 2 × 1,790.00 = 3,580.00 (mail 67). Meridian had paid RE-2026-0318 in full, so RE-2026-0318 shows a balance of -3,580.00. This credit balance is part of p2, not a separate finding.
Rule: framework Section 6.3: the order price applies: 2 × 1,895.00 = 3,790.00.
Next step: deduct 3,580.00 (pay 900.00 instead of 4,480.00 on 9000010427), as Kolbe allows in mail 67, or ask Kolbe to pay it back. Ask Kolbe in writing for the missing 210.00. Do not deduct the 210.00 before Kolbe agrees (framework Section 8: set-off only with written agreement).

**p3. Extra users not invoiced** (`collections`). EUR 475.00.
Kolbe had 262 users on 1 September and 257 on 1 October (mails 49, 58). MDS-2026-09 and MDS-2026-10 charge only the monthly fee.
Rule: platform Section 2.2: 25.00 a month for each user above 250, counted on the 1st, billed monthly. 12 × 25.00 + 7 × 25.00 = 475.00.
Next step: invoice Kolbe 475.00 (separately or with the next monthly invoice).

**p4. One delivery invoiced twice** (`payables`). EUR 3,200.00.
Kolbe started a new invoicing system (mail 57). It sent 9000010498 for delivery note LS-2026-1187 (mail 65). RE-2026-0379 already charged this delivery note (mail 59), and Meridian paid it on 9 October. The order has 12 hubs: 5 on RE-2026-0379, 7 on 9000010427 (mail 63).
Next step: do not pay 9000010498. Before 5 November, tell Kolbe in writing that it is a duplicate, and ask for a credit note that cancels it.

## The decoys

A decoy looks wrong but is correct. Do not report it.

- **s1.** Kolbe's IBAN changed for invoices from 1 April, with no amendment to the agreement. Correct: framework Section 7.2 asks only for a signed letter and a call to the Section 11 number, and both happened (mails 12, 13). The March invoices were paid to the old IBAN in April (payment advices, mails 18 and 20); the letter says the bank forwards these payments until 30 September.
- **s2.** 9000010571 uses the old gateway price, 1,895.00. Correct: the new price list is for orders from 1 October (mail 57). This order is from 10 September (mail 56). Not 735.00 too much.
- **s3.** 257 users in June. Correct: only from 3 to 26 June (mails 29, 36). On 1 June and 1 July: 232. Not 175.00 due.
- **s4.** Q2 support hours add up to 23.5. Correct: 12 hours were for a fault in Meridian's platform (mail 22) and do not count (platform Section 2.3). Q2 is 11.5 hours. Not 420.00 due.
  Q3 is 17.0 hours: 4 + 2.5 + 3 + 1.5 + 3 + 3. Ticket MDS-SUP-26-0650 (mail 64) books its 4.5 hours on 1 October, so they are Q4. Nothing due for Q3.
- **s5.** Kolbe paid only 4,900.00 on MDS-2026-08. Correct: paid on the last day of the 2% early-payment discount (platform Section 4.5: within 10 days of the invoice date, 1 August + 10 days = 11 August; mail 45).
- **s6.** Kolbe paid only 900.00 on MDS-2026-06, and Meridian never paid RE-2026-0270. Correct: both agreed in writing to offset 4,100.00 between the two invoices (mails 33 to 35).
- **s7.** Two invoices of 1,560.00 and two of 4,100.00. Correct: each pair is two part deliveries of one order (mails 19, 21).
- **s8.** Kolbe paid MDS-2026-04 three days after the due date. Correct: 1 May is a public holiday in Barcelona, then a weekend. Platform Section 4.2: the next work day is on time.
- **s9.** Two invoices of 4,480.00 for the same 7 hubs (delivery note LS-2026-1342), one day apart, like p4. Correct: 9000010412 had no PO number. Meridian returned it (mails 61, 62; framework Section 5.2). Kolbe cancelled it in full with credit note 9000000109 and reissued it as 9000010427 (mail 63). 4,480.00 − 4,480.00 = 0.00 open on 9000010412. Framework Section 5.3 is met. 9000010427 is not a duplicate.

## What is clean on purpose

- All other invoices are paid in full and on time.
- RE-2025-0402: 8,400.00 paid plus a 1,200.00 credit note for a returned gateway (mails 3, 4).
- 9000010412: cancelled by credit note 9000000109 (s9), 0.00 open.
- Open on "now", none overdue: 9000010427 (due 29 October), MDS-2026-10 (due 31 October), 9000010498 (p4), 9000010571 (due 12 November).
- The discount (s5) and both sides of the offset (s6) are `deduction` rows. No money moved for them, so each has its own `external_ref` (DISCOUNT-MDS-2026-08, SETOFF-MDS-2026-06, SETOFF-RE-2026-0270), like each credit note. A shared `external_ref` means one transfer.

## How I made it

I chose the problems and decoys. Claude Code wrote the scripts, agreements and mails from my choices. A script checks every ID and amount. By hand I checked each case against its contract section, the weekday of every date named, and that nothing is overdue on 22 October. p2 comes from my own reselling business: a refund lower than agreed.
