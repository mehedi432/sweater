frappe.query_reports["Production Status Report"] = {
	filters: [
		{ fieldname: "report_date", label: __("Report Date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "buyer", label: __("Buyer"), fieldtype: "Data" },
		{ fieldname: "season", label: __("Season"), fieldtype: "Data" },
	],

	onload(report) {
		const g = __("Print");
		report.page.add_inner_button(__("All 3 Copies"), () => print_sheet(report, ["md", "planning", "merchant"]), g);
		report.page.add_inner_button(__("MD Copy (Remarks 60%)"), () => print_sheet(report, ["md"]), g);
		report.page.add_inner_button(__("Planning Copy (Remarks Blank)"), () => print_sheet(report, ["planning"]), g);
		report.page.add_inner_button(__("Merchant Copy (Remarks 60%)"), () => print_sheet(report, ["merchant"]), g);
	},

	// show only the formatted sheet; the flat datatable stays available for Export
	after_datatable_render(datatable) {
		$(datatable.wrapper).hide();
		setTimeout(() => draw_diagonals(document.querySelector(".ps-sheet")), 150);
	},
};

// label + remarks text opacity for every printed copy
// show:false = remarks left completely blank (planning writes by hand)
const PS_COPIES = {
	md: { label: "MD COPY", opacity: 0.06, show: true },
	planning: { label: "PLANNING COPY", opacity: 1, show: false },
	merchant: { label: "MERCHANT COPY", opacity: 0.06, show: true },
};

// crisp vector diagonal (bottom-left -> top-right) inside every Knitting/Linking cell
function draw_diagonals(root) {
	if (!root) return;
	const NS = "http://www.w3.org/2000/svg";
	root.querySelectorAll(".ps-diag-box").forEach((box) => {
		if (box.querySelector("svg.ps-diag-line")) return;
		const svg = document.createElementNS(NS, "svg");
		svg.setAttribute("class", "ps-diag-line");
		svg.setAttribute("viewBox", "0 0 100 100");
		svg.setAttribute("preserveAspectRatio", "none");
		svg.setAttribute("style", "position:absolute;left:0;top:0;width:100%;height:100%;z-index:1;overflow:visible;");
		const ln = document.createElementNS(NS, "line");
		ln.setAttribute("x1", "0"); ln.setAttribute("y1", "100");
		ln.setAttribute("x2", "100"); ln.setAttribute("y2", "0");
		ln.setAttribute("stroke", box.dataset.line || "#0a0a0a");
		ln.setAttribute("stroke-width", "1");
		ln.setAttribute("vector-effect", "non-scaling-stroke");
		ln.setAttribute("shape-rendering", "geometricPrecision");
		svg.appendChild(ln);
		box.insertBefore(svg, box.firstChild);
	});
}

function print_sheet(report, copies) {
	const html = $(report.page.main).find(".ps-sheet").html();
	if (!html) return frappe.msgprint(__("Run the report first."));

	// build every copy and apply the opacity directly on each remarks element (inline, so print can't drop it)
	const wrap = document.createElement("div");
	wrap.innerHTML = copies
		.map((c) => `<div class="pg"><div class="lbl">${PS_COPIES[c].label}</div>${html}</div>`)
		.join("");
	draw_diagonals(wrap);
	wrap.querySelectorAll(".pg").forEach((pg, i) => {
		const cfg = PS_COPIES[copies[i]];
		pg.querySelectorAll(".ps-remarks").forEach((el) => {
			if (!cfg.show) {
				el.innerHTML = "";          // blank remarks box to write in
			} else {
				el.style.opacity = cfg.opacity;
				el.style.display = "inline-block";
			}
		});
	});

	const w = window.open("", "_blank");
	w.document.write(`<html><head><title>Production Status</title>
	<style>
		@page { size: A4 landscape; margin: 6mm; }
		* { -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }
		body { margin: 0; background: #fff; }
		.pg { page-break-after: always; }
		.pg:last-child { page-break-after: auto; }
		.lbl { text-align: right; font: 800 11px 'Inter','Segoe UI','Helvetica Neue',Arial,sans-serif; letter-spacing: 1.5px; margin-bottom: 4px; color: #0a0a0a; }
		table { page-break-inside: auto; }
		tr { page-break-inside: avoid; }
	</style></head><body>${wrap.innerHTML}</body></html>`);
	w.document.close();
	setTimeout(() => w.print(), 500);
}