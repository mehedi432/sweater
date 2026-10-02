frappe.listview_settings["Production Status"] = {
    add_fields: [
        "style_name",
        "buyer",
        "season",
        "gauge",
        "time",
        "total_order_qty",
        "report_date",
        "row_group"
    ],

    hide_name_column: true,

    get_indicator(doc) {
        const color_map = {
            Green: "green",
            Red: "red",
            None: "grey"
        };

        const group = doc.row_group || "None";

        return [
            __(group),
            color_map[group] || "grey",
            "row_group,=," + group
        ];
    },

    formatters: {
        style_name(value) {
            return value
                ? `${frappe.utils.escape_html(
                      value
                  )}`
                : "";
        },

        gauge(value) {
            return value
                ? `
                    <span style="
                        display:inline-block;
                        min-width:44px;
                        padding:3px 7px;
                        text-align:center;
                        border:1px solid var(--border-color);
                        border-radius:6px;
                        font-weight:700;
                    ">
                        ${frappe.utils.escape_html(value)}
                    </span>
                `
                : "";
        },

        total_order_qty(value) {
            return `
                <strong style="
                    font-variant-numeric:tabular-nums;
                ">
                    ${format_number(
                        parseInt(value || 0, 10)
                    )}
                </strong>
            `;
        }
    },
};