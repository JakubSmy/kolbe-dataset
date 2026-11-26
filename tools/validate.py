#!/usr/bin/env python3
"""Validator for a "Nanzen dataset challenge" dataset folder, separate from the generators.

Usage:  python3 -I validate.py <dataset_folder>

Built only from the challenge brief and the SAMPLE worked example.
Standard library only. Exit code 1 if any ERROR was reported.

Levels:
  ERROR  a rule of the brief is broken (the loader or a number on screen would be wrong)
  WARN   something a human must judge (may be a planted problem, may be a bug)
  INFO   context to read
"""

import csv
import datetime as dt
import io
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict
from decimal import ROUND_HALF_UP, Decimal

try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None

# ---------------------------------------------------------------------------
# Spec constants (from the brief)
# ---------------------------------------------------------------------------

HEADERS = OrderedDict(
    [
        ("company.csv", ["company_id", "name"]),
        (
            "invoices.csv",
            [
                "invoice_number",
                "company_id",
                "direction",
                "issue_date",
                "due_date",
                "payment_terms",
                "amount",
                "tax_amount",
                "currency",
                "document_ref",
                "iban",
            ],
        ),
        (
            "transactions.csv",
            [
                "transaction_id",
                "company_id",
                "direction",
                "invoice_number",
                "origin_tx",
                "occurred_at",
                "amount",
                "currency",
                "kind",
                "external_ref",
                "method",
            ],
        ),
        ("contracts.csv", ["contract_ref", "company_id", "document_date", "document_ref", "content", "supersedes"]),
        ("mail.csv", ["seq", "thread", "direction", "sent_at", "sender", "recipient", "subject", "body", "attachment"]),
    ]
)
REQUIRED = {
    "company.csv": ["company_id", "name"],
    "invoices.csv": ["invoice_number", "company_id", "direction", "issue_date", "due_date", "amount", "currency"],
    "transactions.csv": ["transaction_id", "direction", "occurred_at", "amount", "currency", "kind"],
    "contracts.csv": ["contract_ref", "company_id", "document_date", "document_ref"],
    "mail.csv": ["seq", "thread", "direction", "sent_at", "sender", "recipient", "subject", "body"],
}
MUST_BE_EMPTY = {
    "invoices.csv": ["document_ref"],
    "contracts.csv": ["content"],
    "mail.csv": ["attachment"],
}
INV_DIR = {"inbound", "outbound"}
TX_DIR = {"in", "out"}
MAIL_DIR = {"inbound", "outbound"}
KINDS = {"payment_initiated", "payment", "refund", "credit_note", "write_off", "deduction"}
SETTLING_PLUS = {"payment", "credit_note", "write_off", "deduction"}
SETTLING_MINUS = {"refund"}
METHODS = {"transfer", "direct_debit", "card", "cheque"}
BOOK = {"out": "inbound", "in": "outbound"}  # tx direction -> invoice direction it pays
CATEGORIES = {"payables", "collections", "contract", "cross_source", "hallucination"}
ALLOWED_TOP_FILES = {
    "README.md",
    "company.csv",
    "invoices.csv",
    "transactions.csv",
    "contracts.csv",
    "mail.csv",
    "expected.json",
    "documents",
}

IBAN_LENGTHS = {
    "AD": 24,
    "AE": 23,
    "AL": 28,
    "AT": 20,
    "AZ": 28,
    "BA": 20,
    "BE": 16,
    "BG": 22,
    "BH": 22,
    "BI": 27,
    "BR": 29,
    "BY": 28,
    "CH": 21,
    "CR": 22,
    "CY": 28,
    "CZ": 24,
    "DE": 22,
    "DJ": 27,
    "DK": 18,
    "DO": 28,
    "EE": 20,
    "EG": 29,
    "ES": 24,
    "FI": 18,
    "FK": 18,
    "FO": 18,
    "FR": 27,
    "GB": 22,
    "GE": 22,
    "GI": 23,
    "GL": 18,
    "GR": 27,
    "GT": 28,
    "HN": 28,
    "HR": 21,
    "HU": 28,
    "IE": 22,
    "IL": 23,
    "IQ": 23,
    "IS": 26,
    "IT": 27,
    "JO": 30,
    "KW": 30,
    "KZ": 20,
    "LB": 28,
    "LC": 32,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "LV": 21,
    "LY": 25,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "MK": 19,
    "MN": 20,
    "MR": 27,
    "MT": 31,
    "MU": 30,
    "NI": 28,
    "NL": 18,
    "NO": 15,
    "OM": 23,
    "PK": 24,
    "PL": 28,
    "PS": 29,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "RS": 22,
    "RU": 33,
    "SA": 24,
    "SC": 31,
    "SD": 18,
    "SE": 24,
    "SI": 19,
    "SK": 24,
    "SM": 27,
    "SO": 23,
    "ST": 25,
    "SV": 28,
    "TL": 23,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "VA": 22,
    "VG": 24,
    "XK": 20,
    "YE": 30,
}
# Standard and reduced VAT rates in use in EU member states (percent).
EU_VAT_RATES = [
    Decimal(x)
    for x in (
        "3",
        "4",
        "5",
        "5.5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "12",
        "13",
        "13.5",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "25.5",
        "27",
    )
]
COMMON_CCY = {
    "EUR",
    "USD",
    "GBP",
    "CHF",
    "SEK",
    "DKK",
    "NOK",
    "PLN",
    "CZK",
    "HUF",
    "RON",
    "BGN",
    "JPY",
    "CAD",
    "AUD",
    "CNY",
    "MXN",
    "BRL",
    "INR",
    "TRY",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AMOUNT_RE = re.compile(r"^(0|[1-9]\d*)\.\d{2}$")
CCY_RE = re.compile(r"^[A-Z]{3}$")
SENT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?([+-]\d{2}:\d{2}|Z)$")
NET_RE = re.compile(r"^Net (\d+)$")
CODENAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
# country code + 2 check digits + up to 30 alnum, optionally spaced in groups of 4
IBAN_RE = re.compile(
    r"(?<![A-Za-z0-9])([A-Z]{2}\d{2}(?:[A-Z0-9]{4,30}|(?: [A-Z0-9]{1,4}){1,8}|[A-Z0-9]{1,4}(?: [A-Z0-9]{1,4}){1,7}))(?![A-Za-z0-9])"
)

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

COUNTS = {"ERROR": 0, "WARN": 0, "INFO": 0}


def say(level, msg):
    COUNTS[level] += 1
    if level == "INFO" and os.environ.get("VERBOSE") != "1":
        return
    tag = {"ERROR": "ERROR", "WARN": "WARN ", "INFO": "INFO "}[level]
    lines = str(msg).split("\n")
    print(f"  {tag} {lines[0]}")
    for extra in lines[1:]:
        print(f"        {extra}")


def err(m):
    say("ERROR", m)


def warn(m):
    say("WARN", m)


def info(m):
    say("INFO", m)


def plain(m=""):
    print(f"        {m}" if m else "")


def section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def money(d):
    if d is None:
        return "-"
    q = d.quantize(Decimal("0.01"))
    s = f"{abs(q):,.2f}"
    return ("-" if q < 0 else "") + s


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_date(s):
    if not DATE_RE.match(s or ""):
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def parse_amount(s):
    if not AMOUNT_RE.match(s or ""):
        return None
    return Decimal(s)


def read_text(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, bom, f"not valid UTF-8: {e}"
    if bom:
        text = text[1:]
    return text, bom, None


def load_csv(folder, name, optional=False):
    """Return (rows as list of dicts with '_line', raw_text) or (None, None)."""
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        if optional:
            info(f"{name}: not present (optional)")
        else:
            err(f"{name}: missing (required file)")
        return None, None
    text, bom, problem = read_text(path)
    if problem:
        err(f"{name}: {problem}")
        return None, None
    if bom:
        err(f"{name}: starts with a UTF-8 BOM; the first header would read '\\ufeff{HEADERS[name][0]}'")
    if "\r\n" in text:
        info(f"{name}: uses CRLF line endings")
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows:
        err(f"{name}: empty file")
        return None, text
    header = rows[0]
    expected = HEADERS[name]
    first_line = text.splitlines()[0] if text else ""
    if header != expected:
        err(f"{name}: header is {header}\n      expected {expected}")
    elif first_line.strip("\r") != ",".join(expected):
        err(f"{name}: raw header line '{first_line}' is not exactly '{','.join(expected)}'")
    else:
        info(f"{name}: header OK ({len(expected)} columns)")
    out = []
    # map record index to physical line number (multi-line quoted cells shift lines)
    reader2 = csv.reader(io.StringIO(text, newline=""))
    next(reader2, None)
    phys = []
    prev = reader2.line_num
    for rec in reader2:
        phys.append(prev + 1)
        prev = reader2.line_num
    for i, rec in enumerate(rows[1:]):
        ln = phys[i] if i < len(phys) else i + 2
        if not rec or all(c == "" for c in rec) and len(rec) <= 1:
            warn(f"{name}:{ln}: blank line")
            continue
        if len(rec) != len(header):
            err(f"{name}:{ln}: {len(rec)} fields, header has {len(header)}: {rec}")
            continue
        d = dict(zip(header, rec, strict=False))
        d["_line"] = ln
        out.append(d)
        for k, v in zip(header, rec, strict=False):
            if v != v.strip() and not (name == "mail.csv" and k == "body"):
                warn(f"{name}:{ln}: {k} has leading/trailing whitespace: {v!r}")
    return out, text


def where(name, row, key=None):
    idcol = {
        "invoices.csv": "invoice_number",
        "transactions.csv": "transaction_id",
        "contracts.csv": "contract_ref",
        "mail.csv": "seq",
    }.get(name)
    s = f"{name}:{row['_line']}"
    if idcol and row.get(idcol):
        s += f" [{row[idcol]}]"
    if key:
        s += f" {key}"
    return s


# ---------------------------------------------------------------------------
# IBAN helpers
# ---------------------------------------------------------------------------


def iban_mod97_ok(iban):
    s = iban[4:] + iban[:4]
    digits = "".join(str(int(c, 36)) for c in s)
    return int(digits) % 97 == 1


def find_ibans(text):
    """Return list of (compact_iban, raw_match, offset)."""
    found = []
    for m in IBAN_RE.finditer(text):
        raw = m.group(1)
        compact = raw.replace(" ", "")
        cc = compact[:2]
        L = IBAN_LENGTHS.get(cc)
        if L and len(compact) > L:
            # Trailing token(s) grabbed (e.g. "... 8315 EUR"): cut back at a group boundary.
            parts = raw.split(" ")
            acc = ""
            for p in parts:
                if len(acc) + len(p) <= L:
                    acc += p
                else:
                    break
            if len(acc) == L:
                compact = acc
                raw = raw[: len(raw)]  # keep raw for context
        if len(compact) < 12:
            continue  # too short to be an IBAN (e.g. "ES21 VAT")
        if not any(ch.isdigit() for ch in compact[4:]):
            continue
        found.append((compact, raw, m.start()))
    return found


# ---------------------------------------------------------------------------
# Time zone helper
# ---------------------------------------------------------------------------


def last_sunday(year, month):
    d = dt.date(year, month + 1, 1) - dt.timedelta(days=1) if month < 12 else dt.date(year, 12, 31)
    while d.weekday() != 6:
        d -= dt.timedelta(days=1)
    return d


def eu_cet_offset_for_utc(utc_dt):
    """Expected CET/CEST offset (hours) for a naive UTC datetime using EU rules."""
    y = utc_dt.year
    start = dt.datetime.combine(last_sunday(y, 3), dt.time(1, 0))
    end = dt.datetime.combine(last_sunday(y, 10), dt.time(1, 0))
    return 2 if start <= utc_dt < end else 1


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    folder = os.path.abspath(argv[1])
    if not os.path.isdir(folder):
        print(f"not a folder: {folder}")
        return 2

    print(f"Nanzen dataset validator: {folder}")

    # ------------------------------------------------------------------ 1
    section("1. FILES AND SCHEMA")
    entries = sorted(os.listdir(folder))
    for e in entries:
        if e not in ALLOWED_TOP_FILES:
            warn(f"unexpected entry in dataset folder: {e}")
    for req in ("README.md", "expected.json", "documents"):
        if req not in entries:
            err(f"{req}: missing")

    company, _ = load_csv(folder, "company.csv")
    invoices, _ = load_csv(folder, "invoices.csv")
    txs, _ = load_csv(folder, "transactions.csv")
    contracts, _ = load_csv(folder, "contracts.csv")
    mail, _ = load_csv(folder, "mail.csv", optional=True)
    invoices = invoices or []
    txs = txs or []
    contracts = contracts or []
    mail = mail or []

    # company.csv
    cid = None
    if company is not None:
        if len(company) != 1:
            err(f"company.csv: {len(company)} data rows, must be exactly 1")
        if company:
            c = company[0]
            cid = c.get("company_id", "")
            info(f"company: {cid} = {c.get('name')!r}")
            if not CODENAME_RE.match(cid or ""):
                err(f"company.csv: company_id {cid!r} is not an uppercase codename")
            if not c.get("name"):
                err("company.csv: name is empty")
            raw_lines = open(os.path.join(folder, "company.csv"), encoding="utf-8-sig").read().splitlines()
            if len(raw_lines) >= 2:
                rest = raw_lines[1].split(",", 1)[1] if "," in raw_lines[1] else ""
                if not (rest.startswith('"') and rest.rstrip().endswith('"')):
                    err(f"company.csv: name is not quoted in the raw file: {raw_lines[1]!r}")
                else:
                    info("company.csv: name is quoted in the raw file")
            base = os.path.basename(folder.rstrip(os.sep))
            if cid and base != cid:
                err(f"dataset folder is named {base!r}, but company_id is {cid!r} (folder must be named after the codename)")

    def check_common(name, rows):
        for r in rows:
            for k in REQUIRED.get(name, []):
                if r.get(k, "") == "":
                    err(f"{where(name, r)}: required field {k} is empty")
            for k in MUST_BE_EMPTY.get(name, []):
                if r.get(k, "") != "":
                    err(f"{where(name, r)}: {k} must be empty, has {r[k][:60]!r}")
            if "company_id" in r and cid is not None:
                v = r["company_id"]
                if v == "" and name == "transactions.csv":
                    pass
                elif v != cid:
                    err(f"{where(name, r)}: company_id {v!r} != {cid!r}")

    check_common("invoices.csv", invoices)
    check_common("transactions.csv", txs)
    check_common("contracts.csv", contracts)
    check_common("mail.csv", mail)

    # invoices
    inv_by_no = {}
    for r in invoices:
        w = where("invoices.csv", r)
        no = r["invoice_number"]
        if no in inv_by_no:
            err(f"{w}: invoice_number {no} duplicated (also line {inv_by_no[no]['_line']})")
        else:
            inv_by_no[no] = r
        if r["direction"] not in INV_DIR:
            err(f"{w}: direction {r['direction']!r} not in {sorted(INV_DIR)}")
        r["_issue"] = parse_date(r["issue_date"])
        r["_due"] = parse_date(r["due_date"])
        for k in ("issue_date", "due_date"):
            if r[k] and parse_date(r[k]) is None:
                err(f"{w}: {k} {r[k]!r} is not a real YYYY-MM-DD date")
        r["_amount"] = parse_amount(r["amount"])
        if r["amount"] and r["_amount"] is None:
            err(f"{w}: amount {r['amount']!r} must have exactly 2 decimals, no sign, no thousands separator")
        elif r["_amount"] is not None and r["_amount"] <= 0:
            err(f"{w}: amount must be positive, is {r['amount']}")
        r["_tax"] = None
        if r["tax_amount"] != "":
            r["_tax"] = parse_amount(r["tax_amount"])
            if r["_tax"] is None:
                err(f"{w}: tax_amount {r['tax_amount']!r} must have exactly 2 decimals and be >= 0")
        if r["currency"] and not CCY_RE.match(r["currency"]):
            err(f"{w}: currency {r['currency']!r} is not 3 uppercase letters")
        elif r["currency"] and r["currency"] not in COMMON_CCY:
            warn(f"{w}: currency {r['currency']} is unusual; check it is a real ISO 4217 code")
        if r["iban"] and (" " in r["iban"] or r["iban"] != r["iban"].upper()):
            err(f"{w}: iban must be written without spaces, uppercase: {r['iban']!r}")

    # transactions
    tx_by_id = {}
    for r in txs:
        w = where("transactions.csv", r)
        tid = r["transaction_id"]
        if tid in tx_by_id:
            err(f"{w}: transaction_id {tid} duplicated (also line {tx_by_id[tid]['_line']})")
        else:
            tx_by_id[tid] = r
        if r["direction"] not in TX_DIR:
            err(f"{w}: direction {r['direction']!r} not in {sorted(TX_DIR)}")
        if r["kind"] not in KINDS:
            err(f"{w}: kind {r['kind']!r} not in {sorted(KINDS)}")
        if r["method"] and r["method"] not in METHODS:
            err(f"{w}: method {r['method']!r} not in {sorted(METHODS)} (or empty)")
        r["_date"] = parse_date(r["occurred_at"])
        if r["occurred_at"] and r["_date"] is None:
            err(f"{w}: occurred_at {r['occurred_at']!r} is not a real YYYY-MM-DD date")
        r["_amount"] = parse_amount(r["amount"])
        if r["amount"] and r["_amount"] is None:
            err(f"{w}: amount {r['amount']!r} must have exactly 2 decimals, no sign")
        elif r["_amount"] is not None and r["_amount"] <= 0:
            err(f"{w}: amount must be positive, is {r['amount']}")
        if r["currency"] and not CCY_RE.match(r["currency"]):
            err(f"{w}: currency {r['currency']!r} is not 3 uppercase letters")
        elif r["currency"] and r["currency"] not in COMMON_CCY:
            warn(f"{w}: currency {r['currency']} is unusual; check it is a real ISO 4217 code")

    # contracts
    docs_dir = os.path.join(folder, "documents")
    contract_by_ref = {}
    for r in contracts:
        w = where("contracts.csv", r)
        ref = r["contract_ref"]
        if ref in contract_by_ref:
            err(f"{w}: contract_ref {ref} duplicated")
        contract_by_ref[ref] = r
        r["_date"] = parse_date(r["document_date"])
        if r["document_date"] and r["_date"] is None:
            err(f"{w}: document_date {r['document_date']!r} is not a real YYYY-MM-DD date")
        want = f"documents/{ref}.md"
        if r["document_ref"] != want:
            err(f"{w}: document_ref {r['document_ref']!r} must be {want!r}")
        path = os.path.join(folder, want)
        if not os.path.isfile(path):
            err(f"{w}: file {want} does not exist")
        else:
            text, bom, problem = read_text(path)
            if problem:
                err(f"{want}: {problem}")
            else:
                top = "\n".join(text.splitlines()[:8])
                if ref not in top:
                    err(f"{want}: contract_ref {ref} is not printed at the top (first 8 lines)")
                else:
                    info(f"{want}: reference {ref} printed at the top")
    for r in contracts:
        w = where("contracts.csv", r)
        s = r["supersedes"]
        if s:
            if s == r["contract_ref"]:
                err(f"{w}: supersedes itself")
            elif s not in contract_by_ref:
                err(f"{w}: supersedes {s!r}, which is not a contract_ref in contracts.csv")
            else:
                old = contract_by_ref[s]
                if old.get("_date") and r.get("_date") and r["_date"] < old["_date"]:
                    warn(f"{w}: amendment dated {r['document_date']} is earlier than the contract it supersedes ({old['document_date']})")
    if os.path.isdir(docs_dir):
        for fn in sorted(os.listdir(docs_dir)):
            if not fn.endswith(".md"):
                warn(f"documents/{fn}: not a .md file")
                continue
            if fn[:-3] not in contract_by_ref:
                err(f"documents/{fn}: no contracts.csv row has contract_ref {fn[:-3]!r}")
    elif "documents" in entries:
        err("documents is not a folder")

    # mail
    seqs = {}
    for r in mail:
        w = where("mail.csv", r)
        if not re.match(r"^[1-9]\d*$", r["seq"]):
            err(f"{w}: seq {r['seq']!r} is not a positive integer")
        elif r["seq"] in seqs:
            err(f"{w}: seq {r['seq']} duplicated")
        seqs[r["seq"]] = r
        if r["direction"] not in MAIL_DIR:
            err(f"{w}: direction {r['direction']!r} not in {sorted(MAIL_DIR)}")
        m = SENT_RE.match(r["sent_at"])
        r["_date"] = None
        r["_utc"] = None
        r["_offset"] = None
        if not m:
            err(f"{w}: sent_at {r['sent_at']!r} is not ISO 8601 with a timezone offset (YYYY-MM-DDTHH:MM[:SS]+HH:MM)")
        else:
            d = parse_date(m.group(1))
            if d is None:
                err(f"{w}: sent_at date part {m.group(1)!r} is not a real date")
            try:
                ts = dt.datetime.fromisoformat(r["sent_at"].replace("Z", "+00:00"))
                r["_date"] = d
                r["_utc"] = ts.astimezone(dt.timezone.utc).replace(tzinfo=None)
                r["_offset"] = m.group(5)
                if m.group(5) == "Z":
                    warn(f"{w}: sent_at uses 'Z'; the brief asks for a timezone offset like +01:00")
            except ValueError as e:
                err(f"{w}: sent_at {r['sent_at']!r} does not parse: {e}")
        # direction vs sender (Meridian side)
        snd, rcp = r["sender"].lower(), r["recipient"].lower()
        if r["direction"] == "outbound" and "meridian" not in snd:
            warn(f"{w}: outbound mail but sender {r['sender']!r} does not look like Meridian")
        if r["direction"] == "inbound" and "meridian" in snd:
            warn(f"{w}: inbound mail but sender {r['sender']!r} looks like Meridian")
        if r["direction"] == "inbound" and "meridian" not in rcp:
            warn(f"{w}: inbound mail but recipient {r['recipient']!r} does not look like Meridian")
    if mail:
        by_seq = sorted([r for r in mail if r["seq"].isdigit()], key=lambda r: int(r["seq"]))
        for a, b in zip(by_seq, by_seq[1:], strict=False):
            if a["_utc"] and b["_utc"] and b["_utc"] < a["_utc"]:
                warn(f"mail.csv: seq {b['seq']} ({b['sent_at']}) is earlier in time than seq {a['seq']} ({a['sent_at']})")
        threads = defaultdict(list)
        for r in mail:
            threads[r["thread"]].append(r)
        for t, rs in threads.items():
            for r in rs[1:]:
                subj = r["subject"]
                if not subj.lower().startswith(("re:", "fwd:", "fw:", "aw:")) and subj != rs[0]["subject"]:
                    info(f"mail.csv seq {r['seq']}: thread {t} subject changes to {subj!r}")

    info(f"row counts: invoices {len(invoices)}, transactions {len(txs)}, contracts {len(contracts)}, mail {len(mail)}")

    # ------------------------------------------------------------------ 2
    section("2. CROSS-ROW RULES")
    for r in txs:
        w = where("transactions.csv", r)
        o = r["origin_tx"]
        if o:
            if o == r["transaction_id"]:
                err(f"{w}: origin_tx points to itself")
            elif o not in tx_by_id:
                err(f"{w}: origin_tx {o!r} is not an existing transaction_id")
            else:
                src = tx_by_id[o]
                if src["_date"] and r["_date"] and src["_date"] > r["_date"]:
                    err(f"{w}: origin_tx {o} is dated {src['occurred_at']}, later than this row ({r['occurred_at']})")
                if src["invoice_number"] != r["invoice_number"]:
                    warn(
                        f"{w}: origin_tx {o} is for invoice {src['invoice_number'] or '(none)'}, this row for {r['invoice_number'] or '(none)'}"
                    )
                if src["currency"] != r["currency"]:
                    warn(f"{w}: origin_tx {o} currency {src['currency']} != {r['currency']}")
                if r["kind"] == "payment" and src["kind"] == "payment_initiated" and src["_amount"] != r["_amount"]:
                    warn(f"{w}: lands {r['amount']} but the announcement {o} said {src['amount']}")
                if r["kind"] == "refund" and src["kind"] in ("payment", "refund") and src["direction"] == r["direction"]:
                    warn(
                        f"{w}: refund has the same direction ({r['direction']}) as the payment {o} it follows; a reversal normally moves money the other way"
                    )
                if r["kind"] == "refund" and src["_amount"] is not None and r["_amount"] is not None and r["_amount"] > src["_amount"]:
                    warn(f"{w}: refund {r['amount']} is larger than origin {o} ({src['amount']})")
        inv_no = r["invoice_number"]
        if inv_no:
            inv = inv_by_no.get(inv_no)
            if inv is None:
                err(f"{w}: invoice_number {inv_no!r} does not exist in invoices.csv")
                continue
            if r["direction"] in BOOK and inv["direction"] in INV_DIR and BOOK[r["direction"]] != inv["direction"]:
                warn(
                    f"{w}: direction '{r['direction']}' ({r['kind']}) against {inv['direction']} invoice {inv_no}: "
                    f"wrong book, so under rule 5 this row settles NOTHING"
                )
            if r["currency"] != inv["currency"]:
                warn(f"{w}: currency {r['currency']} != invoice {inv_no} currency {inv['currency']}: under rule 5 this row settles NOTHING")
            if inv["_issue"] and r["_date"] and r["_date"] < inv["_issue"] and r["kind"] != "payment_initiated":
                warn(f"{w}: {r['kind']} on {r['occurred_at']} is before invoice {inv_no} was issued ({inv['issue_date']})")
    for r in invoices:
        w = where("invoices.csv", r)
        if r["_tax"] is not None and r["_amount"] is not None and r["_tax"] > r["_amount"]:
            err(f"{w}: tax_amount {r['tax_amount']} > amount {r['amount']}")
        if r["_issue"] and r["_due"]:
            if r["_due"] < r["_issue"]:
                err(f"{w}: due_date {r['due_date']} is before issue_date {r['issue_date']}")
            pt = r["payment_terms"]
            m = NET_RE.match(pt)
            if m:
                want = r["_issue"] + dt.timedelta(days=int(m.group(1)))
                if r["_due"] != want:
                    err(
                        f"{w}: payment_terms '{pt}' from {r['issue_date']} gives {want}, but due_date is {r['due_date']} "
                        f"({(r['_due'] - r['_issue']).days} days)"
                    )
            elif pt:
                if re.match(r"^net\s*\d+$", pt, re.I):
                    warn(f"{w}: payment_terms {pt!r} looks like Net N but is not written 'Net N' exactly; due date not checked")
                else:
                    info(
                        f"{w}: payment_terms {pt!r} is not 'Net N'; due date not checked ({(r['_due'] - r['_issue']).days} days after issue)"
                    )
            else:
                info(f"{w}: no payment_terms; due {(r['_due'] - r['_issue']).days} days after issue")

    # ------------------------------------------------------------------ 3
    section('3. "NOW"')
    cands = []
    for r in invoices:
        if r["_issue"]:
            cands.append((r["_issue"], f"invoices.csv:{r['_line']} issue_date of {r['invoice_number']}"))
    for r in txs:
        if r["_date"]:
            cands.append((r["_date"], f"transactions.csv:{r['_line']} occurred_at of {r['transaction_id']}"))
    for r in mail:
        if r["_date"]:
            cands.append((r["_date"], f"mail.csv:{r['_line']} sent_at of seq {r['seq']} ({r['sent_at']})"))
    now = None
    if not cands:
        err('no dates found; cannot work out "now"')
    else:
        now = max(d for d, _ in cands)
        setters = [s for d, s in cands if d == now]
        print(f"  NOW = {now.isoformat()}  ({now.strftime('%A')})")
        for s in setters:
            plain(f"set by {s}")
        all_dates = [d for d, _ in cands] + [r["_due"] for r in invoices if r["_due"]] + [r["_date"] for r in contracts if r.get("_date")]
        span_start = min(all_dates)
        months = (now.year - span_start.year) * 12 + (now.month - span_start.month)
        info(f"time span: {span_start} to {now} (about {months} months; the brief suggests 6 to 18)")
        if not (10 <= len(invoices) <= 40):
            info(f"{len(invoices)} invoices (the brief suggests about 10 to 40)")
        for r in invoices:
            if r["_due"] and r["_due"] > now:
                info(f"invoices.csv:{r['_line']} {r['invoice_number']} due_date {r['due_date']} is after now (not yet due)")
        for r in contracts:
            if r.get("_date") and r["_date"] > now:
                warn(
                    f"contracts.csv:{r['_line']} {r['contract_ref']} document_date {r['document_date']} is after now; "
                    f"document_date does NOT move now"
                )
        readme = os.path.join(folder, "README.md")
        if os.path.isfile(readme):
            rt = open(readme, encoding="utf-8", errors="replace").read()
            if now.isoformat() not in rt:
                warn(f'README.md does not mention now = {now.isoformat()} (the brief: state your "now" in the README)')
            else:
                info(f"README.md states {now.isoformat()}")

    # ------------------------------------------------------------------ 4
    section("4. LEDGER PER INVOICE (as of now)")
    ledger = {}
    for inv in invoices:
        ledger[inv["invoice_number"]] = {"settled": Decimal("0.00"), "rows": [], "lenient": Decimal("0.00"), "ignored": []}
    for r in sorted(txs, key=lambda x: (x["_date"] or dt.date.min, x["transaction_id"])):
        inv = inv_by_no.get(r["invoice_number"])
        if not inv or r["_amount"] is None:
            continue
        if now and r["_date"] and r["_date"] > now:
            continue
        L = ledger[inv["invoice_number"]]
        sign = Decimal(1) if r["kind"] in SETTLING_PLUS else Decimal(-1) if r["kind"] in SETTLING_MINUS else Decimal(0)
        matches = r["currency"] == inv["currency"] and BOOK.get(r["direction"]) == inv["direction"]
        if sign != 0:
            L["lenient"] += sign * r["_amount"]
        if matches:
            L["settled"] += sign * r["_amount"]
            L["rows"].append((r, sign))
        else:
            L["ignored"].append(r)

    hdr = f"  {'invoice':<20} {'dir':<8} {'ccy':<3} {'amount':>12} {'settled':>12} {'open':>12} {'issue':<10} {'due':<10} status"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    order = sorted(invoices, key=lambda r: (r["direction"], r["_issue"] or dt.date.min, r["invoice_number"]))
    totals = defaultdict(lambda: Decimal("0.00"))
    status_notes = []
    for inv in order:
        no = inv["invoice_number"]
        L = ledger[no]
        amt = inv["_amount"] or Decimal("0.00")
        open_ = amt - L["settled"]
        status = "?"
        if inv["_amount"] is None:
            status = "n/a (amount unreadable)"
        elif open_ == 0:
            status = "paid"
            # when did it become fully paid?
            run = Decimal("0.00")
            paid_on = None
            for r, sign in L["rows"]:
                run += sign * r["_amount"]
                if run >= amt:
                    paid_on = r["_date"]
                elif run < amt:
                    paid_on = None
            if paid_on and inv["_due"] and paid_on > inv["_due"]:
                status += f" (late: completed {paid_on}, {(paid_on - inv['_due']).days} days after due)"
                status_notes.append(("WARN", f"{no} was paid late: fully settled on {paid_on}, due {inv['due_date']}"))
        elif open_ < 0:
            status = f"OVERPAID by {money(-open_)}"
            status_notes.append(("WARN", f"{no} OVERPAID by {inv['currency']} {money(-open_)}"))
        else:
            part = " partial" if L["settled"] > 0 else ""
            if now and inv["_due"] and inv["_due"] < now:
                n = (now - inv["_due"]).days
                status = f"OVERDUE {n} days{part}"
                status_notes.append(("WARN", f"{no} OVERDUE {n} days at now, open {inv['currency']} {money(open_)}"))
            else:
                status = f"open-not-due{part}"
        totals[(inv["direction"], inv["currency"])] += open_
        print(
            f"  {no:<20} {inv['direction']:<8} {inv['currency']:<3} {money(amt):>12} {money(L['settled']):>12} "
            f"{money(open_):>12} {inv['issue_date']:<10} {inv['due_date']:<10} {status}"
        )
    print()
    for (d, c), v in sorted(totals.items()):
        side = "we owe (AP)" if d == "inbound" else "they owe us (AR)"
        plain(f"total open {d:<8} {c}: {money(v):>12}   {side}")
    print()
    for lvl, msg in status_notes:
        say(lvl, msg)
    print()
    print("  Rows per invoice (+ settles, - adds back, 0 counts nothing):")
    for inv in order:
        no = inv["invoice_number"]
        L = ledger[no]
        if not L["rows"] and not L["ignored"]:
            plain(f"{no}: no transactions")
            continue
        plain(f"{no}:")
        for r, sign in L["rows"]:
            sg = "+" if sign > 0 else "-" if sign < 0 else "0"
            plain(
                f"   {sg} {r['transaction_id']:<22} {r['occurred_at']} {r['direction']:<3} {r['kind']:<17} {r['currency']} {money(r['_amount']):>11}"
                + (f"  ext={r['external_ref']}" if r["external_ref"] else "")
                + (f"  origin={r['origin_tx']}" if r["origin_tx"] else "")
            )
        for r in L["ignored"]:
            plain(
                f"   x {r['transaction_id']:<22} {r['occurred_at']} {r['direction']:<3} {r['kind']:<17} {r['currency']} {money(r['_amount']):>11}  IGNORED (wrong book or currency)"
            )
        if L["lenient"] != L["settled"]:
            warn(
                f"{no}: if direction/currency were ignored, settled would be {money(L['lenient'])} instead of {money(L['settled'])}; check the intent"
            )

    print()
    print("  payment_initiated rows with no follow-up row (origin_tx pointing at them):")
    followed = defaultdict(list)
    for r in txs:
        if r["origin_tx"]:
            followed[r["origin_tx"]].append(r)
    any_pi = False
    for r in txs:
        if r["kind"] != "payment_initiated":
            continue
        any_pi = True
        fol = [f for f in followed.get(r["transaction_id"], []) if not (f["_date"] and r["_date"] and f["_date"] < r["_date"])]
        if not fol:
            age = f", {(now - r['_date']).days} days before now" if now and r["_date"] else ""
            warn(
                f"{r['transaction_id']} announced {r['currency']} {r['amount']} for {r['invoice_number'] or '(no invoice)'} "
                f"on {r['occurred_at']}{age}; nothing landed (it pays nothing)"
            )
        else:
            info(
                f"{r['transaction_id']} ({r['occurred_at']}) followed by "
                + ", ".join(f"{f['transaction_id']} {f['kind']} {f['occurred_at']}" for f in fol)
            )
    if not any_pi:
        plain("(no payment_initiated rows)")

    print()
    print("  Unapplied cash (no invoice_number or no company_id):")
    any_un = False
    for r in txs:
        if not r["invoice_number"] or not r["company_id"]:
            any_un = True
            missing = " and ".join(k for k in ("invoice_number", "company_id") if not r[k])
            warn(
                f"{r['transaction_id']} {r['occurred_at']} {r['direction']} {r['kind']} {r['currency']} {r['amount']}: no {missing}"
                + (f" (ext {r['external_ref']})" if r["external_ref"] else "")
            )
            if r["_amount"] is not None:
                same = [
                    i["invoice_number"]
                    for i in invoices
                    if i["_amount"] == r["_amount"] and i["currency"] == r["currency"] and BOOK.get(r["direction"]) == i["direction"]
                ]
                opens = [
                    i["invoice_number"]
                    for i in invoices
                    if i["_amount"] is not None
                    and i["currency"] == r["currency"]
                    and BOOK.get(r["direction"]) == i["direction"]
                    and (i["_amount"] - ledger[i["invoice_number"]]["settled"]) == r["_amount"]
                ]
                if same:
                    plain(f"   amount equals invoice(s): {', '.join(same)}")
                if opens:
                    plain(f"   amount equals the open balance of: {', '.join(opens)}")
    if not any_un:
        plain("(none)")

    print()
    print("  Rows sharing an external_ref:")
    groups = defaultdict(list)
    for r in txs:
        if r["external_ref"]:
            groups[r["external_ref"]].append(r)
    shared = {k: v for k, v in groups.items() if len(v) > 1}
    if not shared:
        plain("(none)")
    for ref, rs in sorted(shared.items()):
        tot = sum((r["_amount"] or Decimal(0)) for r in rs)
        ccys = {r["currency"] for r in rs}
        dirs = {r["direction"] for r in rs}
        dates = {r["occurred_at"] for r in rs}
        plain(f"{ref}: {len(rs)} rows, total {'/'.join(sorted(ccys))} {money(tot)}")
        for r in rs:
            inv = inv_by_no.get(r["invoice_number"])
            note = ""
            if inv and inv["_amount"] is not None:
                note = "= invoice amount" if inv["_amount"] == r["_amount"] else f"invoice is {money(inv['_amount'])}"
            plain(
                f"   {r['transaction_id']:<22} {r['occurred_at']} {r['direction']:<3} {r['kind']:<17} {r['invoice_number'] or '(none)':<16} {money(r['_amount']):>11} {note}"
            )
        if len(dates) > 1:
            warn(f"external_ref {ref}: rows on different dates {sorted(dates)}; one bank transfer normally books on one date")
        if len(dirs) > 1:
            warn(f"external_ref {ref}: mixed directions {sorted(dirs)}")
        if len(ccys) > 1:
            warn(f"external_ref {ref}: mixed currencies {sorted(ccys)}")
        invs = [inv_by_no[r["invoice_number"]] for r in rs if r["invoice_number"] in inv_by_no]
        inv_sum = sum(i["_amount"] for i in {i["invoice_number"]: i for i in invs}.values() if i["_amount"] is not None)
        if invs and inv_sum == tot:
            info(f"external_ref {ref}: total {money(tot)} equals the sum of the invoices it covers")
        elif invs:
            info(f"external_ref {ref}: total {money(tot)} vs sum of covered invoices {money(inv_sum)} (difference {money(tot - inv_sum)})")
        whole = [i["invoice_number"] for i in invoices if i["_amount"] == tot]
        if whole:
            info(f"external_ref {ref}: total {money(tot)} equals the amount of invoice(s) {', '.join(whole)}")

    # ------------------------------------------------------------------ 5
    section("5. DUPLICATE HINTS (same direction, identical amount)")
    by_amt = defaultdict(list)
    for inv in invoices:
        if inv["_amount"] is not None:
            by_amt[(inv["direction"], inv["currency"], inv["_amount"])].append(inv)
    found = False
    for (d, c, a), rs in sorted(by_amt.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        if len(rs) < 2:
            continue
        found = True
        months = [i["issue_date"][:7] for i in rs]
        same_month = len(set(months)) < len(months)
        lst = ", ".join(f"{i['invoice_number']} ({i['issue_date']})" for i in rs)
        msg = f"{d} {c} {money(a)}: {lst}"
        if same_month:
            warn(msg + "  <- two of these are issued in the same month")
        else:
            info(msg)
    if not found:
        plain("(none)")

    # ------------------------------------------------------------------ 6
    section("6. IBANs")
    occurrences = defaultdict(list)  # iban -> [(source, context)]
    raw_forms = {}
    for inv in invoices:
        if inv["iban"]:
            occurrences[inv["iban"].replace(" ", "")].append(("invoices", f"invoices.csv:{inv['_line']} {inv['invoice_number']}"))
    if os.path.isdir(docs_dir):
        for fn in sorted(os.listdir(docs_dir)):
            if not fn.endswith(".md"):
                continue
            text, _, problem = read_text(os.path.join(docs_dir, fn))
            if problem:
                continue
            for comp, raw, off in find_ibans(text):
                ln = text.count("\n", 0, off) + 1
                occurrences[comp].append(("contract", f"documents/{fn}:{ln}"))
                raw_forms[comp] = raw
    for r in mail:
        for col in ("subject", "body"):
            for comp, raw, off in find_ibans(r[col]):
                occurrences[comp].append(("mail", f"mail.csv seq {r['seq']} ({r['sent_at']}, {r['direction']}, from {r['sender']}) {col}"))
                raw_forms[comp] = raw
    readme_ibans = set()
    readme_path = os.path.join(folder, "README.md")
    if os.path.isfile(readme_path):
        rt = open(readme_path, encoding="utf-8", errors="replace").read()
        for comp, raw, off in find_ibans(rt):
            readme_ibans.add(comp)
    if not occurrences:
        err("no IBAN found in invoices.iban, documents/*.md or mail.csv (the brief requires at least one)")
    for iban in sorted(occurrences):
        cc = iban[:2]
        L = IBAN_LENGTHS.get(cc)
        problems = []
        if L is None:
            problems.append(f"unknown IBAN country {cc}")
        elif len(iban) != L:
            problems.append(f"length {len(iban)}, {cc} IBANs are {L}")
        if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", iban):
            problems.append("bad characters")
        elif not iban_mod97_ok(iban):
            problems.append("mod-97 check digits WRONG")
        srcs = sorted({s for s, _ in occurrences[iban]})
        head = f"{iban}  [{', '.join(srcs)}]"
        if problems:
            err(f"{head}: " + "; ".join(problems))
        else:
            info(f"{head}: valid ({cc}, {len(iban)} chars, mod-97 OK)")
        for _, wh in occurrences[iban]:
            plain(f"   in {wh}")
    print()
    inv_ibans = defaultdict(list)
    for inv in invoices:
        if inv["iban"]:
            inv_ibans[inv["iban"].replace(" ", "")].append(inv["invoice_number"])
    for iban, nos in sorted(inv_ibans.items()):
        srcs = {s for s, _ in occurrences[iban]}
        if not ({"contract", "mail"} & srcs):
            warn(f"invoice IBAN {iban} (on {', '.join(nos)}) appears in no contract and no mail")
        else:
            info(f"invoice IBAN {iban} (on {len(nos)} invoice(s)) also appears in: {', '.join(sorted(srcs - {'invoices'}))}")
    if len(occurrences) > 1:
        warn(f"{len(occurrences)} different IBANs in the data; check each mismatch is planted and documented")
    by_dir = defaultdict(set)
    for inv in invoices:
        if inv["iban"]:
            by_dir[inv["direction"]].add(inv["iban"].replace(" ", ""))
    for d, s in by_dir.items():
        if len(s) > 1:
            warn(f"{d} invoices ask to be paid into {len(s)} different IBANs: {sorted(s)}")
    if by_dir.get("outbound"):
        info("outbound invoices carry an IBAN: that should be Meridian's own bank account")
    inv_no_iban = [i["invoice_number"] for i in invoices if not i["iban"]]
    if inv_no_iban:
        info(f"invoices with no iban: {', '.join(inv_no_iban)}")
    for ib in sorted(readme_ibans - set(occurrences)):
        warn(f"README.md mentions IBAN {ib}, which is in no invoice, contract or mail")

    # ------------------------------------------------------------------ 7
    section("7. WORDING (banned words, 'account', role words in CSV values)")
    text_files = []
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for fn in sorted(files):
            text_files.append(os.path.join(root, fn))
    banned = ["vendor", "creditor", "payee", "client"]
    account_hits = []
    for path in text_files:
        rel = os.path.relpath(path, folder)
        for b in banned:
            if b in rel.lower():
                err(f"file name {rel} contains '{b}'")
        text, _, problem = read_text(path)
        if problem or text is None:
            continue
        low = text.lower()
        for b in banned:
            for m in re.finditer(re.escape(b), low):
                ln = text.count("\n", 0, m.start()) + 1
                ctx = text[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
                err(f"{rel}:{ln}: banned word '{b}': ...{ctx}...")
        for m in re.finditer("account", low):
            ln = text.count("\n", 0, m.start()) + 1
            ctx = text[max(0, m.start() - 40) : m.end() + 40].replace("\n", " ")
            account_hits.append((rel, ln, ctx))
    bankish = re.compile(
        r"bank\s+account|account\s+holder|account\s+(number|details)|iban|bank\s+details|"
        r"(our|your|their|the|its|new|old|same|different|receiving|beneficiary)\s+(bank\s+)?account\b(?!\s*(manager|executive|team|owner|settings|login|page|user|name))",
        re.I,
    )
    if account_hits:
        print(f"  'account' occurrences ({len(account_hits)}); judge each is a BANK account:")
        for rel, ln, ctx in account_hits:
            if bankish.search(ctx):
                say("INFO", f"{rel}:{ln}: ...{ctx}...")
            else:
                err(f"{rel}:{ln}: 'account' not used for a bank account (brief): ...{ctx}...")
    else:
        plain("no 'account' anywhere")

    role_words = ["supplier", "customer", "buyer", "seller"]
    csv_tables = [
        ("company.csv", company or []),
        ("invoices.csv", invoices),
        ("transactions.csv", txs),
        ("contracts.csv", contracts),
        ("mail.csv", mail),
    ]
    role_found = False
    for name, rows in csv_tables:
        for h in HEADERS[name]:
            for rw in role_words:
                if rw in h.lower():
                    err(f"{name}: column {h} contains role word '{rw}'")
                    role_found = True
        for r in rows:
            for k in HEADERS[name]:
                if name == "mail.csv" and k in ("subject", "body"):
                    continue  # prose
                v = r.get(k, "")
                vl = v.strip().lower()
                for rw in role_words:
                    if vl == rw or vl == rw + "s":
                        err(f"{name}:{r['_line']} {k} = {v!r}: role word stored as a value")
                        role_found = True
                    elif re.search(r"(?<![a-z])" + rw, vl):
                        warn(f"{name}:{r['_line']} {k} = {v!r} contains '{rw}' (role must show only through direction)")
                        role_found = True
    if not role_found:
        info("no supplier/customer/buyer/seller in any CSV column or value (mail subject/body treated as prose)")

    # ------------------------------------------------------------------ 8
    section("8. VAT SANITY (tax_amount / (amount - tax_amount))")
    for inv in order:
        no = inv["invoice_number"]
        a, t = inv["_amount"], inv["_tax"]
        if a is None:
            continue
        if t is None:
            info(f"{no}: no tax_amount")
            continue
        net = a - t
        if net <= 0:
            err(f"{no}: net amount {money(net)} is not positive")
            continue
        rate = t / net * 100
        rate_s = f"{rate.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)}%"
        if t == 0:
            info(f"{no}: amount {money(a)}, tax 0.00 -> 0% (exempt / reverse charge / export; check the contract says so)")
            continue
        match = None
        for r_ in EU_VAT_RATES:
            if abs(net * r_ / 100 - t) <= Decimal("0.01"):
                match = r_
                break
        line = f"{no}: amount {money(a)} = net {money(net)} + tax {money(t)} -> {rate_s}"
        if match is not None:
            exact = (net * match / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == t
            info(line + f"  (= {match}%{'' if exact else ', off by a rounding cent'})")
        else:
            warn(line + "  not a common EU VAT rate")

    # ------------------------------------------------------------------ 9
    section("9. MAIL TIME ZONES (Europe/Madrid, Europe/Berlin)")
    if not mail:
        plain("(no mail)")
    for r in mail:
        if r["_utc"] is None:
            continue
        off = r["_offset"]
        exp_h = None
        if ZoneInfo is not None:
            try:
                z = ZoneInfo("Europe/Madrid")
                aware = r["_utc"].replace(tzinfo=dt.timezone.utc).astimezone(z)
                exp_h = int(aware.utcoffset().total_seconds() // 3600)
                zb = ZoneInfo("Europe/Berlin")
                exp_b = int(r["_utc"].replace(tzinfo=dt.timezone.utc).astimezone(zb).utcoffset().total_seconds() // 3600)
                if exp_b != exp_h:
                    warn(f"seq {r['seq']}: Madrid and Berlin offsets differ at this instant (unexpected)")
            except Exception:
                exp_h = None
        if exp_h is None:
            exp_h = eu_cet_offset_for_utc(r["_utc"])
        manual = eu_cet_offset_for_utc(r["_utc"])
        if manual != exp_h:
            warn(f"seq {r['seq']}: zoneinfo says +0{exp_h}:00, manual EU rule says +0{manual}:00")
        exp_s = f"+0{exp_h}:00"
        name = "CEST" if exp_h == 2 else "CET"
        if off in ("+01:00", "+02:00"):
            if off != exp_s:
                warn(f"seq {r['seq']} {r['sent_at']} ({r['sender']}): offset {off}, but Madrid/Berlin on that date is {exp_s} ({name})")
            else:
                info(f"seq {r['seq']} {r['sent_at']}: {off} correct for Madrid/Berlin ({name})")
        else:
            info(f"seq {r['seq']} {r['sent_at']} ({r['sender']}): offset {off} is not CET/CEST; check the sender's location fits")

    # ------------------------------------------------------------------ 10
    section("10. expected.json")
    ej = os.path.join(folder, "expected.json")
    if not os.path.isfile(ej):
        err("expected.json missing")
    else:
        text, bom, problem = read_text(ej)
        data = None
        if problem:
            err(f"expected.json: {problem}")
        else:
            if bom:
                warn("expected.json starts with a BOM")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as e:
                err(f"expected.json is not valid JSON: {e}")
        if data is not None:
            if not isinstance(data, dict) or not isinstance(data.get("patterns"), list):
                err("expected.json must be an object with a 'patterns' list")
            else:
                if set(data) != {"patterns"}:
                    warn(f"expected.json has extra top-level keys: {sorted(set(data) - {'patterns'})}")
                pats = data["patterns"]
                ids = set()
                n_present = n_absent = 0
                cats = set()
                pnums, snums = [], []
                for i, p in enumerate(pats):
                    if not isinstance(p, dict):
                        err(f"pattern #{i}: not an object")
                        continue
                    pid = p.get("id", "")
                    tag = f"pattern {pid or '#' + str(i)}"
                    extra = set(p) - {"id", "polarity", "category", "description", "task"}
                    if extra:
                        warn(f"{tag}: unexpected keys {sorted(extra)}")
                    m = re.match(r"^([ps])(\d+)_[a-z0-9_]+$", pid or "")
                    if not m:
                        err(f"{tag}: id must look like p<N>_<words> or s<N>_<words> (lowercase)")
                    if pid in ids:
                        err(f"{tag}: duplicate id")
                    ids.add(pid)
                    pol = p.get("polarity")
                    if pol not in ("present", "absent"):
                        err(f"{tag}: polarity {pol!r} must be present or absent")
                    if m:
                        if m.group(1) == "p" and pol != "present":
                            err(f"{tag}: p-id must have polarity present")
                        if m.group(1) == "s" and pol != "absent":
                            err(f"{tag}: s-id must have polarity absent")
                        (pnums if m.group(1) == "p" else snums).append(int(m.group(2)))
                    if pol == "present":
                        n_present += 1
                    elif pol == "absent":
                        n_absent += 1
                    cat = p.get("category")
                    if cat not in CATEGORIES:
                        err(f"{tag}: category {cat!r} not in {sorted(CATEGORIES)}")
                    else:
                        cats.add(cat)
                    if pol == "present" and cat == "hallucination":
                        warn(f"{tag}: a present problem with category hallucination (that category is for decoys)")
                    if not isinstance(p.get("description"), str) or not p["description"].strip():
                        err(f"{tag}: description missing or empty")
                    elif len(p["description"]) < 120:
                        warn(
                            f"{tag}: description is short ({len(p['description'])} chars); judges need invoice, clause, amounts, arithmetic"
                        )
                    if "task" in p:
                        if pol != "present":
                            err(f"{tag}: task is only allowed on present patterns")
                        if p["task"] != ["human"]:
                            err(f'{tag}: task must be exactly ["human"], is {p["task"]!r}')
                for label, nums in (("p", pnums), ("s", snums)):
                    if nums and sorted(nums) != list(range(1, len(nums) + 1)):
                        warn(f"{label}-numbers are {sorted(nums)}; expected 1..{len(nums)} with no gaps")
                # The worked example SAMPLE is deliberately tiny (1 problem, 1 decoy); the minimums
                # apply to a submission, so for SAMPLE they are only a warning.
                size_fail = err if cid != "SAMPLE" else warn
                if n_present < 3:
                    size_fail(f"only {n_present} present problems (a submission needs at least 3)")
                if n_absent < 2:
                    size_fail(f"only {n_absent} absent decoys (a submission needs at least 2)")
                if len(cats) < 2:
                    size_fail(f"only {len(cats)} categories used (need at least 2): {sorted(cats)}")
                info(f"{n_present} present, {n_absent} absent, categories: {', '.join(sorted(cats))}")
                if os.path.isfile(readme_path):
                    rt = open(readme_path, encoding="utf-8", errors="replace").read()
                    for pid in sorted(ids):
                        short = pid.split("_")[0]
                        if pid not in rt and not re.search(r"(?<![A-Za-z0-9])" + re.escape(short) + r"(?![0-9])", rt):
                            warn(f"README.md does not mention {short} ({pid})")

    # ------------------------------------------------------------------ 11
    section("11. WEEKEND BOOKINGS (occurred_at on Saturday/Sunday)")
    wk = False
    for r in txs:
        if r["_date"] and r["_date"].weekday() >= 5:
            wk = True
            info(
                f"{r['transaction_id']} {r['occurred_at']} is a {r['_date'].strftime('%A')} ({r['kind']}, {r['method'] or 'no method'}); bank transfers rarely book on weekends"
            )
    if not wk:
        plain("(none)")

    # ------------------------------------------------------------------ summary
    section("SUMMARY")
    print(f"  now = {now.isoformat() if now else '?'}")
    print(f"  ERROR {COUNTS['ERROR']}   WARN {COUNTS['WARN']}   INFO {COUNTS['INFO']}")
    print("  RESULT: " + ("FAIL (fix every ERROR)" if COUNTS["ERROR"] else "PASS (no ERROR; read every WARN)"))
    return 1 if COUNTS["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
