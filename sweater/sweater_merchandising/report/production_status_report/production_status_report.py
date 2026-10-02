import frappe
from frappe import _
from frappe.utils import escape_html, flt, formatdate, today


def norm_gauge(g):
	"""'12gg', '12 GG', '12Gg' -> '12GG'; '5, 7 gg' -> '5,7GG'. Blank -> 'N/A'."""
	g = (g or "").upper().replace("GAUGE", "").replace(" ", "")
	if not g:
		return "N/A"
	return g if g.endswith("GG") else g + "GG"


GROUP_ORDER = ["Green", "Red", "None"]
GROUP_COLORS = {"Green": "#0a8043", "Red": "#c8102e", "None": "#5f6b7a"}

INK = "#0a0a0a"
GRID = "#0a0a0a"
HEAD_BG = "#ffffff"
SOFT = "#f2f2f2"
FONT = (
	"font-family:'Inter','SF Pro Display','Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif;"
	"font-size:13px;color:" + INK + ";line-height:1.3;"
)
PRINT = "-webkit-print-color-adjust:exact;print-color-adjust:exact;"
TD = (
	FONT + PRINT + "border:1px solid " + GRID + ";padding:0 5px;text-align:center;"
	"vertical-align:middle;background:#fff;word-wrap:break-word;font-variant-numeric:tabular-nums;"
)

NOWRAP = "white-space:nowrap;padding:0 10px;"   # keep style / date / qty on one line
SHRINK = "width:1%;"                              # column shrinks to its content; Remarks takes the rest

ROW_H = 38      # px, schedule row when a style has 2+ ex-factory dates
TOTAL_H = 30    # px, total row (only for styles with 2+ dates)
SINGLE_H = 64   # px, a style with ONE ex-factory date (no total row)
HEAD_H = 52     # px, column header row


def execute(filters=None):
	filters = frappe._dict(filters or {})
	docs = get_docs(filters)
	return get_columns(), get_data(docs), render_sheet(docs, filters)


def get_columns():
	return [
		{"label": _("SL"), "fieldname": "sl", "fieldtype": "Int", "width": 89},
		{"label": _("Style"), "fieldname": "style", "fieldtype": "Data", "width": 120},
		{"label": _("GG"), "fieldname": "gauge", "fieldtype": "Data", "width": 70},
		{"label": _("Qty"), "fieldname": "qty", "fieldtype": "Int", "width": 90},
		{"label": _("Ex-Fty Date"), "fieldname": "ex_factory_date", "fieldtype": "Date", "width": 100},
		{"label": _("Yarn Status"), "fieldname": "yarn_status", "fieldtype": "Data", "width": 120},
		{"label": _("PPS"), "fieldname": "pps_status", "fieldtype": "Data", "width": 100},
		{"label": _("Knitting"), "fieldname": "knitting", "fieldtype": "Data", "width": 200},
		{"label": _("Linking"), "fieldname": "linking", "fieldtype": "Data", "width": 200},
		{"label": _("Remarks"), "fieldname": "remarks", "fieldtype": "Data", "width": 300},
	]


_osv_cache = {}


def osv_value(doc, fieldname):
	"""Value from the linked Order Sheet Entry (fallback when the stored field is blank)."""
	key = (doc.order_sheet_entry, fieldname)
	if key not in _osv_cache:
		val = ""
		try:
			if doc.order_sheet_entry and frappe.get_meta("Order Sheet Entry").has_field(fieldname):
				val = frappe.db.get_value("Order Sheet Entry", doc.order_sheet_entry, fieldname) or ""
		except Exception:
			val = ""
		_osv_cache[key] = val
	return _osv_cache[key]


def doc_value(doc, fieldname):
	return (doc.get(fieldname) or osv_value(doc, fieldname) or "").strip()


def get_docs(filters):
	_osv_cache.clear()
	names = frappe.get_all(
		"Production Status",
		filters={"report_date": filters.get("report_date") or today()},
		order_by="creation asc",
		pluck="name",
	)
	docs = [frappe.get_doc("Production Status", n) for n in names]

	# Buyer / Season: case-insensitive "contains" match, falls back to the Order Sheet Entry value
	for key in ("buyer", "season"):
		wanted = (filters.get(key) or "").strip().lower()
		if wanted:
			docs = [d for d in docs if wanted in doc_value(d, key).lower()]

	docs.sort(key=lambda d: GROUP_ORDER.index(d.row_group) if d.row_group in GROUP_ORDER else 99)
	return docs


def get_data(docs):
	data = []
	for i, d in enumerate(docs, 1):
		rows = d.schedules or [frappe._dict()]
		for j, s in enumerate(rows):
			data.append({
				"sl": i if j == 0 else None,
				"style": d.style_name if j == 0 else None,
				"gauge": d.gauge if j == 0 else None,
				"qty": s.get("qty"),
				"ex_factory_date": s.get("ex_factory_date"),
				"yarn_status": d.yarn_status if j == 0 else None,
				"pps_status": d.pps_status if j == 0 else None,
				"knitting": d.knitting if j == 0 else None,
				"linking": d.linking if j == 0 else None,
				"remarks": d.remarks if j == 0 else None,
			})
	return data


def e(v):
	return escape_html(v or "")


def td(content="", style="", **attrs):
	a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
	return f'<td {a} style="{TD}{style}">{content}</td>'


def multiline(v):
	return e(v).replace("\n", "<br>")


def diag_cell(top, bottom, height, bg="#fff", line=INK, color=INK, extra="", **attrs):
	a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
	return (
		f'<td {a} style="{TD}padding:0;vertical-align:top;min-width:170px;width:14%;background:{bg};color:{color};{extra}">'
		f'<div class="ps-diag-box" data-line="{line}" style="position:relative;height:{height}px;width:100%;">'
		f'<div style="position:absolute;z-index:2;top:6px;left:8px;text-align:left;">{top}</div>'
		f'<div style="position:absolute;z-index:2;bottom:6px;right:8px;text-align:right;font-weight:700;">{bottom}</div>'
		f'</div></td>'
	)


def render_sheet(docs, filters):
	if not docs:
		return '<p style="padding:20px">No Production Status records found for these filters.</p>'

	buyer = doc_value(docs[0], "buyer") or (filters.get("buyer") or "")
	season = doc_value(docs[0], "season") or (filters.get("season") or "")
	title = " - ".join(x for x in (buyer.upper(), season.upper()) if x)
	date_txt = formatdate(filters.get("report_date") or today(), "dd-MMM-yy")

	out = ['<div class="ps-sheet" style="overflow-x:auto">']
	out.append(
		f'<table style="border-collapse:collapse;width:100%;table-layout:auto;border:1px solid {GRID};{FONT}">'
	)

	out.append(
		'<tr style="height:56px">'
		+ td(e(title), "font-size:24px;font-weight:800;letter-spacing:3px;", colspan="8")
		+ td(e(date_txt), "font-size:15px;font-weight:700;letter-spacing:.5px;white-space:nowrap;")
		+ "</tr>"
	)

	h = (
		f"background:{HEAD_BG};color:{INK};font-weight:800;font-size:12px;letter-spacing:.6px;"
		f"text-transform:uppercase;border-bottom:2px solid {GRID};"
	)
	out.append(
		f'<tr style="height:{HEAD_H}px">'
		+ td("SL<br>No", h + NOWRAP + SHRINK) + td("Style", h + NOWRAP + SHRINK) + td("GG", h + NOWRAP + SHRINK)
		+ td("Qty", h + NOWRAP + SHRINK) + td("Ex-Fty<br>Date", h + NOWRAP + SHRINK)
		+ td("Yarn<br>Status", h + SHRINK + "min-width:95px;") + td("PPS", h + SHRINK + "min-width:80px;")
		+ diag_cell("KNITTING", "LINKING", HEAD_H - 2, bg=HEAD_BG, line=INK, color=INK,
			extra="font-size:11px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;"
			"border-bottom:2px solid " + GRID + ";")
		+ td("Remarks", h + "font-size:14px;min-width:260px;")
		+ "</tr>"
	)

	gauge_totals = {}
	grand_total = 0
	current_group = None
	sl = 0
	for d in docs:
		if d.row_group != current_group:
			current_group = d.row_group
			if current_group != "None":
				color = GROUP_COLORS.get(current_group, "#5f6b7a")
				out.append(
					f'<tr style="height:28px"><td colspan="9" style="{TD}background:{color};color:#fff;'
					f'font-weight:800;font-size:12px;text-transform:uppercase;letter-spacing:4px;">{e(current_group)}</td></tr>'
				)
		sl += 1
		rows = list(d.schedules) or [frappe._dict()]
		multi = len(rows) > 1                      # 2+ ex-factory dates -> show a total row
		row_h = ROW_H if multi else SINGLE_H
		span = len(rows) + 1 if multi else 1
		total = sum(flt(r.get("qty")) for r in rows) or flt(d.total_order_qty)
		g = norm_gauge(d.gauge)
		gauge_totals[g] = gauge_totals.get(g, 0) + total
		grand_total += total
		box_h = len(rows) * row_h + (TOTAL_H if multi else 0) - 2

		for j, s in enumerate(rows):
			tr = f'<tr style="height:{row_h}px">'
			if j == 0:
				tr += td(sl, "font-weight:600;font-size:14px;" + NOWRAP, rowspan=span)
				tr += td(e(d.style_name), "font-size:15px;font-weight:800;letter-spacing:.6px;" + NOWRAP, rowspan=span)
				tr += td(e(d.gauge), "font-size:12px;" + NOWRAP, rowspan=span)
			qty_txt = f"{int(flt(s.get('qty'))):,}" if s.get("qty") else ""
			tr += td(qty_txt, "font-size:14px;" + NOWRAP + ("" if multi else "font-weight:700;"))
			tr += td(formatdate(s.get("ex_factory_date"), "dd.MM.yy") if s.get("ex_factory_date") else "", "font-size:13px;" + NOWRAP)
			if j == 0:
				tr += td(multiline(d.yarn_status), "font-size:12px;font-weight:600;", rowspan=span)
				tr += td(multiline(d.pps_status), "font-size:12px;font-weight:600;", rowspan=span)
				if d.knitting or d.linking:
					tr += diag_cell(multiline(d.knitting), multiline(d.linking), box_h,
						extra="font-size:14px;", rowspan=span)
				else:
					tr += td("", rowspan=span)
				tr += td(
					'<span class="ps-remarks">' + multiline(d.remarks) + "</span>",
					"text-align:left;font-size:12.5px;vertical-align:top;padding:7px 10px;line-height:1.45;",
					rowspan=span,
				)
			tr += "</tr>"
			out.append(tr)
		if multi:  # total row only when there is more than one ex-factory date
			out.append(
				f'<tr style="height:{TOTAL_H}px">'
				+ td(f"{int(total):,}", "font-weight:800;font-size:14px;white-space:nowrap;background:" + SOFT + ";")
				+ td("", "background:" + SOFT + ";")
				+ "</tr>"
			)

	out.append('<tr><td colspan="9" style="border:0;height:12px;padding:0;background:#fff"></td></tr>')
	for g, qty in sorted(gauge_totals.items()):
		out.append(
			'<tr style="height:30px"><td style="border:0;background:#fff"></td>'
			+ td(e(g), "font-weight:800;font-size:13px;white-space:nowrap;background:" + SOFT + ";", colspan="2")
			+ td(f"{int(qty):,}", "font-weight:800;font-size:14px;white-space:nowrap;")
			+ td("PCS", "font-weight:700;font-size:12px;letter-spacing:1px;")
			+ '<td colspan="4" style="border:0;background:#fff"></td></tr>'
		)
	out.append(
		'<tr style="height:36px"><td style="border:0;background:#fff"></td>'
		+ td("GRAND TOTAL", "white-space:nowrap;font-size:12px;font-weight:800;letter-spacing:1px;border:2px solid #0a0a0a;", colspan="2")
		+ td(f"{int(grand_total):,}", "font-weight:800;font-size:15px;border:2px solid #0a0a0a;")
		+ td("PCS", "font-weight:700;font-size:12px;letter-spacing:1px;border:2px solid #0a0a0a;")
		+ '<td colspan="4" style="border:0;background:#fff"></td></tr>'
	)
	out.append("</table></div>")
	return "".join(out)