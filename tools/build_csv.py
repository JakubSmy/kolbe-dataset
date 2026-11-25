"""Builds the numeric part of the KOLBE dataset: company, invoices, transactions, contracts.
Every amount and date comes from this file. Mail, documents, README and expected.json are separate.
"""

import csv
import datetime as dt
import json
import os
import sys
from decimal import Decimal as D

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "KOLBE")
CID = "KOLBE"


# ---------- IBANs (ISO 13616 mod-97, plus national check digits where a country has them) ----------
def iban(country, bban):
    num = "".join(str(int(c, 36)) for c in (bban + country + "00"))
    check = 98 - int(num) % 97
    return f"{country}{check:02d}{bban}"


def es_bban(bank, branch, acct):
    w = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6]

    def dc(digits):
        s = sum(int(d) * w[i] for i, d in enumerate(digits.zfill(10)))
        r = 11 - s % 11
        return {10: 1, 11: 0}.get(r, r)

    return f"{bank}{branch}{dc('00' + bank + branch)}{dc(acct)}{acct}"


IBAN_MERIDIAN = iban("ES", es_bban("9917", "3305", "0002184466"))  # Meridian, receives Kolbe's payments
IBAN_KOLBE_OLD = iban("DE", "44094440" + "0047113580")  # Volksbank Emscherbrueck eG (before merger)
IBAN_KOLBE_NEW = iban("DE", "44099570" + "0047113580")  # Ruhrwald Genossenschaftsbank eG (after merger)
IBAN_FRAUD = iban("LT", "39990" + "00012847561")  # only in the fraudulent email


def check_iban(s):
    r = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in r)) % 97 == 1


for x in (IBAN_MERIDIAN, IBAN_KOLBE_OLD, IBAN_KOLBE_NEW, IBAN_FRAUD):
    assert check_iban(x), x

d = dt.date.fromisoformat


def net30(issue):
    return (d(issue) + dt.timedelta(days=30)).isoformat()


def m(x):
    return f"{D(x):.2f}"


# ---------- invoices ----------
FEE = D("5000.00")
inv = []
# outbound: Meridian platform licence, billed on the 1st, Net 30, reverse charge (no VAT)
months = ["2025-10", "2025-11", "2025-12"] + [f"2026-{i:02d}" for i in range(1, 11)]
for ym in months:
    issue = ym + "-01"
    inv.append(
        dict(
            invoice_number=f"MDS-{ym}",
            direction="outbound",
            issue_date=issue,
            due_date=net30(issue),
            payment_terms="Net 30",
            amount=FEE,
            tax_amount=D("0"),
            iban=IBAN_MERIDIAN,
        )
    )
# inbound: Kolbe hardware and services, Net 30, intra-EU supply (no VAT) except one
inbound = [
    ("RE-2025-0311", "2025-10-14", "14315.00", "0.00", IBAN_KOLBE_OLD),
    (
        "RE-2025-0402",
        "2025-11-18",
        "9600.00",
        "0.00",
        IBAN_KOLBE_OLD,
    ),  # 8 x 1,200.00 (KG-2, the older gateway model); one unit returned and credited at the PO price (clean)
    ("RE-2025-0477", "2025-12-16", "11425.00", "0.00", IBAN_KOLBE_OLD),
    ("RE-2026-0031", "2026-01-20", "8940.00", "0.00", IBAN_KOLBE_OLD),
    ("RE-2026-0089", "2026-02-17", "12500.00", "0.00", IBAN_KOLBE_OLD),
    ("RE-2026-0142", "2026-03-19", "7380.00", "0.00", IBAN_KOLBE_OLD),
    ("RE-2026-0191", "2026-04-21", "13050.00", "0.00", IBAN_KOLBE_NEW),
    # PO-MDS-2026-0215: 32 TS-2 sensor kits at 410.00 in call-offs of 10, 10 and 12 (RE-2026-0244 and RE-2026-0270 have the same amount: decoy s7)
    ("RE-2026-0244", "2026-05-15", "4100.00", "0.00", IBAN_KOLBE_NEW),
    ("RE-2026-0270", "2026-06-11", "4100.00", "0.00", IBAN_KOLBE_NEW),
    ("RE-2026-0324", "2026-07-24", "4920.00", "0.00", IBAN_KOLBE_NEW),
    ("RE-2026-0281", "2026-06-23", "15920.00", "0.00", IBAN_KOLBE_NEW),
    (
        "RE-2026-0318",
        "2026-07-21",
        "9475.00",
        "0.00",
        IBAN_KOLBE_NEW,
    ),  # 5 x 1,895.00; two units returned, credited at 1,790.00 instead (p2)
    ("RE-2026-0350", "2026-08-18", "6210.00", "0.00", IBAN_KOLBE_NEW),
    # PO-MDS-2026-0342: 12 KS-8 hubs at 640.00, shipped 5 + 7: RE-2026-0379 bills the 5, 9000010427 the 7
    ("9000010427", "2026-09-29", "4480.00", "0.00", IBAN_KOLBE_NEW),
    # PO-MDS-2026-0361 of 10 September: 7 KG-3 at the PO price 1,895.00, right although the list price fell on 1 October (decoy s2)
    ("9000010571", "2026-10-13", "13265.00", "0.00", IBAN_KOLBE_NEW),
    # Kolbe's new ERP invoices the delivery of 10 September (5 KS-8 hubs, delivery note LS-2026-1187) a second time:
    # RE-2026-0379 already billed and Meridian paid it on 9 October (p4)
    ("9000010498", "2026-10-06", "3200.00", "0.00", IBAN_KOLBE_NEW),
]
# PO-MDS-2026-0171 ships in two halves: RE-2026-0207 and RE-2026-0216, 20 x 78.00 each (decoy s7)
# routine orders of sensors and cabling (the brief asks for about 10 to 40 invoices), all paid in full in a Friday run before the due date
ROUTINE = [
    ("RE-2025-0338", "2025-10-28", "2340.00"),
    ("RE-2025-0439", "2025-12-02", "3615.00"),
    ("RE-2026-0012", "2026-01-08", "2090.00"),
    ("RE-2026-0107", "2026-03-03", "2880.00"),
    ("RE-2026-0156", "2026-03-31", "1345.00"),
    ("RE-2026-0174", "2026-04-08", "2215.00"),
    ("RE-2026-0207", "2026-04-28", "1560.00"),
    ("RE-2026-0216", "2026-05-05", "1560.00"),
    ("RE-2026-0331", "2026-07-30", "2430.00"),
    ("RE-2026-0379", "2026-09-15", "3200.00"),
]
# A1 Section 7.1: the new bank account applies to invoices issued from 1 April 2026
inbound += [(n, issue, amt, "0.00", IBAN_KOLBE_OLD if issue < "2026-04-01" else IBAN_KOLBE_NEW) for n, issue, amt in ROUTINE]
for n, issue, amt, tax, ib in inbound:
    inv.append(
        dict(
            invoice_number=n,
            direction="inbound",
            issue_date=issue,
            due_date=net30(issue),
            payment_terms="Net 30",
            amount=D(amt),
            tax_amount=D(tax),
            iban=ib,
        )
    )
inv.sort(key=lambda r: (r["issue_date"], r["invoice_number"]))

# ---------- transactions ----------
tx = []


def t(tid, direction, invno, when, amt, kind, ext="", method="transfer", origin="", cid=CID):
    tx.append(
        dict(
            transaction_id=tid,
            company_id=cid,
            direction=direction,
            invoice_number=invno,
            origin_tx=origin,
            occurred_at=when,
            amount=D(amt),
            currency="EUR",
            kind=kind,
            external_ref=ext,
            method=method if kind in ("payment", "payment_initiated") else "",
        )
    )


# Kolbe pays Meridian (in). Kolbe pays after the 10th day, so it takes no cash discount, except once in August (s5)
def full(inv_no, when, ref):
    t(f"{inv_no}-P1", "in", inv_no, when, FEE, "payment", ref)


full("MDS-2025-10", "2025-10-27", "KOL-ZA-25-10-27")
full("MDS-2025-11", "2025-11-20", "KOL-ZA-25-11-20")
full("MDS-2025-12", "2025-12-17", "KOL-ZA-25-12-17")
full("MDS-2026-01", "2026-01-28", "KOL-ZA-26-01-28")
full("MDS-2026-02", "2026-02-19", "KOL-ZA-26-02-19")
full("MDS-2026-03", "2026-03-24", "KOL-ZA-26-03-24")
# April: due Friday 2026-05-01, a public holiday, then a weekend: received Monday 2026-05-04, on time under SUB 4.2 (decoy s8)
full("MDS-2026-04", "2026-05-04", "KOL-ZA-26-05-04")
full("MDS-2026-05", "2026-05-28", "KOL-ZA-26-05-28")
# June: set-off agreed by email under SUB 6 and FWA 8 (mail thread SETOFF-KOL-2026-06): MDS-2026-06 (5,000.00) against
# RE-2026-0270 (4,100.00). Kolbe pays the rest, 900.00; Meridian does not pay RE-2026-0270 (decoy s6)
t("MDS-2026-06-P1", "in", "MDS-2026-06", "2026-06-26", "900.00", "payment", "KOL-ZA-26-06-26")
t("MDS-2026-06-D1", "in", "MDS-2026-06", "2026-06-26", "4100.00", "deduction", "SETOFF-KOL-2026-06", method="")
t("RE-2026-0270-D1", "out", "RE-2026-0270", "2026-06-26", "4100.00", "deduction", "SETOFF-KOL-2026-06", method="")
full("MDS-2026-07", "2026-07-28", "KOL-ZA-26-07-28")
# August: Kolbe takes the 2% cash discount of SUB 4.7 and pays on 2026-08-11, the 10th calendar day after the issue date: valid (decoy s5)
t("MDS-2026-08-P1", "in", "MDS-2026-08", "2026-08-11", "4900.00", "payment", "KOL-ZA-26-08-11")
t("MDS-2026-08-D1", "in", "MDS-2026-08", "2026-08-11", "100.00", "deduction", "KOL-ZA-26-08-11", method="")
full("MDS-2026-09", "2026-09-29", "KOL-ZA-26-09-29")
# MDS-2026-09 and MDS-2026-10 bill only the fee: the named users above 250 are not billed (p3), nor the 4 support hours above the Q3 quota (p4)

# Meridian pays Kolbe (out), Friday payment runs
for n, when in [
    ("RE-2025-0311", "2025-11-07"),
    ("RE-2025-0477", "2026-01-09"),
    ("RE-2026-0031", "2026-02-13"),
    ("RE-2026-0089", "2026-03-13"),
    ("RE-2026-0142", "2026-04-17"),
    ("RE-2026-0191", "2026-05-15"),
    ("RE-2026-0244", "2026-06-12"),
    ("RE-2026-0281", "2026-07-17"),
    ("RE-2026-0318", "2026-08-14"),
    ("RE-2026-0324", "2026-08-14"),
    ("RE-2026-0350", "2026-09-04"),
]:
    amt = next(r["amount"] for r in inv if r["invoice_number"] == n)
    t(f"{n}-P1", "out", n, when, amt, "payment", f"MDS-PAYRUN-{when}")
# routine orders: first Friday at least 21 days after issue
HOLIDAYS = {"2025-12-26", "2026-05-01", "2026-09-11"}  # Sant Esteve, Labour Day, La Diada (Catalonia): no payment run


def friday_run(issue):
    x = d(issue) + dt.timedelta(days=21)
    while x.weekday() != 4:
        x += dt.timedelta(days=1)
    if x.isoformat() in HOLIDAYS:
        x += dt.timedelta(days=7)
        if x.isoformat() > net30(issue):
            x -= dt.timedelta(days=14)
    return x.isoformat()


for n, issue, amt in ROUTINE:
    when = friday_run(issue)
    assert when <= net30(issue), n
    t(f"{n}-P1", "out", n, when, amt, "payment", f"MDS-PAYRUN-{when}")
# RE-2026-0318: two gateways returned; credit note 9000000117 from Kolbe's new ERP at 2 x 1,790.00, not the PO price 1,895.00 (p2)
t("RE-2026-0318-C1", "out", "RE-2026-0318", "2026-10-09", "3580.00", "credit_note", "9000000117", method="")
# RE-2025-0402: one gateway returned before payment, credit note GS-2025-0047 at the PO price, deducted
t("RE-2025-0402-C1", "out", "RE-2025-0402", "2025-12-02", "1200.00", "credit_note", "GS-2025-0047", method="")
t("RE-2025-0402-P1", "out", "RE-2025-0402", "2025-12-12", "8400.00", "payment", "MDS-PAYRUN-2025-12-12")
KORD = {"payment_initiated": 0, "credit_note": 1, "payment": 2, "deduction": 3}
tx.sort(key=lambda r: (r["occurred_at"], r["direction"], r["invoice_number"], KORD[r["kind"]]))

# ---------- contracts ----------
contracts = [
    ("KOL-MDS-FWA-2025-001", "2025-09-22", ""),
    ("MDS-KOL-SUB-2025-001", "2025-09-24", ""),
    ("KOL-MDS-FWA-2025-001-A1", "2026-03-09", "KOL-MDS-FWA-2025-001"),
]

# ---------- write ----------
os.makedirs(OUT + "/documents", exist_ok=True)


def w(name, header, rows):
    with open(f"{OUT}/{name}", "w", newline="") as f:
        cw = csv.writer(f, lineterminator="\n")
        cw.writerow(header)
        for r in rows:
            cw.writerow(r)


with open(f"{OUT}/company.csv", "w") as f:
    f.write('company_id,name\nKOLBE,"Kolbe Industrietechnik GmbH"\n')
w(
    "invoices.csv",
    "invoice_number,company_id,direction,issue_date,due_date,payment_terms,amount,tax_amount,currency,document_ref,iban".split(","),
    [
        [
            r["invoice_number"],
            CID,
            r["direction"],
            r["issue_date"],
            r["due_date"],
            r["payment_terms"],
            m(r["amount"]),
            m(r["tax_amount"]),
            "EUR",
            "",
            r["iban"],
        ]
        for r in inv
    ],
)
w(
    "transactions.csv",
    "transaction_id,company_id,direction,invoice_number,origin_tx,occurred_at,amount,currency,kind,external_ref,method".split(","),
    [
        [
            r["transaction_id"],
            r["company_id"],
            r["direction"],
            r["invoice_number"],
            r["origin_tx"],
            r["occurred_at"],
            m(r["amount"]),
            r["currency"],
            r["kind"],
            r["external_ref"],
            r["method"],
        ]
        for r in tx
    ],
)
w(
    "contracts.csv",
    "contract_ref,company_id,document_date,document_ref,content,supersedes".split(","),
    [[c, CID, dd, f"documents/{c}.md", "", s] for c, dd, s in contracts],
)

# facts for the doc writers and the answer key
facts = dict(IBAN_MERIDIAN=IBAN_MERIDIAN, IBAN_KOLBE_OLD=IBAN_KOLBE_OLD, IBAN_KOLBE_NEW=IBAN_KOLBE_NEW, IBAN_FRAUD=IBAN_FRAUD)
print(json.dumps(facts, indent=2))
print(len(inv), "invoices,", len(tx), "transactions")
