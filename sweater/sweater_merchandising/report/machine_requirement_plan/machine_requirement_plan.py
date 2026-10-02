import math
import os
import re
from bisect import bisect_left

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, add_days, date_diff, nowdate

DOCTYPE = "Order Sheet Entry"
TNA_FIELD = "production_tna"
QTY_FIELDS = ("order_qty", "po_qty", "total_qty", "qty")
SHIP_FIELDS = ("shipment_date", "delivery_date", "ex_factory_date")
WEEKLY_OFF = 4   # Friday
WEEK_START = 5   # Saturday
MAX_ORDERS = 1500
MAX_HORIZON = 540
TIGHT_DAYS = 3
EPS = 1e-6
START_WORDS = ("START", "BEGIN")
CLOSE_WORDS = ("CLOSE", "END", "FINISH", "COMPLETE")


# ------------------------------------------------------------ helpers
def num(v):
    m = re.search(r"\d+(?:\.\d+)?", str(v or "").replace(",", ""))
    return flt(m.group()) if m else 0


def fdate(d, fmt="%d-%m-%Y"):
    return getdate(d).strftime(fmt) if d else ""


def pick(doc, *fields):
    for f in fields:
        if doc.get(f):
            return doc.get(f)
    return ""


def get_qty(doc):
    for f in QTY_FIELDS:
        if flt(doc.get(f)):
            return int(flt(doc.get(f)))
    return 0


def get_knit_time(doc):
    if doc.get("knitting_time"):
        return num(doc.get("knitting_time"))
    for df in doc.meta.get_link_fields():
        val = doc.get(df.fieldname)
        if val and df.options and frappe.get_meta(df.options).has_field("knitting_time"):
            t = frappe.db.get_value(df.options, val, "knitting_time")
            if t:
                return num(t)
    return 0


def read_tna(doc):
    rows = doc.get(TNA_FIELD)
    if not rows:
        for df in doc.meta.get_table_fields():
            if "tna" in f"{df.fieldname} {df.options}".lower() and doc.get(df.fieldname):
                rows = doc.get(df.fieldname)
                break
    tna = {}
    for r in rows or []:
        act = " ".join((r.get("activity") or "").upper().split())
        d = r.get("actual_date") or r.get("planned_date")
        if act and d:
            tna[act] = getdate(d)
    return tna


def knit_dates(tna):
    st, en = tna.get("KNITTING START DATE"), tna.get("KNITTING CLOSE DATE")
    for a, d in tna.items():
        if a.startswith("KNITTING"):
            if not st and any(w in a for w in START_WORDS):
                st = d
            if not en and any(w in a for w in CLOSE_WORDS):
                en = d
    return st, en


def week_of(d):
    return getdate(add_days(d, -((d.weekday() - WEEK_START) % 7)))


# ------------------------------------------------------------ scheduler
def schedule(jobs, n, days, cap_eff):
    """Finite-capacity, earliest-deadline-first. n machines share every working day."""
    room = [n * cap_eff] * len(days)
    res = {}
    for j in sorted(jobs, key=lambda x: (x["deadline"], x["earliest"], x["order"])):
        rem, i, alloc = j["minutes"], j["i0"], {}
        while rem > EPS and i < len(days):
            if room[i] > EPS:
                take = min(rem, room[i])
                room[i] -= take
                rem -= take
                alloc[i] = take
            i += 1
        res[j["order"]] = (alloc, rem)
    return res, room


def on_time(j, alloc, rem, days):
    return rem <= EPS and bool(alloc) and days[max(alloc)] <= j["deadline"]


def min_machines(jobs, days, cap_eff):
    ok_jobs = [j for j in jobs if j["window"]]
    if not ok_jobs:
        return 1

    def feasible(n):
        res, _r = schedule(ok_jobs, n, days, cap_eff)
        return all(on_time(j, *res[j["order"]], days) for j in ok_jobs)

    lo = 1
    hi = max(1, min(5000, math.ceil(sum(j["minutes"] for j in ok_jobs) / cap_eff)))
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ------------------------------------------------------------ visuals
def build_chart(week_rows, line):
    n = len(week_rows)
    if not n:
        return None
    W, H, top, bottom = 1000, 150, 16, 22
    ph = H - top - bottom
    ymax = (max([w["machines"] for w in week_rows] + [line or 0]) * 1.2) or 1
    slot = W / n
    bw = min(56, slot * 0.6)
    bars = []
    for i, w in enumerate(week_rows):
        h = ph * w["machines"] / ymax
        bars.append(dict(x=round(slot * i + (slot - bw) / 2, 1), y=round(top + ph - h, 1),
                         w=round(bw, 1), h=round(h, 1), cx=round(slot * i + slot / 2, 1),
                         label=w["short"], val=w["machines"]))
    return dict(W=W, H=H, bars=bars, base=top + ph, ly=H - 6, step=max(1, math.ceil(n / 16)),
                line_y=round(top + ph - ph * line / ymax, 1) if line else None)


def build_gantt(rows, d0, d1, limit=45):
    shown = rows[:limit]
    if not shown:
        return None
    W, label_w, top = 1000, 175, 22
    span = max(1, date_diff(d1, d0) + 1)
    pw = W - label_w - 12

    def sx(d):
        return round(label_w + pw * date_diff(d, d0) / span, 1)

    step = 7 if span <= 120 else (14 if span <= 240 else 30)
    ticks = []
    k = 0
    while k <= span:
        d = getdate(add_days(d0, k))
        ticks.append(dict(x=sx(d), label=fdate(d, "%d %b")))
        k += step

    out = []
    for i, r in enumerate(shown):
        y = top + i * 13
        item = dict(ty=y + 7, label=(r["order"][:26] + "…") if len(r["order"]) > 26 else r["order"],
                    y=y, late=r["late"])
        if r["start"] and r["close"]:
            x1, x2 = sx(r["start"]), sx(r["close"])
            item.update(x=x1, w=max(3, round(x2 - x1 + pw / span, 1)))
        dx, cy = sx(r["deadline"]), y + 4
        item["dpts"] = f"{dx},{cy-4.5} {dx+4.5},{cy} {dx},{cy+4.5} {dx-4.5},{cy}"
        item["sx"] = sx(r["ship"])
        item["cy"] = cy
        out.append(item)
    return dict(W=W, H=top + len(shown) * 13 + 6, ticks=ticks, rows=out,
                more=max(0, len(rows) - limit))


def get_columns():
    return [
        {"label": _("Order"), "fieldname": "order", "fieldtype": "Link", "options": DOCTYPE, "width": 190},
        {"label": _("Buyer"), "fieldname": "buyer", "fieldtype": "Data", "width": 110},
        {"label": _("Style"), "fieldname": "style", "fieldtype": "Data", "width": 110},
        {"label": _("Order Qty"), "fieldname": "qty", "fieldtype": "Int", "width": 90},
        {"label": _("Knit Time (min/pc)"), "fieldname": "knit_time", "fieldtype": "Float", "width": 100},
        {"label": _("Machine Hours"), "fieldname": "hours", "fieldtype": "Float", "precision": 1, "width": 100},
        {"label": _("Shipment"), "fieldname": "ship_s", "fieldtype": "Data", "width": 95},
        {"label": _("Latest Knit Close"), "fieldname": "deadline_s", "fieldtype": "Data", "width": 110},
        {"label": _("Proposed Start"), "fieldname": "start_s", "fieldtype": "Data", "width": 105},
        {"label": _("Proposed Close"), "fieldname": "close_s", "fieldtype": "Data", "width": 105},
        {"label": _("Slack (days)"), "fieldname": "slack", "fieldtype": "Int", "width": 90},
        {"label": _("Peak Machines"), "fieldname": "machines", "fieldtype": "Int", "width": 100},
        {"label": _("Manpower"), "fieldname": "manpower", "fieldtype": "Int", "width": 90},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 220},
    ]


def render_html(ctx):
    path = os.path.join(os.path.dirname(__file__), "plan_template.html")
    with open(path, encoding="utf-8") as f:
        return frappe.render_template(f.read(), ctx)


# ------------------------------------------------------------ main
def execute(filters=None):
    filters = frappe._dict(filters or {})
    cap = flt(filters.machine_minutes) or 2100
    eff_pct = flt(filters.efficiency) or 100
    cap_eff = cap * eff_pct / 100
    wpm = flt(filters.workers_per_machine) or 1
    installed = cint(filters.available_machines)
    lead = cint(filters.get("lead_days", 14))
    plan_start = getdate(filters.from_date) if filters.from_date else getdate(nowdate())
    ship_to = getdate(filters.to_date) if filters.to_date else None
    sm = filters.get("show_missing")
    show_missing = True if sm is None else bool(cint(sm))
    columns = get_columns()

    names = frappe.get_list(DOCTYPE, filters={"docstatus": ["<", 2]}, pluck="name",
                            limit_page_length=MAX_ORDERS)

    jobs, gaps = [], []
    ignored_past = no_yarn = 0

    for name in names:
        doc = frappe.get_doc(DOCTYPE, name)
        Q, kt = get_qty(doc), get_knit_time(doc)
        ship_raw = pick(doc, *SHIP_FIELDS)

        issues = []
        if not Q:
            issues.append("Order qty missing")
        if not kt:
            issues.append("Knitting time missing")
        if not ship_raw:
            issues.append("Shipment date missing")

        base = dict(order=name, buyer=pick(doc, "buyer", "buyer_name", "customer"),
                    style=pick(doc, "style_name", "style", "item_name"),
                    qty=Q, knit_time=kt, minutes=Q * kt,
                    hours=(Q * kt / 60) or None)
        if issues:
            if show_missing:
                base.update(issues=issues, ship_s=fdate(ship_raw),
                            actions="Complete the missing fields to include this order")
                gaps.append(base)
            continue

        ship = getdate(ship_raw)
        if ship < plan_start:
            ignored_past += 1
            continue
        if ship_to and ship > ship_to:
            continue

        tna = read_tna(doc)
        deadline = getdate(add_days(ship, -lead))
        if deadline.weekday() == WEEKLY_OFF:
            deadline = getdate(add_days(deadline, -1))
        yarn = tna.get("YARN INHOUSE DATE")
        if not yarn:
            no_yarn += 1
        earliest = max(plan_start, yarn) if yarn else plan_start
        cs, ce = knit_dates(tna)
        base.update(ship=ship, deadline=deadline, earliest=earliest, yarn=yarn,
                    cur_start=cs, cur_close=ce)
        jobs.append(base)

    if not jobs:
        msg = _("No schedulable orders. Orders need qty, knitting_time and a shipment date on or after the plan start.")
        if gaps:
            msg += "<br>" + _("{0} order(s) have missing data, e.g. {1}").format(
                len(gaps), ", ".join(g["order"] for g in gaps[:5]))
        return columns, [], msg

    # working-day calendar
    last = max(max(j["deadline"] for j in jobs), plan_start)
    horizon_end = min(getdate(add_days(last, 90)), getdate(add_days(plan_start, MAX_HORIZON)))
    days = []
    for i in range(date_diff(horizon_end, plan_start) + 1):
        d = getdate(add_days(plan_start, i))
        if d.weekday() != WEEKLY_OFF:
            days.append(d)

    for j in jobs:
        j["i0"] = bisect_left(days, j["earliest"])
        j["window"] = j["i0"] < len(days) and days[j["i0"]] <= j["deadline"]

    n_min = min_machines(jobs, days, cap_eff)
    n_plan = installed if installed > 0 else n_min

    res, room = schedule(jobs, n_plan, days, cap_eff)

    # per-order results
    orders = []
    for j in jobs:
        alloc, rem = res[j["order"]]
        r = dict(j)
        if alloc:
            r["start"], r["close"] = days[min(alloc)], days[max(alloc)]
            pk = max(alloc.values()) / cap_eff
            r["machines"] = max(1, math.ceil(pk - EPS))
            r["avg_m"] = j["minutes"] / cap_eff / max(1, len(alloc))
        else:
            r["start"] = r["close"] = None
            r["machines"], r["avg_m"] = 0, 0
        r["manpower"] = math.ceil(r["machines"] * wpm)

        if rem > EPS or not r["close"]:
            r.update(status="Unscheduled (beyond horizon)", cls="bad", late=True, slack=None)
        elif r["close"] > j["deadline"]:
            late_d = date_diff(r["close"], j["deadline"])
            note = " · yarn arrives too late" if not j["window"] else ""
            r.update(status=f"Late by {late_d} days{note}", cls="bad", late=True, slack=-late_d)
        else:
            sl = date_diff(j["deadline"], r["close"])
            r.update(status="Tight" if sl < TIGHT_DAYS else "On Time",
                     cls="warn" if sl < TIGHT_DAYS else "ok", late=False, slack=sl)
        r["start_s"], r["close_s"] = fdate(r["start"]), fdate(r["close"])
        r["ship_s"], r["deadline_s"] = fdate(j["ship"]), fdate(j["deadline"])
        r["yarn_s"] = fdate(j["yarn"]) if j["yarn"] else "-"
        r["cur_start_s"], r["cur_close_s"] = fdate(j["cur_start"]), fdate(j["cur_close"])
        r["shift"] = date_diff(r["close"], j["cur_close"]) if (r["close"] and j["cur_close"]) else None
        r["alloc"] = alloc
        orders.append(r)

    orders.sort(key=lambda r: (r["start"] or r["deadline"], r["deadline"]))
    total_min = sum(r["minutes"] for r in orders)
    total_hours = total_min / 60
    for r in orders:
        r["share"] = round(r["minutes"] * 100 / total_min, 1) if total_min else 0
    n_late = sum(1 for r in orders if r["late"])
    n_tight = sum(1 for r in orders if r["status"] == "Tight")

    # daily and weekly load
    day_machines = {}
    for i in range(len(days)):
        used = n_plan * cap_eff - room[i]
        if used > EPS:
            day_machines[days[i]] = used / cap_eff

    week_rows, matrix = [], []
    first_used = last_used = None
    if day_machines:
        first_used, last_used = min(day_machines), max(day_machines)
        wk = {}
        for d in days:
            if first_used <= d <= last_used:
                w = wk.setdefault(week_of(d), dict(days=0, peak=0, sumload=0, orders=set()))
                w["days"] += 1
                w["peak"] = max(w["peak"], day_machines.get(d, 0))
                w["sumload"] += day_machines.get(d, 0)
        for r in orders:
            for i in r["alloc"]:
                if days[i] in day_machines:
                    wk[week_of(days[i])]["orders"].add(r["order"])
        for ws in sorted(wk):
            w = wk[ws]
            m = math.ceil(w["peak"] - EPS) if w["peak"] > EPS else 0
            week_rows.append(dict(
                ws=ws, label=f"{fdate(ws, '%d %b')} - {fdate(add_days(ws, 5), '%d %b %Y')}",
                short=fdate(ws, "%d/%m"), days=w["days"], orders=len(w["orders"]),
                avg=round(w["sumload"] / w["days"], 1), machines=m,
                util=round(w["sumload"] * 100 / (n_plan * w["days"])) if n_plan else 0,
                manpower=math.ceil(m * wpm), hours=round(w["sumload"] * cap_eff / 60, 1),
                free=n_plan - m))

        # order x week distribution matrix (chunks of 12 weeks)
        cell = {}
        for r in orders:
            for i, mins in r["alloc"].items():
                key = (r["order"], week_of(days[i]))
                cell[key] = max(cell.get(key, 0), mins / cap_eff)
        for c0 in range(0, len(week_rows), 12):
            chunk = week_rows[c0:c0 + 12]
            rows = []
            for r in orders:
                if not r["alloc"]:
                    continue
                cells, any_v = [], False
                for w in chunk:
                    v = cell.get((r["order"], w["ws"]), 0)
                    v = math.ceil(v - EPS) if v > EPS else 0
                    any_v = any_v or v > 0
                    t = min(4, math.ceil(4 * v / n_plan)) if (v and n_plan) else 0
                    cells.append(dict(v=v, t=t))
                if any_v:
                    rows.append(dict(order=r["order"], cells=cells))
            matrix.append(dict(weeks=[w["short"] for w in chunk], rows=rows,
                               totals=[w["machines"] for w in chunk]))

    peak_m = max((w["machines"] for w in week_rows), default=0)
    peak_week = max(week_rows, key=lambda w: w["machines"]) if week_rows else None
    span_days = len([d for d in days if first_used and first_used <= d <= last_used])
    util = round(total_min * 100 / (n_plan * cap_eff * span_days)) if (n_plan and span_days) else 0
    last_close = max((r["close"] for r in orders if r["close"]), default=None)

    # what-if scenarios
    cand = {max(1, round(n_plan * f)) for f in (0.6, 0.8, 1, 1.2, 1.5)} | {n_min}
    if installed:
        cand.add(installed)
    scenarios = []
    for m in sorted(cand):
        sres, sroom = schedule(jobs, m, days, cap_eff)
        late = delay = 0
        fin = None
        for j in jobs:
            a, rem = sres[j["order"]]
            if rem > EPS or not a:
                late += 1
                continue
            f_ = days[max(a)]
            fin = f_ if not fin or f_ > fin else fin
            if f_ > j["deadline"]:
                late += 1
                delay = max(delay, date_diff(f_, j["deadline"]))
        note = []
        if m == n_min:
            note.append("Minimum for on-time")
        if installed and m == installed:
            note.append("Installed")
        if m == n_plan and not installed:
            note.append("Plan")
        scenarios.append(dict(machines=m, manpower=math.ceil(m * wpm), late=late, delay=delay,
                              finish=fdate(fin) or "-", note=" · ".join(note) or "-"))

    # smart insights
    insights = []
    n_ok = len([j for j in jobs if j["window"]])
    insights.append(f"{n_min} machine(s) are needed to finish {n_ok} order(s) {lead} days before shipment "
                    f"at {fmt_int(cap)} min/day and {eff_pct:g}% efficiency.")
    if installed:
        if installed >= n_min:
            insights.append(f"The {installed} installed machines cover the plan with {installed - n_min} spare.")
        else:
            worst = sorted([r for r in orders if r["late"]], key=lambda r: r["slack"] if r["slack"] is not None else -999)[:3]
            tail = (" Most affected: " + ", ".join(f"{r['order']} ({r['status']})" for r in worst)) if worst else ""
            insights.append(f"Shortfall: {installed} installed vs {n_min} needed. Add {n_min - installed} machine(s) "
                            f"or move {n_late} order(s) out.{tail}")
    if peak_week:
        insights.append(f"Peak load is in the week of {fdate(peak_week['ws'])}: {peak_week['machines']} machines "
                        f"and {fmt_int(peak_week['manpower'])} workers.")
    nowin = [r["order"] for r in orders if not r["window"]]
    if nowin:
        insights.append(f"{len(nowin)} order(s) have no workable window (yarn or plan start is after the latest "
                        f"knitting close): {', '.join(nowin[:5])}. Expedite yarn or renegotiate shipment.")
    if no_yarn:
        insights.append(f"{no_yarn} order(s) have no Yarn In-House date in TnA, so knitting may start on the plan start date.")
    if ignored_past:
        insights.append(f"{ignored_past} order(s) with shipment before the plan start were ignored.")
    if gaps:
        insights.append(f"{len(gaps)} order(s) are excluded until their data is completed (see Data Gaps).")

    gantt = build_gantt(orders, min([plan_start] + [r["start"] for r in orders if r["start"]]),
                        max([r["deadline"] for r in orders] + [r["close"] for r in orders if r["close"]]))

    letter_head = frappe.db.get_value("Letter Head", {"is_default": 1}, "content")
    html = render_html(dict(
        orders=orders, gaps=gaps, weeks=week_rows, matrix=matrix, scenarios=scenarios,
        insights=insights, gantt=gantt, chart=build_chart(week_rows, n_plan),
        letter_head=letter_head, cap=cap, eff=eff_pct, wpm=wpm, lead=lead,
        installed=installed, n_min=n_min, n_plan=n_plan,
        p_from=fdate(plan_start), p_to=fdate(ship_to) or "-",
        total_qty=sum(r["qty"] for r in orders), total_hours=total_hours,
        n_late=n_late, n_tight=n_tight, util=util, peak_m=peak_m,
        peak_mp=math.ceil(peak_m * wpm), last_close=fdate(last_close) or "-",
        gap_hours=sum(g["hours"] or 0 for g in gaps),
        user=frappe.utils.get_fullname(frappe.session.user),
        now=frappe.utils.now_datetime().strftime("%d-%m-%Y %H:%M")))

    data = [dict(r) for r in orders]
    for g in gaps:
        data.append(dict(order=g["order"], buyer=g["buyer"], style=g["style"], qty=g["qty"],
                         knit_time=g["knit_time"], hours=g["hours"], ship_s=g["ship_s"],
                         status="Missing: " + ", ".join(g["issues"])))
    return columns, data, html


def fmt_int(v):
    return f"{int(v or 0):,}"