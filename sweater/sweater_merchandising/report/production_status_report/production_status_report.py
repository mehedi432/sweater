import frappe
from frappe import _
from frappe.utils import escape_html, flt, formatdate, getdate, today

def norm_gauge(g):
	"""'12gg', '12 GG', '12Gg' -> '12GG'; '5, 7 gg' -> '5,7GG'. Blank -> 'N/A'."""
	g = (g or "").upper().replace("GAUGE", "").replace(" ", "")
	if not g:
		return "N/A"
	return g if g.endswith("GG") else g + "GG"


GROUP_ORDER = ["Green", "Red", "None"]
GROUP_COLORS = {"Green": "#0a8043", "Red": "#c8102e", "None": "#5f6b7a"}

INK = "#0a0a0a"      # text
GRID = "#0a0a0a"     # grid lines
HEAD_BG = "#ffffff"  # header band (black & white)
SOFT = "#f2f2f2"     # total rows
FONT = "font-family:'Inter','SF Pro Display','Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif;font-size:12.5px;color:" + INK + ";line-height:1.3;"
PRINT = "-webkit-print-color-adjust:exact;print-color-adjust:exact;"
TD = (
	FONT + PRINT + "border:1px solid " + GRID + ";padding:0 4px;text-align:center;"
	"vertical-align:middle;background:#fff;word-wrap:break-word;font-variant-numeric:tabular-nums;"
)
ROW_H = 36    # px, each schedule row
TOTAL_H = 28  # px, each total row
HEAD_H = 48   # px, column header row


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


def get_docs(filters):
	f = {"report_date": filters.get("report_date") or today()}
	for key in ("buyer", "season"):
		if filters.get(key):
			f[key] = filters[key]
	names = frappe.get_all("Production Status", filters=f, order_by="creation asc", pluck="name")
	docs = [frappe.get_doc("Production Status", n) for n in names]
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
		f'<td {a} style="{TD}padding:0;vertical-align:top;background:{bg};color:{color};{extra}">'
		f'<div class="ps-diag-box" data-line="{line}" style="position:relative;height:{height}px;width:100%;">'
		f'<div style="position:absolute;z-index:2;top:5px;left:6px;text-align:left;">{top}</div>'
		f'<div style="position:absolute;z-index:2;bottom:5px;right:6px;text-align:right;font-weight:700;">{bottom}</div>'
		f'</div></td>'
	)


def render_sheet(docs, filters):
	if not docs:
		return '<p style="padding:20px">No Production Status records found for these filters.</p>'

	buyer = filters.get("buyer") or docs[0].buyer or ""
	season = filters.get("season") or docs[0].season or ""
	title = " - ".join(x for x in (buyer.upper(), season.upper()) if x)
	date_txt = formatdate(filters.get("report_date") or today(), "dd-MMM-yy")

	widths = [4, 8, 5.5, 8, 8.5, 9, 8, 11, 38]
	out = ['<div class="ps-sheet" style="overflow-x:auto">']
	out.append(
		f'<table style="border-collapse:collapse;width:100%;table-layout:fixed;border:1px solid {GRID};{FONT}">'
	)
	out.append("<colgroup>" + "".join(f'<col style="width:{w}%">' for w in widths) + "</colgroup>")

	# title band
	out.append(
		'<tr style="height:52px">'
		+ td(e(title), "font-size:21px;font-weight:800;letter-spacing:3px;", colspan="8")
		+ td(e(date_txt), "font-size:13px;font-weight:700;letter-spacing:.5px;")
		+ "</tr>"
	)

	# column header band
	h = f"background:{HEAD_BG};color:{INK};font-weight:800;font-size:10px;letter-spacing:0.2px;text-transform:uppercase;border-bottom:2px solid {GRID};"
	out.append(
		f'<tr style="height:{HEAD_H}px">'
		+ td("SL<br>No", h) + td("Style", h) + td("GG", h) + td("Qty", h)
		+ td("Ex-Fty<br>Date", h) + td("Yarn<br>Status", h) + td("PPS", h)
		+ diag_cell("KNITTING", "LINKING", HEAD_H - 2, bg=HEAD_BG, line=INK, color=INK,
			extra="font-size:8px;font-weight:500;letter-spacing:0.2px;text-transform:uppercase;border-bottom:2px solid " + GRID + ";")
		+ td("Remarks", h)
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
					f'<tr style="height:26px"><td colspan="9" style="{TD}background:{color};color:#fff;'
					f'font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:3px;">{e(current_group)}</td></tr>'
				)
		sl += 1
		rows = list(d.schedules) or [frappe._dict()]
		span = len(rows) + 1
		total = sum(flt(r.get("qty")) for r in rows) or flt(d.total_order_qty)
		g = norm_gauge(d.gauge)
		gauge_totals[g] = gauge_totals.get(g, 0) + total
		grand_total += total

		for j, s in enumerate(rows):
			tr = f'<tr style="height:{ROW_H}px">'
			if j == 0:
				tr += td(sl, "font-weight:600;", rowspan=span)
				tr += td(e(d.style_name), "font-size:9px;font-weight:800;letter-spacing:0.6px;", rowspan=span)
				tr += td(e(d.gauge), "font-size:9px;", rowspan=span)
			tr += td(f"{int(flt(s.get('qty'))):,}" if s.get("qty") else "")
			tr += td(formatdate(s.get("ex_factory_date"), "dd.MM.yy") if s.get("ex_factory_date") else "")
			if j == 0:
				tr += td(multiline(d.yarn_status), "font-size:9px;font-weight:600;", rowspan=span)
				tr += td(multiline(d.pps_status), "font-size:9px;font-weight:600;", rowspan=span)
				if d.knitting or d.linking:
					tr += diag_cell(multiline(d.knitting), multiline(d.linking),
						len(rows) * ROW_H + TOTAL_H - 2, rowspan=span)
				else:
					tr += td("", rowspan=span)
				tr += td(
					'<span class="ps-remarks">' + multiline(d.remarks) + "</span>",
					"text-align:left;font-size:9px;vertical-align:top;padding:6px 8px;line-height:1.4;",
					rowspan=span,
				)
			tr += "</tr>"
			out.append(tr)
		out.append(
			f'<tr style="height:{TOTAL_H}px">'
			+ td(f"{int(total):,}", "font-weight:700;font-size:11x;background:#f2f2f2;")
			+ td("", "background:#f2f2f2;")
			+ "</tr>"
		)

	# gauge summary + grand total, aligned to the Style / GG / Qty columns
	out.append('<tr><td colspan="9" style="border:0;height:12px;padding:0;background:#fff"></td></tr>')
	for g, qty in sorted(gauge_totals.items()):
		out.append(
			'<tr style="height:28px"><td style="border:0;background:#fff"></td>'
			+ td(e(g), "font-weight:800;background:" + SOFT + ";", colspan="2")
			+ td(f"{int(qty):,}", "font-weight:800;font-size:11px;")
			+ td("PCS", "font-weight:700;font-size:11px;letter-spacing:1px;")
			+ '<td colspan="4" style="border:0;background:#fff"></td></tr>'
		)
	out.append(
		'<tr style="height:34px"><td style="border:0;background:#fff"></td>'
		+ td("GRAND TOTAL", "font-weight:800;letter-spacing:1px;background:#fff;color:#0a0a0a;border:1px solid #0a0a0a;", colspan="2")
		+ td(f"{int(grand_total):,}", "font-weight:800;font-size:8px;border:1px solid #0a0a0a;")
		+ td("PCS", "font-weight:700;font-size:10px;letter-spacing:1px;border:1px solid #0a0a0a;")
		+ '<td colspan="4" style="border:0;background:#fff"></td></tr>'
	)
	out.append("</table></div>")
	return "".join(out)