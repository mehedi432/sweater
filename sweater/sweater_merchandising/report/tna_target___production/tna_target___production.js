frappe.query_reports["TNA TARGET - PRODUCTION"] = {
  filters: [{
    fieldname: "order_sheet_entry",
    label: "Order Sheet Entry",
    fieldtype: "Link",
    options: "Order Sheet Entry",
    reqd: 1
  }],

  onload(report) {
    report.page.add_inner_button(__("Print Plan"), () => {
      if (!window.__pp_html) return frappe.msgprint(__("Nothing to print"));
      const w = window.open("", "_blank");
      w.document.write("<html><head><title>Production Plan</title></head><body style='margin:0'>" + window.__pp_html + "</body></html>");
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
        if (!html) return;
        window.__pp_html = html;
        $(".pp-view").remove();
        const $v = $('<div class="pp-view" style="background:#fff;padding:18px;overflow-x:auto;border:1px solid #d1d8dd;border-radius:8px;margin-top:10px"><div style="zoom:1.35">' + html + '</div></div>');
        $(".report-wrapper").first().hide().before($v);
      }
    });
  }
};