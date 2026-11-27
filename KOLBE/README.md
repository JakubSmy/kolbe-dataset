# KOLBE: Kolbe Industrietechnik GmbH

## Who this is

Kolbe (Dortmund) makes IoT gateways. It is on both sides:

- **Supplier:** Kolbe invoices (`inbound`), Meridian pays (`out`). Framework agreement KOL-MDS-FWA-2025-001.
- **Customer:** Meridian invoices (`outbound`), Kolbe pays (`in`). Platform agreement MDS-KOL-SUB-2025-001: EUR 5,000.00 a month, 250 users and 20 support hours a quarter included.

## The data

- **Rows:** company 1; invoices 40 (13 platform, 27 hardware); transactions 40 (34 payments, 3 credit notes, 3 deductions); contracts 2, each with its text in documents/; mail 70.
- **Time span:** 22 September 2025 to 22 October 2026.
- **"Now":** Thursday 2026-10-22 (mail 70).
- **Money:** EUR, Net 30, no VAT (intra-EU supply, framework 4.1; reverse charge, platform 3.2).
- **IBANs:** Kolbe old DE04440944400047113580 (framework 7.1, mail 12, invoices to RE-2026-0156, payment advices to April). Kolbe new DE07440995700047113580 (mails 12, 13, 57, 61, 65, invoices from RE-2026-0174, payment advices from May). Meridian ES4399173305310002184466 (platform 5.1, platform invoices). Fraud LT733999000012847561 (mail 69 only).

## The problems

**p1. Fraudulent bank change** (`cross_source`, a person decides). EUR 17,745.00.
Mail 69, from Sabine Wörner's hijacked mailbox, asks Meridian to pay 9000010427 (4,480.00) and 9000010571 (13,265.00) to a Lithuanian IBAN and to confirm on +49 231 000 3175 (her real number ends 3157). A forged signed letter followed; Meridian called 3175, the number in the letter; the bank name check matched, and the payment goes out tomorrow (mail 70). Framework 7.2 allows confirmation only via the Section 11 number, 3141; 7.3: only payment to the last validly notified IBAN, DE07440995700047113580, pays the debt.
Next step: stop the payment, call 3141, set the IBAN back, warn Kolbe. Pay 9000010427 there: 900.00 if the p2 credit is deducted, else 4,480.00.

**p2. Credit note at the wrong price** (`contract`). EUR 210.00.
For 2 gateways returned from RE-2026-0318 (mails 47, 51), Kolbe's credit note 9000000117 comes 32 days after the 14-day deadline and uses the new price, 2 × 1,790.00 = 3,580.00 (mail 67). Framework 6.3: the order price applies, 2 × 1,895.00 = 3,790.00. It came after full payment, so RE-2026-0318 shows -3,580.00; this is part of p2.
Next step: deduct 3,580.00 from 9000010427 (mail 67 allows it) or ask for a refund; claim 210.00 in writing, no set-off without agreement (framework 8).

**p3. Extra users not invoiced** (`collections`). EUR 475.00.
262 users on 1 September, 257 on 1 October (mails 49, 58); MDS-2026-09 and -10 bill only the fee. Platform 2.2: 25.00 a month per user above 250: 12 × 25 + 7 × 25 = 475.00.
Next step: invoice 475.00.

**p4. One delivery invoiced twice** (`payables`). EUR 3,200.00.
After its ERP move (mail 57), Kolbe invoiced delivery note LS-2026-1187 again as 9000010498 (mail 65). RE-2026-0379 already billed it (mail 59, paid 9 October). Framework 5.1: one invoice per delivery; 5.3: owed once.
Next step: do not pay; dispute in writing before the due date, 5 November (framework 5.5), and ask for a credit note.

## The decoys

- **s1.** New IBAN without amendment: framework 7.2 needs only a letter and a call to 3141, both done (mails 12, 13).
- **s2.** 9000010571 at the old price 1,895.00: the order is from 10 September, the new prices start 1 October (mails 56, 57). No claim of 7 × 105.00 = 735.00.
- **s3.** 257 users in June: only 3 to 26 June; 232 on 1 June and 1 July (mails 29, 36). No claim of 7 × 25.00 = 175.00.
- **s4.** Q2 support 23.5 hours: 12 were a Meridian fault (mail 22, platform 2.3), so 11.5. No claim of 3.5 × 120.00 = 420.00. Q3 is 17.0 hours: mail 64 books its 4.5 hours on 1 October, in Q4.
- **s5.** MDS-2026-08 paid 4,900.00: 2% discount within 10 days (platform 4.5, mail 45).
- **s6.** MDS-2026-06 paid 900.00, RE-2026-0270 unpaid: agreed set-off of 4,100.00 (mails 33 to 35).
- **s7.** Two 1,560.00 and two 4,100.00 invoices: part deliveries (mails 19, 21).
- **s8.** MDS-2026-04 paid 3 days late: 1 May holiday plus weekend (platform 4.2).
- **s9.** Two 4,480.00 invoices for the same hubs: 9000010412 lacked a PO number, was cancelled by credit note 9000000109 and reissued as 9000010427 (mails 61 to 63, framework 5.2, 5.3).

## Clean on purpose

Apart from the cases above, all invoices are paid in full and on time. RE-2025-0402 has a clean credit note, GS-2025-0047, for a returned gateway (mails 3, 4). Four invoices are open on "now", none overdue. Discount and set-off rows each have their own `external_ref`; a shared one means one transfer.

## How I made it

I chose the problems and decoys; Claude Code wrote the scripts, agreements and mails and drafted this README and the key. A script checks every ID and amount, and I checked each case by hand. p2 comes from my own reselling business: a refund lower than agreed.
