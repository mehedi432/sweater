frappe.query_reports["Machine Requirement Plan"] = {
  filters: [
    { fieldname: "from_date", label: "Plan From", fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
    { fieldname: "to_date", label: "Shipments Up To", fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), 4) },
    { fieldname: "lead_days", label: "Days Between Knitting End and Shipment", fieldtype: "Int", default: 14, reqd: 1 },
    { fieldname: "machine_minutes", label: "Machine Minutes / Day", fieldtype: "Float", default: 2100, reqd: 1 },
    { fieldname: "efficiency", label: "Efficiency %", fieldtype: "Float", default: 85, reqd: 1 },
    { fieldname: "workers_per_machine", label: "Workers per Machine", fieldtype: "Float", default: 1, reqd: 1 },
    { fieldname: "available_machines", label: "Installed Machines (0 = auto)", fieldtype: "Int", default: 0 },
    { fieldname: "show_missing", label: "Show Orders With Missing Data", fieldtype: "Check", default: 1 }
  ],

  onload(report) {
    report.page.add_inner_button(__("Print Plan"), () => {
      if (!window.__mr_html) return frappe.msgprint(__("Nothing to print"));
      const w = window.open("", "_blank");
      w.document.write("<html><head><title>Machine Requirement Plan</title></head><body style='margin:0'>" + window.__mr_html + "</body></html>");
      w.document.close();
      w.focus();
      setTimeout(() => w.print(), 500);
    });
  },

  after_datatable_render() {
    const report = frappe.query_report;
    frappe.call({
      method: "frappe.desk.query_report.run",
      args: {
        report_name: report.report_name,
        filters: report.get_filter_values(),
        ignore_prepared_report: 1
      },
      callback(r) {
        const html = r.message && r.message.message;
        $(".mr-view").remove();
        if (!html || html.indexOf('class="mr"') === -1) {
          $(".report-wrapper").first().show();
          return;
        }
        window.__mr_html = html;
        const $v = $('<div class="mr-view" style="background:#fff;padding:18px;overflow-x:auto;border:1px solid #d1d8dd;border-radius:8px;margin-top:10px"><div style="zoom:1.35">' + html + '</div></div>');
        $(".report-wrapper").first().hide().before($v);
        $(".report-summary, .chart-wrapper").hide();
      }
    });
  }
};