#!/usr/bin/env python3
"""Write KOLBE/mail.csv (the emails between Meridian and Kolbe)."""

import collections
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal

OUT = os.path.join(
    sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "KOLBE"), "mail.csv"
)
HEADER = ["seq", "thread", "direction", "sent_at", "sender", "recipient", "subject", "body", "attachment"]

AP = "ap@meridian-data.example"
AR = "ar@meridian-data.example"
KOLBE_MD = "m.kolbe@kolbe-industrietechnik.example"
WOERNER = "s.woerner@kolbe-industrietechnik.example"
REIBER = "j.reiber@kolbe-industrietechnik.example"
BRANDT = "t.brandt@kolbe-industrietechnik.example"

SIG_MARTA = "Marta Soler Vidal\nPayables team\nMeridian Data Systems S.L.\n+34 930 000 271"
SIG_PAYRUN = "Meridian Data Systems, payables team"
SIG_NURIA = "Núria Ferrer Bosch\nReceivables team\nMeridian Data Systems S.L.\n+34 930 000 274"
SIG_WOERNER = "Sabine Wörner\nReceivables team\nKolbe Industrietechnik GmbH\n+49 231 000 3157\nSensorweg 18, 44309 Dortmund\nSitz Dortmund, Amtsgericht Dortmund HRB 31853, Geschäftsführer: Matthias Kolbe"
SIG_BRANDT = "Tobias Brandt\nSales\nKolbe Industrietechnik GmbH\nSensorweg 18, 44309 Dortmund\nSitz Dortmund, Amtsgericht Dortmund HRB 31853, Geschäftsführer: Matthias Kolbe"
SIG_REIBER = "Jonas Reiber\nPayables team\nKolbe Industrietechnik GmbH\n+49 231 000 3162\nSensorweg 18, 44309 Dortmund\nSitz Dortmund, Amtsgericht Dortmund HRB 31853, Geschäftsführer: Matthias Kolbe"

ERP_SUBJECT = "Kolbe moves to a new ERP system: new invoice numbers from 28 September"
ERP_BODY_MAIN = (
    "we are moving to a new ERP system. From 28 September our invoices have 10-digit numbers "
    "starting with 9000. RE- numbers stop on that date. The invoice layout also changes a little. "
    "Deliveries that we have not invoiced by 25 September are invoiced from the new system.\n\n"
    "Our bank details do not change. Please continue to pay to Ruhrwald Genossenschaftsbank eG, "
    "IBAN DE07 4409 9570 0047 1135 80, as in Mr Kolbe's letter of 9 March.\n\n"
    "Our sales team will send you a new price list, valid for POs dated from 1 October. The KG-3 gateway, for example, "
    "goes down from EUR 1,895.00 to EUR 1,790.00.\n\n"
    "If you have any questions, just let me know."
)

mails = [
    # return in November 2025, credited at the PO price
    (
        "RET-RE-2025-0402",
        "outbound",
        "2025-11-25T09:40:00+01:00",
        AP,
        WOERNER,
        "Return: one gateway from invoice RE-2025-0402",
        "Hello Ms Wörner,\n\n"
        "One of the eight KG-2 gateways from PO-MDS-2025-0118 (invoice RE-2025-0402, delivered 20 November) does not power up "
        "(serial KG-5102). Under Section 6.3 of our framework agreement we return it; your carrier can collect it today.\n\n"
        "Please send a credit note for EUR 1,200.00.\n\n"
        "Kind regards,\n" + SIG_MARTA,
    ),
    (
        "RET-RE-2025-0402",
        "inbound",
        "2025-12-02T11:15:00+01:00",
        WOERNER,
        AP,
        "Re: Return: one gateway from invoice RE-2025-0402",
        "Hello Ms Soler,\n\n"
        "the gateway arrived on 28 November and our test confirms the fault. We have issued credit note GS-2025-0047 "
        "for EUR 1,200.00 against RE-2025-0402. Please deduct it from your payment; the rest is EUR 8,400.00.\n\n"
        "Viele Grüße\n" + SIG_WOERNER,
    ),
    # s6: set-off between the two agreements, agreed in writing (SUB 6, FWA 8), naming the invoices and amounts
    (
        "SETOFF-KOL-2026-06",
        "inbound",
        "2026-06-19T11:30:00+02:00",
        REIBER,
        AR,
        "Set-off proposal: MDS-2026-06 and RE-2026-0270",
        "Hello Ms Ferrer,\n\nwe propose to set off "
        "your invoice MDS-2026-06 (EUR 5,000.00) against our invoice RE-2026-0270 (EUR 4,100.00). We would then pay you the rest, "
        "EUR 900.00, on 26 June, and you would not pay RE-2026-0270.\n\nPlease confirm in writing.\n\nViele Grüße\n" + SIG_REIBER,
    ),
    (
        "SETOFF-KOL-2026-06",
        "outbound",
        "2026-06-22T10:15:00+02:00",
        AR,
        REIBER,
        "Re: Set-off proposal: MDS-2026-06 and RE-2026-0270",
        "Hello Mr Reiber,\n\nWe agree to this set-off: EUR 4,100.00 of MDS-2026-06 against RE-2026-0270 (EUR 4,100.00). "
        "MDS-2026-06 is settled when we receive EUR 900.00. I have asked our payables team (Marta Soler) to block RE-2026-0270 for payment.\n\n"
        "Kind regards,\n" + SIG_NURIA,
    ),
    (
        "KOL-ZA-26-06-26",
        "inbound",
        "2026-06-26T14:10:00+02:00",
        REIBER,
        AR,
        "Payment advice MDS-2026-06",
        "Hello Ms Ferrer,\n\ntoday we paid EUR 900.00 for MDS-2026-06. The other EUR 4,100.00 is the set-off of 22 June against "
        "RE-2026-0270.\n\nViele Grüße\n" + SIG_REIBER,
    ),
    # s5: Kolbe pays MDS-2026-08 on the 10th calendar day after issue, less the 2% cash discount of SUB 4.7
    (
        "KOL-ZA-26-08-11",
        "inbound",
        "2026-08-11T09:30:00+02:00",
        REIBER,
        AR,
        "Payment advice MDS-2026-08",
        "Hello Ms Ferrer,\n\ntoday we paid your invoice MDS-2026-08 of 1 August by instant transfer: EUR 5,000.00 less 2% cash discount (EUR 100.00), "
        "so EUR 4,900.00 (Skonto).\n\nViele Grüße\n" + SIG_REIBER,
    ),
    # PO-MDS-2026-0215: 32 kits in call-offs of 10, 10 and 12
    (
        "PO-MDS-2026-0215",
        "inbound",
        "2026-05-05T11:20:00+02:00",
        BRANDT,
        AP,
        "Order confirmation PO-MDS-2026-0215",
        "Hello Ms Soler,\n\nwe confirm your order PO-MDS-2026-0215 of 4 May: 32 TS-2 sensor kits at EUR 410.00 each, "
        "delivered in three call-offs of 10, 10 and 12. The first 10 ship next week.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "PO-MDS-2026-0215",
        "inbound",
        "2026-05-13T15:00:00+02:00",
        BRANDT,
        AP,
        "Shipping notice PO-MDS-2026-0215",
        "Hello Ms Soler,\n\ntoday we ship call-off 1 of your PO-MDS-2026-0215: 10 TS-2 sensor kits.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "PO-MDS-2026-0215",
        "inbound",
        "2026-06-09T14:30:00+02:00",
        BRANDT,
        AP,
        "Shipping notice PO-MDS-2026-0215",
        "Hello Ms Soler,\n\ntoday we ship call-off 2 of your PO-MDS-2026-0215: 10 TS-2 sensor kits.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "PO-MDS-2026-0215",
        "inbound",
        "2026-07-22T14:00:00+02:00",
        BRANDT,
        AP,
        "Shipping notice PO-MDS-2026-0215",
        "Hello Ms Soler,\n\ntoday we ship call-off 3 of your PO-MDS-2026-0215: the last 12 TS-2 sensor kits. With this delivery your order is complete.\n\nKind regards,\n"
        + SIG_BRANDT,
    ),
    # routine traffic
    (
        "KOL-HOLIDAY-2025",
        "inbound",
        "2025-12-10T11:00:00+01:00",
        BRANDT,
        AP,
        "Holiday closure 23 December to 6 January",
        "Dear customer,\n\nour warehouse is closed from 23 December 2025 to 6 January 2026. Orders that we confirm by "
        "16 December ship before the closure.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "PO-MDS-2026-0171",
        "inbound",
        "2026-04-22T15:30:00+02:00",
        BRANDT,
        AP,
        "Order confirmation PO-MDS-2026-0171",
        "Hello Ms Soler,\n\nwe confirm your order PO-MDS-2026-0171: 40 temperature sensors with cabling at EUR 78.00 each. "
        "We ship 20 in week 18 and 20 in week 19.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    # PO-MDS-2026-0342: shipped in two parts, billed per delivery (routine)
    (
        "PO-MDS-2026-0342",
        "inbound",
        "2026-09-10T14:20:00+02:00",
        BRANDT,
        AP,
        "Shipping notice PO-MDS-2026-0342",
        "Hello Ms Soler,\n\ntoday we ship 5 of the 12 KS-8 sensor hubs (EUR 640.00 each) on your order PO-MDS-2026-0342 of 26 August, "
        "delivery note LS-2026-1187. The other 7 follow in week 40, as confirmed.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    # decoy s9: the first invoice of the new ERP has no PO number; returned (FWA 5.2), cancelled by a full credit note and reissued (FWA 5.3)
    (
        "KOL-INV-9000010412",
        "inbound",
        "2026-09-28T08:05:00+02:00",
        "invoices@kolbe-industrietechnik.example",
        AP,
        "Invoice 9000010412",
        "This is an automatic message from Kolbe Industrietechnik GmbH.\n\n"
        "Invoice: 9000010412 of 28 September 2026\n"
        "Delivery note: LS-2026-1342 of 28 September 2026\n"
        "7 KS-8 sensor hubs at EUR 640.00: EUR 4,480.00\n"
        "Due date: 28 October 2026\n"
        "Bank: Ruhrwald Genossenschaftsbank eG, IBAN DE07 4409 9570 0047 1135 80\n\n"
        "Please do not reply to this email.",
    ),
    (
        "KOL-INV-9000010412",
        "outbound",
        "2026-09-28T13:40:00+02:00",
        AP,
        WOERNER,
        "Invoice 9000010412 returned: no PO number",
        "Hello Ms Wörner,\n\n"
        "Your invoice 9000010412 of today (EUR 4,480.00) shows no PO number, so we return it under Section 5.2 of our framework agreement. "
        "Please send us a corrected invoice.\n\n"
        "Kind regards,\n" + SIG_MARTA,
    ),
    (
        "KOL-INV-9000010412",
        "inbound",
        "2026-09-29T11:05:00+02:00",
        WOERNER,
        AP,
        "Re: Invoice 9000010412 returned: no PO number",
        "Dear Ms Soler,\n\nsorry, that was our first invoice from the new system. We cancelled 9000010412 with credit note 9000000109 "
        "and reissued it as 9000010427 with your PO number: the other 7 KS-8 sensor hubs of PO-MDS-2026-0342 (delivery note LS-2026-1342 "
        "of 28 September), 7 x EUR 640.00 = EUR 4,480.00. Please tell me if the new layout causes any problems on your side.\n\n"
        "Viele Grüße\n" + SIG_WOERNER,
    ),
    # p4: the delivery of 10 September is invoiced twice: RE-2026-0379 (old system) and 9000010498 (new system)
    (
        "KOL-INV-RE-2026-0379",
        "inbound",
        "2026-09-15T11:40:00+02:00",
        WOERNER,
        AP,
        "Invoice RE-2026-0379",
        "Dear Ms Soler,\n\nwe have sent you invoice RE-2026-0379 for the first 5 KS-8 sensor hubs of PO-MDS-2026-0342 "
        "(delivery note LS-2026-1187 of 10 September): 5 x EUR 640.00 = EUR 3,200.00.\n\nViele Grüße\n" + SIG_WOERNER,
    ),
    (
        "KOL-INV-9000010498",
        "inbound",
        "2026-10-06T08:05:00+02:00",
        "invoices@kolbe-industrietechnik.example",
        AP,
        "Invoice 9000010498",
        "This is an automatic message from Kolbe Industrietechnik GmbH.\n\n"
        "Invoice: 9000010498 of 6 October 2026\n"
        "Your order: PO-MDS-2026-0342\n"
        "Delivery note: LS-2026-1187 of 10 September 2026\n"
        "5 KS-8 sensor hubs at EUR 640.00: EUR 3,200.00\n"
        "Due date: 5 November 2026\n"
        "Bank: Ruhrwald Genossenschaftsbank eG, IBAN DE07 4409 9570 0047 1135 80\n\n"
        "Please do not reply to this email.",
    ),
    # PO-MDS-2026-0361: ordered before the new price list (decoy s2)
    (
        "PO-MDS-2026-0361",
        "inbound",
        "2026-09-11T10:30:00+02:00",
        BRANDT,
        AP,
        "Order confirmation PO-MDS-2026-0361",
        "Hello Ms Soler,\n\nwe confirm your order PO-MDS-2026-0361 of 10 September: 7 KG-3 gateways at EUR 1,895.00 each. "
        "Delivery in week 41.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "PO-MDS-2026-0289",
        "inbound",
        "2026-07-08T09:45:00+02:00",
        BRANDT,
        AP,
        "KG-3 gateways back in stock",
        "Hello Ms Soler,\n\nthe KG-3 gateways are back in stock from 15 July. Your order PO-MDS-2026-0289 (5 KG-3 gateways at EUR 1,895.00 each) ships on "
        "21 July.\n\nKind regards,\n" + SIG_BRANDT,
    ),
    (
        "KOL-BANK-2026-03",
        "inbound",
        "2026-03-09T10:12:00+01:00",
        KOLBE_MD,
        AP,
        "Change of bank details from 1 April 2026",
        "Dear Ms Soler,\n\n"
        "our bank, Volksbank Emscherbrück eG, merges into Ruhrwald Genossenschaftsbank eG on 28 March 2026. "
        "Our IBAN changes with the merger.\n\n"
        "New bank details for all invoices issued from 1 April 2026:\n"
        "Account holder: Kolbe Industrietechnik GmbH\n"
        "Bank: Ruhrwald Genossenschaftsbank eG\n"
        "IBAN: DE07 4409 9570 0047 1135 80\n\n"
        "The bank forwards payments to the old IBAN DE04 4409 4440 0047 1135 80 until 30 September 2026.\n\n"
        "The signed letter went out to you by post today. Please call me to confirm before you change anything.\n\n"
        "Mit freundlichen Grüßen\n"
        "Matthias Kolbe\n"
        "Geschäftsführer\n"
        "Kolbe Industrietechnik GmbH",
    ),
    (
        "KOL-BANK-2026-03",
        "outbound",
        "2026-03-12T15:20:00+01:00",
        AP,
        KOLBE_MD,
        "Re: Change of bank details from 1 April 2026",
        "Dear Mr Kolbe,\n\n"
        "Your letter of 9 March arrived today, thank you. I called you at 14:50 on +49 231 000 3141, the number in Section 11 of our framework agreement, and you confirmed the new IBAN "
        "DE07 4409 9570 0047 1135 80.\n\n"
        "We have updated your bank details for invoices issued from 1 April 2026.\n\n"
        "Kind regards,\n" + SIG_MARTA,
    ),
    # return in August 2026, credited in October at the wrong price (p2)
    (
        "RET-RE-2026-0318",
        "outbound",
        "2026-08-18T10:20:00+02:00",
        AP,
        WOERNER,
        "Return: two gateways from invoice RE-2026-0318",
        "Hello Ms Wörner,\n\n"
        "Two of the five gateways from PO-MDS-2026-0289 (invoice RE-2026-0318, delivered 23 July) do not power up "
        "(serials KG-7731 and KG-7734). Under Section 6.3 of our framework agreement we return them; your carrier collects them today.\n\n"
        "Please send a credit note for 2 x EUR 1,895.00 = EUR 3,790.00.\n\n"
        "Kind regards,\n" + SIG_MARTA,
    ),
    (
        "RET-RE-2026-0318",
        "inbound",
        "2026-08-24T16:05:00+02:00",
        WOERNER,
        AP,
        "Re: Return: two gateways from invoice RE-2026-0318",
        "Hello Ms Soler,\n\n"
        "both gateways arrived today and our test confirms the fault. You will receive a credit note for "
        "both units within 14 days.\n\n"
        "Viele Grüße\n" + SIG_WOERNER,
    ),
    (
        "KOL-ERP-2026-09",
        "inbound",
        "2026-09-14T13:00:00+02:00",
        WOERNER,
        AP,
        ERP_SUBJECT,
        "Dear Ms Soler,\n\n" + ERP_BODY_MAIN + "\n\nViele Grüße\n" + SIG_WOERNER,
    ),
    (
        "RET-RE-2026-0318",
        "inbound",
        "2026-10-09T14:40:00+02:00",
        WOERNER,
        AP,
        "Re: Return: two gateways from invoice RE-2026-0318",
        "Hello Ms Soler,\n\n"
        "sorry for the delay, our ERP move held it up. We have issued credit note 9000000117 for the two returned "
        "gateways (KG-7731, KG-7734): 2 x EUR 1,790.00 = EUR 3,580.00 against RE-2026-0318. You may deduct it from your next payment.\n\n"
        "Viele Grüße\n" + SIG_WOERNER,
    ),
    # p1: reply from Kolbe's real, compromised mailbox, with a forged letter; Meridian calls the number given in it
    (
        "KOL-ERP-2026-09",
        "inbound",
        "2026-10-20T16:10:00+02:00",
        WOERNER,
        AP,
        "Re: " + ERP_SUBJECT,
        "Dear Marta,\n\n"
        "with the ERP move our bank connection has changed after all. Our Managing Director's signed letter goes to you by courier today. "
        "Please pay the two open invoices below in your next payment run, and only to our new bank account:\n\n"
        "- 9000010427: EUR 4,480.00\n"
        "- 9000010571: EUR 13,265.00\n\n"
        "Account holder: Kolbe Industrietechnik GmbH\n"
        "Bank: Baltrava Payments UAB\n"
        "IBAN: LT73 3999 0000 1284 7561\n\n"
        "As the letter says, our finance office confirms the change by phone on +49 231 000 3175.\n\n"
        "Viele Grüße\n"
        "Sabine Wörner\n"
        "Receivables team\n"
        "Kolbe Industrietechnik GmbH\n\n"
        "> From: Sabine Wörner <" + WOERNER + ">\n"
        "> Sent: Monday, 14 September 2026 13:00\n"
        "> To: " + AP + "\n"
        "> Subject: " + ERP_SUBJECT + "\n"
        ">\n"
        "> Dear Ms Soler,\n"
        ">\n"
        "> we are moving to a new ERP system. From 28 September our invoices have 10-digit numbers "
        "starting with 9000. RE- numbers stop on that date. The invoice layout also changes a little.\n"
        "> ...",
    ),
    (
        "KOL-ERP-2026-09",
        "outbound",
        "2026-10-22T08:53:00+02:00",
        AP,
        WOERNER,
        "Re: " + ERP_SUBJECT,
        "Dear Ms Wörner,\n\n"
        "Mr Kolbe's signed letter arrived yesterday by courier. I then called +49 231 000 3175, the number in the letter, and your finance "
        "office confirmed the new bank account. Our bank's name check on the new IBAN, the check every euro transfer now gets, also returned a match for Kolbe Industrietechnik GmbH. We have updated our records and will pay 9000010427 and 9000010571 in our "
        "payment run on Friday, 23 October, to Baltrava Payments UAB. As you asked, this includes 9000010571, although it is due only on 12 November.\n\n"
        "Kind regards,\n" + SIG_MARTA,
    ),
]

# ---------- support tickets, as Meridian's ticket system mails them when a ticket closes ----------
# SUB 2.2: named users above 250, counted on the 1st of each month (p3, s3)
# SUB 2.3: 20 hours a quarter included; every engineer's time counts; time counts in the quarter of the work;
#          time on a fault of the Platform itself does not count (s4)
SUPPORT = "support@meridian-data.example"
HOFFMANN = "l.hoffmann@kolbe-industrietechnik.example"
TICKETS = [
    # id, closed at, title, what was done, work log [(day, engineer, hours)]
    (
        "0118",
        "2026-02-18T16:40:00+01:00",
        "SSO login fails for two new users",
        "We corrected the group mapping in your single sign-on settings.",
        [("17 Feb", "Ana Ruiz", "2.5")],
    ),
    (
        "0196",
        "2026-03-20T11:15:00+01:00",
        "Dashboard export to CSV times out",
        "Your export covered all raw telemetry, including the five years of history you imported at go-live, so we moved it to a background job.",
        [("19 Mar", "Pau Serra", "3.5")],
    ),
    (
        "0251",
        "2026-04-16T15:05:00+02:00",
        "Alert rule for warehouse temperature",
        "We set up the rule and tested it with your team.",
        [("15 Apr", "Ana Ruiz", "3.0")],
    ),
    (
        "0306",
        "2026-05-06T17:40:00+02:00",
        "Dashboards empty after the weekend",
        "The cause was an error in our database upgrade of 3 May. We restored your data and checked every dashboard with your team.",
        [("4 May", "Pau Serra", "8.0"), ("5 May", "Pau Serra", "4.0")],
    ),
    (
        "0333",
        "2026-05-21T10:30:00+02:00",
        "Telemetry gaps after KG-3 firmware 4.2",
        "Your KG-3 gateways send larger packets since firmware 4.2, so we adjusted the buffer settings of your workspace.",
        [("20 May", "Ana Ruiz", "2.25"), ("20 May", "Laia Font", "2.25")],
    ),
    (
        "0359",
        "2026-06-03T09:15:00+02:00",
        "25 temporary users for your auditors",
        "Today we created the 25 named users and will delete them on 26 June, as you asked. Your workspace now has 257 named users.",
        [],
    ),
    (
        "0402",
        "2026-06-17T14:20:00+02:00",
        "Nightly API sync hits the rate limit",
        "We raised your rate limit and split your sync into batches.",
        [("16 Jun", "Laia Font", "4.0")],
    ),
    (
        "0398",
        "2026-06-26T17:05:00+02:00",
        "Remove the auditor users",
        "Today we deleted the 25 temporary named users. Your workspace now has 232 named users.",
        [],
    ),
    (
        "0458",
        "2026-07-07T09:50:00+02:00",
        "Sensor uptime report for the warehouse",
        "We built the report and shared it with your team.",
        [("6 Jul", "Ana Ruiz", "4.0")],
    ),
    (
        "0473",
        "2026-07-10T12:05:00+02:00",
        "Login page slow",
        "This was a known fault on our side, fixed in release 26.6 for all customers.",
        [],
    ),
    (
        "0487",
        "2026-07-16T16:10:00+02:00",
        "Wrong time zone in the alert emails",
        "Your administrator had set the alerts to UTC; we changed them to Europe/Berlin.",
        [("15 Jul", "Pau Serra", "2.5")],
    ),
    (
        "0512",
        "2026-07-29T13:30:00+02:00",
        "Data retention for raw telemetry",
        "We set raw telemetry to 24 months and moved older data to the archive.",
        [("28 Jul", "Ana Ruiz", "3.0")],
    ),
    (
        "0539",
        "2026-08-06T11:45:00+02:00",
        "Map view does not load for TS-2 sensors",
        "The cause was an error in our release 26.7. To fix it we re-indexed your sensor locations; the fix is now live for all customers.",
        [],
    ),
    (
        "0566",
        "2026-08-19T15:25:00+02:00",
        "Password reset emails land in spam",
        "Our password-reset emails go out in your name, from noreply@kolbe-industrietechnik.example. Your mail settings for that domain (the SPF record) did not list our mail service, so your mail server marked the emails as spam. The cause was on your side. We sent your IT team the entry to add and checked it with them.",
        [("18 Aug", "Laia Font", "1.5")],
    ),
    (
        "0571",
        "2026-08-20T11:05:00+02:00",
        "30 new users for the Hamm site",
        "Today we created the 30 named users from your list. Your workspace now has 262 named users.",
        [],
    ),
    ("0590", "2026-08-27T09:40:00+02:00", "Question about user roles", "The answer is in our help centre, article 214.", []),
    (
        "0601",
        "2026-09-02T10:05:00+02:00",
        "Webhook to your new ERP system",
        "We set up the webhook for your ERP go-live on 28 September and tested it with your IT team on 1 September.",
        [("1 Sep", "Ana Ruiz", "3.0")],
    ),
    (
        "0628",
        "2026-09-15T10:20:00+02:00",
        "Remove five users who left",
        "Today we deleted the five named users. Your workspace now has 257 named users.",
        [],
    ),
    (
        "0634",
        "2026-09-17T14:40:00+02:00",
        "Duplicate readings from two KS-8 hubs",
        "Your team had given two hubs the same ID; we removed the duplicate readings and set new IDs.",
        [("16 Sep", "Pau Serra", "3.0")],
    ),
    (
        "0650",
        "2026-10-02T09:20:00+02:00",
        "Webhook retries after your ERP go-live",
        "Your new ERP answered slowly in its first days, so we raised the retry limit of your webhook.",
        [("1 Oct", "Laia Font", "4.5")],
    ),
    (
        "0712",
        "2026-10-15T16:00:00+02:00",
        "New dashboard for the KS-8 hubs",
        "We built the dashboard and gave your team access.",
        [("14 Oct", "Ana Ruiz", "2.0")],
    ),
]
for tid, closed, title, what, log in TICKETS:
    booked = "\n".join(f"- {d}, {who}: {h} h" for d, who, h in log) if log else "none"
    mails.append(
        (
            f"MDS-SUP-26-{tid}",
            "outbound",
            closed,
            SUPPORT,
            HOFFMANN,
            f"Ticket MDS-SUP-26-{tid} closed: {title}",
            f"Hello Ms Hoffmann,\n\nWe have closed ticket MDS-SUP-26-{tid} ({title}). {what}\n\n"
            + (f"Time booked:\n{booked}" if log else "Time booked: none.")
            + "\n\nBest regards\nMeridian Data Systems, customer support",
        )
    )

# a payment advice for every Friday payment run (Meridian's payment system sends it automatically)
D_ = Decimal
invs = {r["invoice_number"]: r for r in csv.DictReader(open(os.path.join(os.path.dirname(OUT), "invoices.csv")))}
txs = list(csv.DictReader(open(os.path.join(os.path.dirname(OUT), "transactions.csv"))))
runs = collections.OrderedDict()
for r in txs:
    if r["direction"] == "out" and r["kind"] == "payment" and r["external_ref"].startswith("MDS-PAYRUN-"):
        runs.setdefault(r["occurred_at"], []).append((r["invoice_number"], D_(r["amount"])))


def long_date(iso):
    x = datetime.fromisoformat(iso)
    return f"{x.day} {x.strftime('%B %Y')}"


have = {m[0] for m in mails}
for day, items in runs.items():
    if "MDS-PAYRUN-" + day in have:
        continue
    dd = datetime.fromisoformat(day)
    off = "+02:00" if datetime.fromisoformat("2026-03-29") <= dd < datetime.fromisoformat("2026-10-25") else "+01:00"
    lines = []
    for n, paid in items:
        inv = invs[n]
        full = D_(inv["amount"])
        cns = [t for t in txs if t["invoice_number"] == n and t["kind"] == "credit_note" and t["occurred_at"] <= day]
        if cns:
            c = cns[0]
            lines.append(
                f"{n} of {long_date(inv['issue_date'])}: EUR {full:,.2f} less your credit note {c['external_ref']} (EUR {D_(c['amount']):,.2f}): EUR {paid:,.2f}"
            )
        else:
            lines.append(f"{n} of {long_date(inv['issue_date'])}: EUR {paid:,.2f}")
    total = sum(p for _, p in items)
    paid_to = {invs[n]["iban"] for n, _ in items}
    assert len(paid_to) == 1, (day, paid_to)
    body = (
        f"Dear Ms Wörner,\n\nThis is an automatic payment advice. Today we transferred EUR {total:,.2f} to IBAN {paid_to.pop()}, "
        f"payment reference MDS-PAYRUN-{day}.\n\n"
        + "\n".join(lines)
        + (f"\nTotal: EUR {total:,.2f}" if len(items) > 1 else "")
        + "\n\n"
        + SIG_PAYRUN
    )
    mails.append(
        (
            "MDS-PAYRUN-" + day,
            "outbound",
            f"{day}T10:0{len(items)}:00{off}",
            AP,
            WOERNER,
            f"Payment advice Meridian Data Systems S.L., {dd.day} {dd.strftime('%B %Y')}",
            body,
        )
    )

DST_START = datetime.fromisoformat("2026-03-29T00:00:00")
DST_END = datetime.fromisoformat("2026-10-25T00:00:00")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(HEADER)
    for seq, (thread, direction, sent_at, sender, recipient, subject, body, *att) in enumerate(
        sorted(mails, key=lambda m: datetime.fromisoformat(m[2])), 1
    ):
        ts = datetime.fromisoformat(sent_at)
        local = ts.replace(tzinfo=None)
        expected = "+02:00" if DST_START <= local < DST_END else "+01:00"
        assert sent_at.endswith(expected), (seq, sent_at)
        w.writerow([seq, thread, direction, sent_at, sender, recipient, subject, body, att[0] if att else ""])

print(f"wrote {len(mails)} rows to {OUT}")
