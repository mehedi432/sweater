import os
import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, date_diff

DOCTYPE = "Order Sheet Entry"
TNA_FIELD = "production_tna"
QTY_FIELDS = ("order_qty", "po_qty", "total_qty", "qty")
WEEKLY_OFF = 4  # Friday
MAX_DAYS = 400
SECTIONS = ["KNITTING", "LINKING", "MENDING", "HOLE BUTTON", "SEWING", "POLY"]
START_WORDS = ("START", "BEGIN")
CLOSE_WORDS = ("CLOSE", "END", "FINISH", "COMPLETE")


def key(s):
    return s.lower().replace(" ", "_")


def pick(doc, *fields):
    for f in fields:
        v = doc.get(f)
        if v:
            return v
    return ""


def fdate(d, fmt="%d-%m-%Y"):
    return getdate(d).strftime(fmt) if d else ""


def get_tna_rows(doc):
    rows = doc.get(TNA_FIELD)
    if rows:
        return rows
    for df in doc.meta.get_table_fields():
        if "tna" in f"{df.fieldname} {df.options}".lower() and doc.get(df.fieldname):
            return doc.get(df.fieldname)
    return []


def get_qty(doc):
    for f in QTY_FIELDS:
        if flt(doc.get(f)):
            return int(flt(doc.get(f)))
    return 0


def read_tna(doc):
    tna = {}
    for r in get_tna_rows(doc):
        act = " ".join((r.get("activity") or "").upper().split())
        d = r.get("actual_date") or r.get("planned_date")  # actual date first
        if act and d:
            tna[act] = getdate(d)
    return tna


def find_date(tna, section, words):
    kind = "START" if words is START_WORDS else "CLOSE"
    exact = tna.get(f"{section} {kind} DATE")
    if exact:
        return exact
    for act, d in tna.items():
        if act.startswith(section) and any(w in act for w in words):
            return d
    return None


def build_plans(tna, Q, warnings):
    plans = {}
    for s in SECTIONS:
        st = find_date(tna, s, START_WORDS)
        en = find_date(tna, s, CLOSE_WORDS)
        if not (st and en):
            continue
        if st.weekday() == WEEKLY_OFF:
            st = getdate(add_days(st, 1))
        if en.weekday() == WEEKLY_OFF:
            en = getdate(add_days(en, -1))
        if st > en:
            warnings.append(f"{s}: start date is after close date, adjusted")
            st = en
        wd = sum(1 for i in range(date_diff(en, st) + 1)
                 if getdate(add_days(st, i)).weekday() != WEEKLY_OFF) or 1
        plans[s] = dict(start=st, close=en, workdays=wd, base=Q // wd,
                        rem=Q % wd, n=0, run=0, week=0, prevw=0)
    missing = [s for s in SECTIONS if s not in plans]
    if missing and plans:
        warnings.append("TnA dates missing for: " + ", ".join(missing))
    return plans


def build_rows(plans, Q):
    first = min(p["start"] for p in plans.values())
    last = max(p["close"] for p in plans.values())
    rows = []
    for i in range(date_diff(last, first) + 1):
        d = getdate(add_days(first, i))
        fri = d.weekday() == WEEKLY_OFF
        cells = {}
        for s in SECTIONS:
            p = plans.get(s)
            c = None
            if fri:
                if p and (p["week"] > 0 or p["run"] > 0):
                    c = dict(prev=p["prevw"], qty=p["week"], cum=p["run"])
                if p:
                    p["prevw"], p["week"] = p["week"], 0
            elif p and p["start"] <= d <= p["close"] and p["run"] < Q:
                p["n"] += 1
                prev = p["run"]
                q = p["base"] + (1 if p["n"] <= p["rem"] else 0)
                if d == p["close"]:
                    q = Q - prev
                q = max(0, min(q, Q - prev))
                p["run"] += q
                p["week"] += q
                if q > 0:
                    c = dict(prev=prev, qty=q, cum=p["run"])
            cells[s] = c
        rows.append(dict(kind="friday" if fri else "day",
                         date=d.strftime("%d-%m-%y"),
                         dayname=d.strftime("%A"), cells=cells))
    return rows


def render_html(ctx):
    path = os.path.join(os.path.dirname(__file__), "plan_template.html")
    with open(path, encoding="utf-8") as f:
        return frappe.render_template(f.read(), ctx)


def get_columns():
    cols = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Data", "width": 90},
        {"label": _("Day"), "fieldname": "day", "fieldtype": "Data", "width": 110},
    ]
    for s in SECTIONS:
        cols += [
            {"label": f"{s.title()} Qty", "fieldname": key(s) + "_qty", "fieldtype": "Int", "width": 95},
            {"label": f"{s.title()} Cum.", "fieldname": key(s) + "_cum", "fieldtype": "Int", "width": 95},
        ]
    return cols


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()

    if not filters.order_sheet_entry:
        return columns, [], _("Select an Order Sheet Entry")
    if not frappe.db.exists(DOCTYPE, filters.order_sheet_entry):
        return columns, [], _("{0} {1} not found").format(DOCTYPE, filters.order_sheet_entry)
    if not frappe.has_permission(DOCTYPE, "read", filters.order_sheet_entry):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = frappe.get_doc(DOCTYPE, filters.order_sheet_entry)
    warnings = []

    Q = get_qty(doc)
    if Q <= 0:
        return columns, [], _("Order quantity is zero or missing. Checked: {0}").format(", ".join(QTY_FIELDS))

    tna = read_tna(doc)
    if not tna:
        return columns, [], _("No TnA rows with dates found in this document")

    plans = build_plans(tna, Q, warnings)
    if not plans:
        return columns, [], _("No section has both start and close dates.<br>TnA found: {0}").format(
            ", ".join(f"{a} ({d})" for a, d in tna.items()))

    span = date_diff(max(p["close"] for p in plans.values()),
                     min(p["start"] for p in plans.values()))
    if span > MAX_DAYS:
        return columns, [], _("Date range is over {0} days. Check TnA dates.").format(MAX_DAYS)

    rows = build_rows(plans, Q)

    final_cells, totals, has = {}, {}, {}
    for s in SECTIONS:
        p = plans.get(s)
        has[s] = bool(p)
        final_cells[s] = dict(prev=p["prevw"], qty=p["week"], cum=p["run"]) if p else None
        totals[s] = dict(run=p["run"], done=p["run"] == Q, balance=Q - p["run"]) if p else None
        if p and p["run"] != Q:
            warnings.append(f"{s}: total {p['run']} does not match order qty {Q}")

    summary_rows = []
    for s in SECTIONS:
        p = plans.get(s)
        summary_rows.append(dict(
            name=s, plan=bool(p),
            start=fdate(p["start"]) if p else "", close=fdate(p["close"]) if p else "",
            workdays=p["workdays"] if p else "", base=p["base"] if p else "",
            rem=p["rem"] if p else "", final=p["run"] if p else "",
            balance=(Q - p["run"]) if p else ""))

    yarn = tna.get("YARN INHOUSE DATE")
    ship = pick(doc, "shipment_date", "delivery_date", "ex_factory_date")
    info = dict(
        buyer=pick(doc, "buyer", "buyer_name", "customer"),
        style=pick(doc, "style_name", "style", "item_name"),
        po=pick(doc, "po_number", "po_no", "purchase_order"),
        colour=pick(doc, "color", "colour", "color_name", "colour_name"),
        gauge=pick(doc, "gauge", "gg"),
        ship=fdate(ship),
        order_ref=pick(doc, "order_number", "order_no", "sales_order") or doc.name,
        yarn=fdate(yarn), season=pick(doc, "season"),
        merch=pick(doc, "merchandiser", "merchant"))

    letter_head = frappe.db.get_value("Letter Head", {"is_default": 1}, "content")

    html = render_html(dict(
        info=info, Q=Q, sections=SECTIONS, rows=rows, has=has,
        final_cells=final_cells, totals=totals, summary_rows=summary_rows,
        warnings=warnings, letter_head=letter_head))

    # plain grid (used for Excel export)
    data = []
    for r in rows:
        row = {"date": r["date"], "day": r["dayname"] + (" - WEEKLY" if r["kind"] == "friday" else "")}
        for s in SECTIONS:
            c = r["cells"][s]
            if c:
                row[key(s) + "_qty"], row[key(s) + "_cum"] = c["qty"], c["cum"]
        data.append(row)
    data.append({"date": "GRAND TOTAL", "day": "",
                 **{key(s) + "_cum": totals[s]["run"] for s in SECTIONS if totals[s]}})

    return columns, data, html