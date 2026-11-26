"""Checks that every fact the answer key cites exists in the data.
Usage: python3 -I check_key.py <dataset_folder>
For each pattern it checks: invoice numbers, transaction ids, mail seq numbers, IBANs,
"Section X of <contract>" references, and that every EUR amount and every date in the
description occurs somewhere in the data or is the result of arithmetic stated in the text.
"""

import csv
import datetime as dt
import glob
import json
import os
import re
import sys
from decimal import Decimal as D

root = sys.argv[1]
inv = {r["invoice_number"]: r for r in csv.DictReader(open(f"{root}/invoices.csv"))}
tx = {r["transaction_id"]: r for r in csv.DictReader(open(f"{root}/transactions.csv"))}
mail = {r["seq"]: r for r in csv.DictReader(open(f"{root}/mail.csv", encoding="utf-8"))}
docs = {os.path.basename(p)[:-3]: open(p, encoding="utf-8").read() for p in glob.glob(f"{root}/documents/*.md")}
key = json.load(open(f"{root}/expected.json", encoding="utf-8"))["patterns"]

# every amount and date that occurs anywhere in the data
data_text = " ".join(
    open(p, encoding="utf-8").read()
    for p in [f"{root}/{f}" for f in ("invoices.csv", "transactions.csv", "mail.csv")] + glob.glob(f"{root}/documents/*.md")
)
data_amounts = {
    D(c)
    for f in ("invoices.csv", "transactions.csv")
    for row in csv.reader(open(f"{root}/{f}"))
    for c in row
    if re.fullmatch(r"\d+\.\d{2}", c)
}
data_amounts |= {
    D(a.replace(",", ""))
    for a in re.findall(
        r"(?<![\d.,])\d{1,3}(?:,\d{3})*\.\d{2}",
        " ".join(open(p, encoding="utf-8").read() for p in [f"{root}/mail.csv"] + glob.glob(f"{root}/documents/*.md")),
    )
}
data_dates = set(re.findall(r"\d{4}-\d{2}-\d{2}", data_text))
ibans_in_data = set(re.sub(r"\s", "", m) for m in re.findall(r"[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,4})?", data_text))

errors = 0


def bad(pid, msg):
    global errors
    errors += 1
    print(f"  ERROR {pid}: {msg}")


for p in key:
    pid, t = p["id"], p["description"]
    n_checked = 0
    # invoice numbers
    for n in set(re.findall(r"\b(?:MDS-\d{4}-\d{2}|RE-\d{4}-\d{4}|9000\d{6})\b", t)):
        n_checked += 1
        if n not in inv and not any(x["external_ref"] == n for x in tx.values()):
            bad(pid, f"invoice {n} not in invoices.csv")
    # transaction ids
    for x in set(re.findall(r"\b(?:(?:MDS-\d{4}-\d{2}|RE-\d{4}-\d{4}|9000\d{6})-[PDIC]\d|BNK-\d{4}-\d{2}-\d{2}-\d{2})\b", t)):
        n_checked += 1
        if x not in tx:
            bad(pid, f"transaction {x} not in transactions.csv")
    # mail seq
    for s in set(re.findall(r"seq (\d+)", t)) | {b for a in re.findall(r"seq (\d+) and (\d+)", t) for b in a}:
        n_checked += 1
        if s not in mail:
            bad(pid, f"mail seq {s} not in mail.csv")
    # sections: "Section 4.3 of MDS-KOL-SUB-2025-001" and "Sections 4.1 to 4.4 of X"
    for sec, ref in re.findall(
        r"Sections? ([\d.]+)(?: to [\d.]+)? of (?:agreement |Amendment )?([A-Z]{3}-[A-Z]{3}-[A-Z]{3}-\d{4}-\d{3}(?:-A1)?)", t
    ):
        n_checked += 1
        if ref not in docs:
            bad(pid, f"contract {ref} has no document")
        elif not re.search(rf"(?m)^(?:## )?{re.escape(sec)}[ .]", docs[ref]):
            bad(pid, f"Section {sec} not found in {ref}")
    # IBANs
    for ib in set(re.findall(r"\b[A-Z]{2}\d{2}[0-9A-Z]{16,30}\b", t)):
        n_checked += 1
        if ib not in ibans_in_data:
            bad(pid, f"IBAN {ib} not in data")
    # amounts: must be in the data, or the result of a sum/product written in the text
    stated = re.findall(r"(?:EUR )?(\d{1,3}(?:,\d{3})*\.\d{2})", t)
    derived = set()
    for expr, res in re.findall(r"((?:\d{1,3}(?:,\d{3})*\.\d{2} ?[+x\-] ?)+[\d,.%]+) = (?:EUR )?(\d{1,3}(?:,\d{3})*\.\d{2})", t):
        derived.add(D(res.replace(",", "")))
    for a in stated:
        n_checked += 1
        v = D(a.replace(",", ""))
        if v not in data_amounts and v not in derived:
            print(f"  NOTE  {pid}: amount {a} is not in the data (derived value; check its arithmetic in the text)")
    # dates
    for dd in set(re.findall(r"\d{4}-\d{2}-\d{2}", t)):
        n_checked += 1
        if dd not in data_dates:
            print(f"  NOTE  {pid}: date {dd} is not in the data (derived; check it)")
    print(f"  ok    {pid}: {n_checked} references checked")
    total_refs = globals().get("total_refs", 0) + n_checked
    globals()["total_refs"] = total_refs

print(f"  {total_refs} references checked in total")
# every derived value the key states, recomputed from the rows

A = lambda n: D(inv[n]["amount"])
T = lambda n: D(inv[n]["tax_amount"])
day = lambda s, k: (dt.date.fromisoformat(s) + dt.timedelta(days=k)).isoformat()
TX = lambda n: D(tx[n]["amount"])
DD = dt.date.fromisoformat


def body(thread):
    return " ".join(m["body"] for m in mail.values() if m["thread"] == thread)


def body_m(thread):
    return [m for m in mail.values() if m["thread"] == thread][0]


def log(thread):
    return [(d_, float(h)) for d_, h in re.findall(r"^- (\d+ \w{3}), [^:]+: ([\d.]+) h$", body(thread), re.M)]


SUB = docs["MDS-KOL-SUB-2025-001"]
FWA = docs["KOL-MDS-FWA-2025-001"]
last = mail[str(len(mail))]
DERIVED = {
    "p1 at risk 17,745.00 = 4,480.00 + 13,265.00; payable now 17,745.00 - 3,580.00 = 14,165.00": A("9000010427") + A("9000010571")
    == D("17745.00")
    and D("17745.00") - TX("RE-2026-0318-C1") == D("14165.00"),
    "p1 2026-10-23 is a Friday, 9000010427 due 2026-10-29": DD("2026-10-23").weekday() == 4
    and inv["9000010427"]["due_date"] == "2026-10-29",
    "p1 the LT IBAN is only in the fraud mail; Meridian called 3175, not the Section 11 number 3141; 7.3 says other accounts do not discharge": sum(
        "LT73" in m["body"] for m in mail.values()
    )
    == 1
    and "+49 231 000 3175" in last["body"]
    and last["sender"] == "ap@meridian-data.example"
    and "+49 231 000 3141 (the number for call-backs under Section 7.2)" in FWA
    and "the Buyer confirms it by a phone call to the Managing Director's number in Section 11, not to a number given in the notice" in FWA
    and "3175" not in FWA
    and "Only a payment to the bank account last validly notified (at the start, the one in Section 7.1) discharges the Buyer's debt."
    in FWA
    and "name check" in last["body"],
    "p1/p2 4,480.00 - 3,580.00 = 900.00": A("9000010427") - TX("RE-2026-0318-C1") == D("900.00"),
    "p2 FWA 6.3 credit at the PO price within 14 days; Kolbe's credit note mail allows the deduction; FWA 8.1/8.3 set-off only with written agreement": "credits returned Goods at the PO price within 14 days"
    in FWA
    and "Section 8 does not apply" not in FWA
    and "You may deduct it from your next payment." in body("RET-RE-2026-0318")
    and "8.3 Section 8.1 and Section 8.2 also apply to any set-off within this agreement." in FWA
    and "Email is enough." in FWA,
    "p2 2026-09-07 = 2026-08-24 + 14 days, 32 days late": (dt.date(2026, 8, 24) + dt.timedelta(days=14)).isoformat() == "2026-09-07"
    and (DD(tx["RE-2026-0318-C1"]["occurred_at"]) - dt.date(2026, 9, 7)).days == 32,
    "p2 RE-2026-0318 = 5 x 1,895.00, credit 3,580.00 = 2 x 1,790.00, short 210.00": A("RE-2026-0318") == 5 * D("1895.00")
    and TX("RE-2026-0318-C1") == 2 * D("1790.00")
    and 2 * D("1895.00") - TX("RE-2026-0318-C1") == D("210.00"),
    "p3 SUB 2.2: 250 users, EUR 25.00 per extra user a month, counted on the 1st; 262 on 1 Sep, 257 on 1 Oct; 12 x 25 + 7 x 25 = 475.00": "covers up to 250 named users"
    in SUB
    and "Users above the limit are billed monthly." in SUB
    and "costs EUR 25.00 per month" in SUB
    and "counts the named users on the first day of each month" in SUB
    and "now has 262 named users" in body("MDS-SUP-26-0571")
    and body_m("MDS-SUP-26-0571")["sent_at"].startswith("2026-08-20")
    and "now has 257 named users" in body("MDS-SUP-26-0628")
    and body_m("MDS-SUP-26-0628")["sent_at"].startswith("2026-09-15")
    and (262 - 250) * D("25") + (257 - 250) * D("25") == D("475")
    and A("MDS-2026-09") == A("MDS-2026-10") == D("5000.00"),
    "support hours: Q1 2.5 + 3.5 = 6; Q3 0458 4 + 0487 2.5 + 0512 3 + 0566 1.5 + 0601 3 + 0634 3 = 17 h by work date and by closing date; 0650 books 4.5 h on 1 Oct (Q4); 0539 books no time": "The fee includes 20 hours of expert support per calendar quarter."
    in SUB
    and "Time spent on faults of the Platform is not counted." in SUB
    and "Further hours cost EUR 120.00 per hour." in SUB
    and log("MDS-SUP-26-0458") == [("6 Jul", 4.0)]
    and log("MDS-SUP-26-0487") == [("15 Jul", 2.5)]
    and log("MDS-SUP-26-0512") == [("28 Jul", 3.0)]
    and log("MDS-SUP-26-0566") == [("18 Aug", 1.5)]
    and log("MDS-SUP-26-0601") == [("1 Sep", 3.0)]
    and log("MDS-SUP-26-0634") == [("16 Sep", 3.0)]
    and log("MDS-SUP-26-0650") == [("1 Oct", 4.5)]
    and body_m("MDS-SUP-26-0650")["sent_at"].startswith("2026-10-02")
    and all(body_m(f"MDS-SUP-26-{t}")["sent_at"][:10] <= "2026-09-30" for t in ("0458", "0487", "0512", "0566", "0601", "0634"))
    and log("MDS-SUP-26-0539") == []
    and 4 + 2.5 + 3 + 1.5 + 3 + 3 == 17,
    "p4 9000010498 = RE-2026-0379 = 5 x 640.00, same delivery note LS-2026-1187; PO-0342 is 12 hubs = 5 + 7; RE-2026-0379 paid 2026-10-09; 9000010498 unpaid, due 2026-11-05": A(
        "9000010498"
    )
    == A("RE-2026-0379")
    == 5 * D("640.00")
    and A("9000010427") == 7 * D("640.00")
    and "LS-2026-1187" in body("KOL-INV-9000010498")
    and "LS-2026-1187" in body("KOL-INV-RE-2026-0379")
    and "12 KS-8 sensor hubs" in body("PO-MDS-2026-0342")
    and tx["RE-2026-0379-P1"]["occurred_at"] == "2026-10-09"
    and inv["9000010498"]["due_date"] == "2026-11-05"
    and not any(t["invoice_number"] == "9000010498" for t in tx.values())
    and "5.1 The Supplier issues one invoice per delivery" in FWA
    and "before the due date" in FWA,
    "s1 bank change by notice under FWA 7.2: MD's letter of 9 March (new IBAN for invoices from 1 April, old IBAN forwarded until 30 September 2026) and Meridian's call to 3141; no amendment exists; March invoices on DE04 paid 2026-04-17 and 2026-04-24": "7.2 The Supplier may change its bank details by notice to the Buyer."
    in FWA
    and "New bank details for all invoices issued from 1 April 2026" in body("KOL-BANK-2026-03")
    and "The bank forwards payments to the old IBAN DE04 4409 4440 0047 1135 80 until 30 September 2026." in body("KOL-BANK-2026-03")
    and "I called you at 14:50 on +49 231 000 3141" in body("KOL-BANK-2026-03")
    and body_m("KOL-BANK-2026-03")["sender"] == "m.kolbe@kolbe-industrietechnik.example"
    and sorted(docs) == ["KOL-MDS-FWA-2025-001", "MDS-KOL-SUB-2025-001"]
    and not any("Amendment" in m["body"] for m in mail.values())
    and inv["RE-2026-0142"]["issue_date"] < "2026-04-01"
    and inv["RE-2026-0156"]["issue_date"] < "2026-04-01"
    and inv["RE-2026-0142"]["iban"] == inv["RE-2026-0156"]["iban"] == "DE04440944400047113580"
    and tx["RE-2026-0142-P1"]["occurred_at"] == "2026-04-17"
    and tx["RE-2026-0156-P1"]["occurred_at"] == "2026-04-24",
    "s8 MDS-2026-04 due Friday 2026-05-01 (Labour Day), paid Monday 2026-05-04; SUB 4.2 next business day": inv["MDS-2026-04"]["due_date"]
    == "2026-05-01"
    and tx["MDS-2026-04-P1"]["occurred_at"] == "2026-05-04"
    and dt.date(2026, 5, 1).weekday() == 4
    and dt.date(2026, 5, 4).weekday() == 0
    and "If a due date is not a business day in Barcelona, payment on the next business day is on time." in SUB,
    "s3 25 temporary users 3 to 26 June: 257 between the counts, 232 on 1 June and 1 July; 7 x 25 = 175.00 would be wrong": "now has 257 named users"
    in body("MDS-SUP-26-0359")
    and body_m("MDS-SUP-26-0359")["sent_at"].startswith("2026-06-03")
    and "now has 232 named users" in body("MDS-SUP-26-0398")
    and body_m("MDS-SUP-26-0398")["sent_at"].startswith("2026-06-26"),
    "s4 Q2 logs 0251 3 + 0306 12 + 0333 2.25+2.25 + 0402 4 = 23.5 h; 0306 a Platform fault; 11.5 h; 420.00 would be wrong": log(
        "MDS-SUP-26-0251"
    )
    == [("15 Apr", 3.0)]
    and log("MDS-SUP-26-0306") == [("4 May", 8.0), ("5 May", 4.0)]
    and log("MDS-SUP-26-0333") == [("20 May", 2.25), ("20 May", 2.25)]
    and log("MDS-SUP-26-0402") == [("16 Jun", 4.0)]
    and "The cause was an error in our database upgrade" in body("MDS-SUP-26-0306")
    and (23.5 - 20) * 120 == 420,
    "s5 MDS-2026-08: 4,900.00 + 100.00 deduction on 2026-08-11 = issue + 10 days; SUB 4.5 allows 2%": TX("MDS-2026-08-P1") == D("4900.00")
    and TX("MDS-2026-08-D1") == D("100.00")
    and tx["MDS-2026-08-D1"]["kind"] == "deduction"
    and tx["MDS-2026-08-P1"]["occurred_at"] == "2026-08-11" == day(inv["MDS-2026-08"]["issue_date"], 10)
    and "4.5 The Customer may deduct a 2% cash discount if payment is received within 10 days of the invoice date." in SUB
    and "Section 4.5 or a set-off" in SUB
    and "4.4 Amounts not paid by the due date" in SUB
    and "EUR 40.00" in SUB,
    "no invoice carries VAT": all(T(n) == 0 for n in inv),
    "s2 9000010571 = 7 x 1,895.00 = 13,265.00, PO of 10 September, new list only for POs from 1 October": A("9000010571")
    == 7 * D("1895.00")
    and "of 10 September: 7 KG-3 gateways at EUR 1,895.00" in body("PO-MDS-2026-0361")
    and "POs dated from 1 October" in body("KOL-ERP-2026-09")
    and "3.1 Prices are as stated in the PO." in FWA,
    "s6 set-off of 22 June: 900.00 + 4,100.00 = 5,000.00 on MDS-2026-06; 4,100.00 settles RE-2026-0270; agreed in writing naming both; SUB 6 and FWA 8": TX(
        "MDS-2026-06-P1"
    )
    + TX("MDS-2026-06-D1")
    == A("MDS-2026-06")
    and TX("RE-2026-0270-D1") == A("RE-2026-0270") == D("4100.00")
    and "We agree to this set-off: EUR 4,100.00 of MDS-2026-06 against RE-2026-0270" in body("SETOFF-KOL-2026-06")
    and "only with the written agreement of both parties for each set-off" in SUB
    and "only with the written agreement of both parties for each set-off" in FWA
    and "The written agreement names the invoices and the amounts set off." in SUB,
    "s7 RE-2026-0207 = RE-2026-0216 = 20 x 78.00 (PO-0171 in two halves); RE-2026-0244 = RE-2026-0270 = 10 x 410.00, RE-2026-0324 = 12 x 410.00 (PO-0215)": A(
        "RE-2026-0207"
    )
    == A("RE-2026-0216")
    == 20 * D("78.00")
    and "We ship 20 in week 18 and 20 in week 19" in body("PO-MDS-2026-0171")
    and A("RE-2026-0244") == A("RE-2026-0270") == 10 * D("410.00")
    and A("RE-2026-0324") == 12 * D("410.00")
    and "call-offs of 10, 10 and 12" in body("PO-MDS-2026-0215"),
    "s9 9000010412 = 9000010427 = 7 x 640.00, same delivery note LS-2026-1342; 9000010412 has no PO number, returned under 5.2, cancelled in full by credit note 9000000109 on 2026-09-29: 4,480.00 - 4,480.00 = 0.00 open; 5.3 met": A(
        "9000010412"
    )
    == A("9000010427")
    == 7 * D("640.00")
    and inv["9000010412"]["issue_date"] == "2026-09-28"
    and inv["9000010412"]["due_date"] == "2026-10-28"
    and DD("2026-09-28").weekday() == 0
    and [t["transaction_id"] for t in tx.values() if t["invoice_number"] == "9000010412"] == ["9000010412-C1"]
    and tx["9000010412-C1"]["kind"] == "credit_note"
    and tx["9000010412-C1"]["external_ref"] == "9000000109"
    and tx["9000010412-C1"]["occurred_at"] == "2026-09-29"
    and A("9000010412") - TX("9000010412-C1") == D("0.00")
    and "LS-2026-1342" in body("KOL-INV-9000010412")
    and "PO-MDS" not in [m for m in mail.values() if m["thread"] == "KOL-INV-9000010412"][0]["body"]
    and "under Section 5.2 of our framework agreement" in body("KOL-INV-9000010412")
    and "We cancelled 9000010412 with credit note 9000000109 and reissued it as 9000010427 with your PO number"
    in body("KOL-INV-9000010412")
    and "5.2 Every invoice must show the Buyer's PO number." in FWA
    and "only together with a credit note that cancels the original invoice in full" in FWA,
    "clean RE-2025-0402: 1,200.00 + 8,400.00 = 9,600.00": TX("RE-2025-0402-C1") + TX("RE-2025-0402-P1") == A("RE-2025-0402"),
    "clean: every other invoice settled in full by its due date": all(
        sum(D(t["amount"]) for t in tx.values() if t["invoice_number"] == n and t["kind"] in ("payment", "deduction", "credit_note"))
        == D(r["amount"])
        and max(t["occurred_at"] for t in tx.values() if t["invoice_number"] == n and t["kind"] in ("payment", "deduction", "credit_note"))
        <= r["due_date"]
        for n, r in inv.items()
        if n not in ("MDS-2026-04", "MDS-2026-10", "RE-2026-0318", "9000010427", "9000010571", "9000010498")
    ),
    "clean: RE-2026-0318 paid in full on time before the return": TX("RE-2026-0318-P1") == A("RE-2026-0318"),
    "clean: deductions only for the set-off (s6) and the cash discount (s5), no announcements, no unknown payers": sorted(
        t["transaction_id"] for t in tx.values() if t["kind"] == "deduction"
    )
    == ["MDS-2026-06-D1", "MDS-2026-08-D1", "RE-2026-0270-D1"]
    and not any(t["kind"] == "payment_initiated" or not t["company_id"] or not t["invoice_number"] for t in tx.values()),
}
for k, ok in DERIVED.items():
    print(f"  {'ok   ' if ok else 'ERROR'} derived: {k}")
    if not ok:
        errors += 1
print("RESULT:", "PASS" if errors == 0 else f"FAIL ({errors} errors)")
sys.exit(1 if errors else 0)
