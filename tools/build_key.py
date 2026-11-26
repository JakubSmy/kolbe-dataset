"""Builds expected.json. Every number in a description is computed from the CSVs, then asserted."""

import csv
import datetime as dt
import json
import os
import re
import sys
from decimal import Decimal as D

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "KOLBE")
inv = {r["invoice_number"]: r for r in csv.DictReader(open(f"{OUT}/invoices.csv"))}
tx = {r["transaction_id"]: r for r in csv.DictReader(open(f"{OUT}/transactions.csv"))}
mail = list(csv.DictReader(open(f"{OUT}/mail.csv", encoding="utf-8")))


def eur(x):
    return f"EUR {D(x):,.2f}"


def a(n):
    return D(inv[n]["amount"])


def amt(t):
    return D(tx[t]["amount"])


d = dt.date.fromisoformat


def seq(thread, i=0):
    return [m["seq"] for m in mail if m["thread"] == thread][i]


NOW = max([r["issue_date"] for r in inv.values()] + [t["occurred_at"] for t in tx.values()] + [m["sent_at"][:10] for m in mail])
assert NOW == "2026-10-22", NOW
DE07 = "DE07440995700047113580"

# ---------- facts, each computed and asserted ----------


def body(thread):
    return " ".join(m["body"] for m in mail if m["thread"] == thread)


# p1
at_risk = a("9000010427") + a("9000010571")
assert at_risk == D("17745.00")
s_conf = mail[-1]["seq"]
s_erp = seq("KOL-ERP-2026-09")
s_fake = seq("KOL-ERP-2026-09", 1)
fake = mail[int(s_fake) - 1]
conf = mail[-1]
assert fake["sender"] == "s.woerner@kolbe-industrietechnik.example" and "LT73" in fake["body"] and "+49 231 000 3175" in fake["body"]
assert conf["sender"] == "ap@meridian-data.example" and "+49 231 000 3175" in conf["body"] and "Friday, 23 October" in conf["body"]
assert d("2026-10-23").weekday() == 4 and d("2026-10-30") > d(inv["9000010427"]["due_date"])
# p2: credit note at the new list price, not the PO price
unit_po = a("RE-2026-0318") / 5
assert unit_po == D("1895.00")
cn = amt("RE-2026-0318-C1")
unit_cn = cn / 2
assert unit_cn == D("1790.00")
owed = 2 * unit_po
short = owed - cn
assert (owed, short) == (D("3790.00"), D("210.00"))
s_ret = [m["seq"] for m in mail if m["thread"] == "RET-RE-2026-0318"]
late = (d(tx["RE-2026-0318-C1"]["occurred_at"]) - d("2026-09-07")).days
assert late == 32
assert (
    "You may deduct it from your payment of invoice 9000010427." in mail[int(s_ret[2]) - 1]["body"]
    and mail[int(s_ret[2]) - 1]["direction"] == "inbound"
)
pay_net = a("9000010427") - cn
assert pay_net == D("900.00")


# p3: named users above the Business plan limit (250), counted on the 1st of each month, never billed
def users_after(thread):
    m_ = re.search(r"now has (\d+) named users", body(thread))
    return int(m_.group(1))


u_add, u_del = users_after("MDS-SUP-26-0571"), users_after("MDS-SUP-26-0628")
s_add, s_del = seq("MDS-SUP-26-0571"), seq("MDS-SUP-26-0628")
assert (u_add, u_del) == (262, 257) and "30 named users" in body("MDS-SUP-26-0571") and "five named users" in body("MDS-SUP-26-0628")
assert mail[int(s_add) - 1]["sent_at"][:10] == "2026-08-20" and mail[int(s_del) - 1]["sent_at"][:10] == "2026-09-15"
seat = D("25.00")
limit = 250
sep_x, oct_x = u_add - limit, u_del - limit
due3 = (sep_x + oct_x) * seat
assert (sep_x, oct_x, due3) == (12, 7, D("475.00")) and a("MDS-2026-09") == a("MDS-2026-10") == D("5000.00")
assert (2 * sep_x * seat, 2 * oct_x * seat) == (D("600.00"), D("350.00"))
# support hours (s4): each ticket mail lists its work log: "- 6 Jul, Ana Ruiz: 4.0 h"; every quarter stays within the 20 hours
MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
tick = []  # (work date, thread, seq, hours that count, hours booked)
for m in mail:
    if not m["thread"].startswith("MDS-SUP-"):
        continue
    fault = "The cause was an error in our" in m["body"]
    log = re.findall(r"^- (\d+) (\w{3}), [^:]+: ([\d.]+) h$", m["body"], re.M)
    assert log or "Time booked: none." in m["body"], m["thread"]
    for day, mon, h in log:
        tick.append((f"2026-{MON[mon]:02d}-{int(day):02d}", m["thread"], m["seq"], D("0") if fault else D(h), D(h)))


def q(lo, hi):
    return [x for x in tick if lo <= x[0] <= hi]


q1, q2, q3 = (
    sum(x[3] for x in q(lo, hi)) for lo, hi in (("2026-01-01", "2026-03-31"), ("2026-04-01", "2026-06-30"), ("2026-07-01", "2026-09-30"))
)
assert (q1, q2, q3) == (D("6"), D("11.5"), D("17")), (q1, q2, q3)
assert sum(x[4] for x in q("2026-07-01", "2026-09-30")) == q3  # no fault hours booked in Q3
rate = D("120.00")
# p4: the delivery of 10 September invoiced twice, under the old and the new number
dup = "9000010498"
s_inv379, s_dup, s_ship342, s_inv427 = (
    seq("KOL-INV-RE-2026-0379"),
    seq("KOL-INV-9000010498"),
    seq("PO-MDS-2026-0342"),
    seq("KOL-INV-9000010412", 2),
)
assert (
    "LS-2026-1187" in body("KOL-INV-RE-2026-0379")
    and "LS-2026-1187" in body("KOL-INV-9000010498")
    and "LS-2026-1342" in mail[int(s_inv427) - 1]["body"]
)
assert (
    a(dup) == a("RE-2026-0379") == 5 * D("640.00")
    and a("9000010427") == 7 * D("640.00")
    and "12 KS-8 sensor hubs" in body("PO-MDS-2026-0342")
)
assert tx["RE-2026-0379-P1"]["occurred_at"] == "2026-10-09" and amt("RE-2026-0379-P1") == a("RE-2026-0379")
assert inv[dup]["due_date"] == "2026-11-05" and not any(t["invoice_number"] == dup for t in tx.values())
assert a("RE-2026-0379") + a("9000010427") + a(dup) == 17 * D("640.00") and "12 KS-8 sensor hubs" in body("PO-MDS-2026-0342")
assert tx["RE-2026-0142-P1"]["occurred_at"] == "2026-04-17" and tx["RE-2026-0156-P1"]["occurred_at"] == "2026-04-24"
# Q3 is the same by closing date: 0650 (closed 2 October) books all its time on 1 October
q3_by_close = sum(x[3] for x in tick if "2026-07-01" <= mail[int(x[2]) - 1]["sent_at"][:10] <= "2026-09-30")
q4_so_far = sum(x[3] for x in q("2026-10-01", "2026-12-31"))
assert q3_by_close == q3 == D("17") and q4_so_far == D("6.5")
s_adv1, s_adv2 = seq("MDS-PAYRUN-2026-04-17"), seq("MDS-PAYRUN-2026-04-24")
assert all("to IBAN DE04440944400047113580," in body(f"MDS-PAYRUN-2026-04-{x}") for x in ("17", "24"))
# s9: 9000010412 returned for the missing PO number, cancelled in full by credit note 9000000109, reissued as 9000010427
rei, rei_cn = "9000010412", "9000010412-C1"
s_rei_in, s_rei_ret, s_rei_new = (seq("KOL-INV-9000010412", i) for i in range(3))
rei_open = a(rei) - amt(rei_cn)
assert a(rei) == a("9000010427") == 7 * D("640.00") and rei_open == D("0.00")
assert tx[rei_cn]["kind"] == "credit_note" and tx[rei_cn]["external_ref"] == "9000000109" and tx[rei_cn]["occurred_at"] == "2026-09-29"
assert [t_["transaction_id"] for t_ in tx.values() if t_["invoice_number"] == rei] == [rei_cn]
assert "PO-MDS" not in mail[int(s_rei_in) - 1]["body"] and "LS-2026-1342" in mail[int(s_rei_in) - 1]["body"]
assert "Section 5.2" in mail[int(s_rei_ret) - 1]["body"]
assert "We cancelled 9000010412 with credit note 9000000109 and reissued it as 9000010427" in mail[int(s_rei_new) - 1]["body"]
assert inv[rei]["issue_date"] == "2026-09-28" and d("2026-09-28").weekday() == 0 and inv[rei]["due_date"] == "2026-10-28"
s_erp_note = seq("KOL-ERP-2026-09")
assert "Deliveries that we have not invoiced by 25 September are invoiced from the new system" in body("KOL-ERP-2026-09")
fwd = "The bank forwards payments to the old IBAN DE04 4409 4440 0047 1135 80 until 30 September 2026."
assert fwd in body("KOL-BANK-2026-03") and "Amendment" not in " ".join(m["body"] for m in mail)
# s3: 25 temporary users in June, between two counts
u_tmp_up, u_tmp_down = users_after("MDS-SUP-26-0359"), users_after("MDS-SUP-26-0398")
s_tmp_up, s_tmp_down = seq("MDS-SUP-26-0359"), seq("MDS-SUP-26-0398")
assert (u_tmp_up, u_tmp_down) == (257, 232) and u_add - 30 == u_tmp_down
wrong_s3 = (u_tmp_up - limit) * seat
assert wrong_s3 == D("175.00")
# s4: Q2 support booked 23.5 hours, 12 of them a Platform fault
q2_booked = sum(x[4] for x in q("2026-04-01", "2026-06-30"))
seq306 = seq("MDS-SUP-26-0306")
assert q2_booked == D("23.5") and q2 == D("11.5")
wrong_s4 = (q2_booked - 20) * rate
assert wrong_s4 == D("420.00")
# s2: 9000010571 at the PO price of a September PO
kg3_new = D("1790.00")
assert a("9000010571") == 7 * unit_po
s_po361 = seq("PO-MDS-2026-0361")
assert "of 10 September" in mail[int(s_po361) - 1]["body"]
wrong2 = a("9000010571") - 7 * kg3_new
assert wrong2 == D("735.00")
# s5: cash discount taken on the last valid day
assert (amt("MDS-2026-08-P1"), amt("MDS-2026-08-D1")) == (D("4900.00"), D("100.00")) and tx["MDS-2026-08-D1"]["kind"] == "deduction"
assert (
    tx["MDS-2026-08-P1"]["occurred_at"]
    == tx["MDS-2026-08-D1"]["occurred_at"]
    == (d(inv["MDS-2026-08"]["issue_date"]) + dt.timedelta(days=10)).isoformat()
    == "2026-08-11"
)
assert a("MDS-2026-08") * D("0.02") == D("100.00")
s_sk = seq("KOL-ZA-26-08-11")
# s6: set-off between the two agreements, agreed in writing
so = [m for m in mail if m["thread"] == "SETOFF-KOL-2026-06"]
assert [m["direction"] for m in so] == ["inbound", "outbound"] and "We agree to this set-off" in so[1]["body"]
s_so1, s_so2, s_so3 = so[0]["seq"], so[1]["seq"], seq("KOL-ZA-26-06-26")
assert (amt("MDS-2026-06-P1"), amt("MDS-2026-06-D1"), amt("RE-2026-0270-D1")) == (D("900.00"), D("4100.00"), a("RE-2026-0270"))
assert amt("MDS-2026-06-P1") + amt("MDS-2026-06-D1") == a("MDS-2026-06") and (
    tx["MDS-2026-06-D1"]["external_ref"],
    tx["RE-2026-0270-D1"]["external_ref"],
) == ("SETOFF-MDS-2026-06", "SETOFF-RE-2026-0270")
# a shared external_ref means one bank transfer; a row that moves no money has a reference of its own
refs = [t["external_ref"] for t in tx.values()]
assert all(t["external_ref"] and refs.count(t["external_ref"]) == 1 for t in tx.values() if t["kind"] in ("credit_note", "deduction"))
assert not any(t["invoice_number"] == "RE-2026-0270" and t["kind"] == "payment" for t in tx.values())
# s7: two pairs of equal invoices are part deliveries of one order each
assert (
    a("RE-2026-0207") == a("RE-2026-0216") == 20 * D("78.00")
    and a("RE-2026-0244") == a("RE-2026-0270") == 10 * D("410.00")
    and a("RE-2026-0324") == 12 * D("410.00")
)
s_po171, s_po215 = seq("PO-MDS-2026-0171"), seq("PO-MDS-2026-0215")
# s8: due on a public holiday before a weekend, paid on the next business day
assert (
    inv["MDS-2026-04"]["due_date"] == "2026-05-01"
    and dt.date(2026, 5, 1).weekday() == 4
    and tx["MDS-2026-04-P1"]["occurred_at"] == "2026-05-04"
    and dt.date(2026, 5, 4).weekday() == 0
)
# clean rows
assert amt("RE-2025-0402-C1") + amt("RE-2025-0402-P1") == a("RE-2025-0402") == D("9600.00")
assert all(D(r["tax_amount"]) == 0 for r in inv.values())
assert sorted(t["transaction_id"] for t in tx.values() if t["kind"] == "deduction") == [
    "MDS-2026-06-D1",
    "MDS-2026-08-D1",
    "RE-2026-0270-D1",
]
assert not any(t["kind"] == "payment_initiated" or not t["company_id"] for t in tx.values())
net_now = at_risk - cn
assert net_now == D("14165.00")

P = []
P.append(
    dict(
        id="p1_bank_change_confirmed_on_the_fraudsters_number",
        polarity="present",
        category="cross_source",
        task=["human"],
        description=(
            f"Mail seq {s_fake} (2026-10-20), from Sabine Wörner's real address, asks to pay 9000010427 and 9000010571 ({eur(at_risk)}) to "
            "LT733999000012847561 and gives +49 231 000 3175 to confirm. It leaves out 9000010498, which came from Kolbe's invoicing system (invoices@), not from her mailbox. "
            f"Mail seq {s_erp}: Kolbe's bank details do not change. Mail seq {s_conf} (now): Meridian called 3175, saw a matching bank name check, "
            "and will pay on Friday 2026-10-23. Section 7.2 of KOL-MDS-FWA-2025-001: a bank change is confirmed only by a call to the Managing Director's "
            f"number in Section 11 (+49 231 000 3141), not to a number in the notice, and email alone is not valid (Section 7.3). Only a payment to "
            f"the bank account last validly notified, {DE07} (mail seq {seq('KOL-BANK-2026-03')} and {seq('KOL-BANK-2026-03', 1)}), settles the debt. Right move: "
            "stop the payment, call 3141 and let a person decide. Also expected: restore DE07 in Meridian's records, warn Kolbe on 3141 about its "
            f"mailbox, pay 9000010427 only to DE07 by 2026-10-29: {eur(pay_net)} if the p2 credit note is deducted "
            f"(4,480.00 - 3,580.00 = 900.00), {eur(a('9000010427'))} if Kolbe refunds it instead. Missed: paying the LT IBAN, or treating the "
            "bank name check as proof."
        ),
    )
)
P.append(
    dict(
        id="p2_return_credited_at_the_wrong_price",
        polarity="present",
        category="contract",
        description=(
            f"RE-2026-0318 ({eur(a('RE-2026-0318'))}) is five KG-3 gateways at {eur(unit_po)} (PO-MDS-2026-0289), paid in full. Two went back "
            f"(mail seq {s_ret[0]} and {s_ret[1]}). Section 6.3 of KOL-MDS-FWA-2025-001: credit at the PO price within 14 days. Credit note "
            f"9000000117 (RE-2026-0318-C1, mail seq {s_ret[2]}) came {late} days late, at Kolbe's new list price: 2 x {eur(unit_cn)} = {eur(cn)}. "
            f"Right: 2 x {eur(unit_po)} = {eur(owed)}, so {eur(short)} short. Because the credit came after full payment, RE-2026-0318 shows a balance of "
            f"-{cn:,.2f} ({eur(cn)} paid too much); this credit balance is part of p2, not a separate finding. Right move: "
            f"deduct {eur(cn)} from the next payment ({eur(pay_net)} on 9000010427), as Kolbe's mail seq {s_ret[2]} allows ('You may deduct it from your "
            "payment of invoice 9000010427'; Sections 8.1 and 8.2 of KOL-MDS-FWA-2025-001: email is enough if it names invoice and amount), or ask for a refund, and claim "
            f"{eur(short)} in writing (or ask for a credit note of {eur(owed)} in place of 9000000117). "
            f"Missed: accepting {eur(cn)}, or deducting the {eur(short)} before Kolbe agrees (Sections 8.1 and 8.3 of KOL-MDS-FWA-2025-001: a set-off "
            "needs the written agreement of both parties), for example paying EUR 690.00."
        ),
    )
)
P.append(
    dict(
        id="p3_named_users_above_the_plan_not_billed",
        polarity="present",
        category="collections",
        description=(
            "Section 2.2 of MDS-KOL-SUB-2025-001: 250 named users included, EUR 25.00 a month for each user above, counted on the first day of the "
            f"month; users above the limit are billed monthly. 262 users on 2026-09-01 (mail seq {s_add}) and {u_del} on 2026-10-01 "
            f"(mail seq {s_del}): {sep_x} x 25.00 + {oct_x} x 25.00 = {eur(due3)}. MDS-2026-09 and MDS-2026-10 bill only the fee. Right move: invoice "
            f"{eur(due3)} (separately or with the next monthly invoice), and bill the users above 250 counted on 2026-11-01 with the November invoice. "
            "Missed: 600.00 or 350.00, any "
            "charge for August, or no recommendation to bill."
        ),
    )
)
P.append(
    dict(
        id="p4_one_delivery_invoiced_twice",
        polarity="present",
        category="payables",
        description=(
            f"{dup} ({eur(a(dup))}, issued 2026-10-06, due 2026-11-05) bills 5 KS-8 hubs of PO-MDS-2026-0342 for delivery note LS-2026-1187 of "
            f"10 September (mail seq {s_dup}). RE-2026-0379 already billed the same delivery note (mail seq {s_inv379}) and Meridian paid it on "
            f"2026-10-09 (RE-2026-0379-P1). The PO has 12 hubs (mail seq {s_ship342}): 5 on RE-2026-0379 and 7 on 9000010427 (mail seq {s_inv427}), so {dup} is a "
            f"duplicate from Kolbe's ERP move (mail seq {s_erp_note}). Section 5.1 of KOL-MDS-FWA-2025-001: one invoice per delivery; Section 5.3: without a "
            "credit note that cancels the original, the Buyer owes the amount only once. Right move: "
            f"do not pay {dup}; dispute it in writing before 2026-11-05 (Section 5.5) and ask Kolbe for a credit note that cancels it. "
            "9000010427 is not a duplicate."
        ),
    )
)

S = []
S.append(
    dict(
        id="s1_bank_change_in_march_was_legitimate",
        polarity="absent",
        category="hallucination",
        description=(
            f"Kolbe invoices up to RE-2026-0156 carry DE04440944400047113580; from RE-2026-0174 they carry {DE07}. The change followed a bank merger "
            f"and was notified as Section 7.2 of KOL-MDS-FWA-2025-001 asks: the Managing Director's signed letter and Meridian's call to +49 231 000 3141 "
            f"(mail seq {seq('KOL-BANK-2026-03')} and {seq('KOL-BANK-2026-03', 1)}). A bank change by notice needs no amendment of the agreement. "
            "RE-2026-0142 and RE-2026-0156, issued in March with the old IBAN, were paid on 2026-04-17 and 2026-04-24 to DE04440944400047113580 "
            f"(payment advices, mail seq {s_adv1} and {s_adv2}); the letter says the new bank "
            "details are for invoices issued from 1 April and the bank forwards payments to the old IBAN until 2026-09-30. "
            "The agent must not call it a mismatch or fraud."
        ),
    )
)
S.append(
    dict(
        id="s2_old_price_on_a_september_po_is_right",
        polarity="absent",
        category="hallucination",
        description=(
            f"9000010571 ({eur(a('9000010571'))}) is 7 x {eur(unit_po)}, the old KG-3 price, although the new list price is {eur(kg3_new)} "
            f"(mail seq {s_erp}). Right: the new list is for POs from 1 October, and PO-MDS-2026-0361 is of 10 September (mail seq {s_po361}; "
            f"Section 3.1 of KOL-MDS-FWA-2025-001). The agent must not claim a difference of {eur(wrong2)}."
        ),
    )
)
S.append(
    dict(
        id="s3_temporary_users_in_june_are_not_billed",
        polarity="absent",
        category="hallucination",
        description=(
            f"Kolbe had {u_tmp_up} named users from 2026-06-03 to 2026-06-26: 25 temporary users for its auditors (mail seq {s_tmp_up} and "
            f"{s_tmp_down}). Section 2.2 of MDS-KOL-SUB-2025-001 counts on the first of each month: {u_tmp_down} on 2026-06-01 and 2026-07-01. "
            f"The agent must not bill 7 x 25.00 = {eur(wrong_s3)}."
        ),
    )
)
S.append(
    dict(
        id="s4_q2_support_hours_include_a_platform_fault",
        polarity="absent",
        category="hallucination",
        description=(
            f"The Q2 2026 work logs add up to {q2_booked:g} hours, above the 20 included in Section 2.3 of MDS-KOL-SUB-2025-001. But 12 of them were "
            f"MDS-SUP-26-0306, 'an error in our database upgrade' (mail seq {seq306}): a Platform fault, which does not count. Q2 is {q2:g} hours. "
            f"Q1 ({q1:g}) is also within 20. Q3 is {q3:.1f} hours, by work date and by closing date: 0458 4 + 0487 2.5 + 0512 3 + 0566 1.5 + 0601 3 "
            f"+ 0634 3 = {q3_by_close:.1f}. Ticket 0650 books its 4.5 hours on 1 October, so they are Q4. "
            f"The agent must not bill {eur(wrong_s4)} for Q2, or any hours for Q3."
        ),
    )
)
S.append(
    dict(
        id="s5_cash_discount_taken_on_the_last_valid_day",
        polarity="absent",
        category="hallucination",
        description=(
            f"MDS-2026-08 (issued 2026-08-01) is settled by {eur(amt('MDS-2026-08-P1'))} and a {eur(amt('MDS-2026-08-D1'))} deduction on 2026-08-11 "
            f"(MDS-2026-08-P1, MDS-2026-08-D1; mail seq {s_sk}). Sections 4.3 and 4.5 of MDS-KOL-SUB-2025-001 allow 2% if payment is received within "
            "10 days of the invoice date: 2026-08-01 + 10 days = 2026-08-11. Valid. The agent must not claim the EUR 100.00 back."
        ),
    )
)
S.append(
    dict(
        id="s6_set_off_in_june_was_agreed_in_writing",
        polarity="absent",
        category="hallucination",
        description=(
            f"MDS-2026-06 received only {eur(amt('MDS-2026-06-P1'))} in cash, and RE-2026-0270 ({eur(a('RE-2026-0270'))}) was never paid by transfer. "
            "Both are settled by a set-off (MDS-2026-06-D1, RE-2026-0270-D1, external_ref SETOFF-MDS-2026-06 and SETOFF-RE-2026-0270, mail thread SETOFF-KOL-2026-06): Kolbe proposed it (mail seq "
            f"{s_so1}), Meridian agreed in writing naming both invoices and the amount (mail seq {s_so2}), Kolbe paid the rest (payment advice, mail seq {s_so3}). "
            "Section 6 of MDS-KOL-SUB-2025-001 and Section 8 of KOL-MDS-FWA-2025-001 allow this. The agent must not claim EUR 4,100.00 or pay "
            "RE-2026-0270."
        ),
    )
)
S.append(
    dict(
        id="s7_equal_invoices_are_separate_deliveries",
        polarity="absent",
        category="hallucination",
        description=(
            f"RE-2026-0207 and RE-2026-0216 are both {eur(a('RE-2026-0207'))}; RE-2026-0244 and RE-2026-0270 are both {eur(a('RE-2026-0244'))}. "
            f"They are part deliveries: PO-MDS-2026-0171 is 40 sensors in two halves of 20 x 78.00 (mail seq {s_po171}); PO-MDS-2026-0215 is "
            f"32 kits in call-offs of 10, 10 and 12 at 410.00 (mail seq {s_po215}). The agent must not report a double payment."
        ),
    )
)
S.append(
    dict(
        id="s8_april_paid_on_the_next_business_day",
        polarity="absent",
        category="hallucination",
        description=(
            "MDS-2026-04 (EUR 5,000.00) is due 2026-05-01 and was paid on 2026-05-04 (MDS-2026-04-P1), which looks three days late. 2026-05-01 is "
            "Labour Day, a public holiday in Barcelona, followed by a weekend; Section 4.2 of MDS-KOL-SUB-2025-001 makes a payment on the next "
            "business day, Monday 2026-05-04, on time. The agent must not claim interest or the EUR 40.00 of Section 4.4."
        ),
    )
)

S.append(
    dict(
        id="s9_reissued_invoice_cancelled_by_credit_note",
        polarity="absent",
        category="hallucination",
        description=(
            f"9000010412 (2026-09-28, {eur(a(rei))}) and 9000010427 (2026-09-29, {eur(a('9000010427'))}) bill the same 7 KS-8 hubs, delivery note "
            f"LS-2026-1342 (mail seq {s_rei_in} and {s_rei_new}). 9000010412 had no PO number; Meridian returned it under Section 5.2 of "
            f"KOL-MDS-FWA-2025-001 (mail seq {s_rei_ret}). Kolbe cancelled it in full with credit note 9000000109 ({rei_cn}, 2026-09-29) and "
            f"reissued it as 9000010427 (mail seq {s_rei_new}). Section 5.3 is met: {eur(a(rei))} - {eur(amt(rei_cn))} = EUR {rei_open:,.2f} open "
            "on 9000010412, and 9000010427 is owed once. Unlike p4, where 9000010498 has no credit note. The agent must not call 9000010427 a "
            "duplicate or hold it as one (it is held only because of p1)."
        ),
    )
)

f = open(f"{OUT}/expected.json", "w")
json.dump({"patterns": P + S}, f, indent=2, ensure_ascii=False)
f.write("\n")
f.close()
print(
    "now",
    NOW,
    "| at risk",
    at_risk,
    "net",
    net_now,
    "| p2 short",
    short,
    "late",
    late,
    "pay",
    pay_net,
    "| p3",
    sep_x,
    oct_x,
    due3,
    "| hours",
    q1,
    q2,
    q3,
)
