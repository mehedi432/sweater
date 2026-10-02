frappe.ui.form.on("Production Status", {
    setup(frm) {
        frm.set_query("order_sheet_entry", function () {
            return {
                filters: {
                    docstatus: ["<", 2]
                }
            };
        });

        frm.set_df_property(
            "row_group",
            "options",
            "Green\nRed\nNone"
        );

        frm.set_df_property(
            "row_group",
            "read_only",
            0
        );
    },

    onload(frm) {
        if (!frm.doc.report_date) {
            frm.set_value(
                "report_date",
                frappe.datetime.get_today()
            );
        }

        if (!frm.doc.row_group) {
            frm.set_value("row_group", "Green");
        }
    },

    refresh(frm) {
        frm.set_df_property(
            "row_group",
            "read_only",
            0
        );

        calculate_total_order_qty(frm);
        add_report_group_indicator(frm);

        setTimeout(function () {
            style_production_form(frm);
            initialize_schedule_grid(frm);
        }, 150);
    },

    order_sheet_entry(frm) {
        if (!frm.doc.order_sheet_entry) {
            clear_order_information(frm);
            return;
        }

        fetch_order_information(frm);
    },

    row_group(frm) {
        add_report_group_indicator(frm);
    },

    before_save(frm) {
        calculate_total_order_qty(frm);
    },

    schedules_on_form_rendered(frm) {
        setTimeout(function () {
            initialize_schedule_grid(frm);
        }, 100);
    }
});


frappe.ui.form.on("Production Status Schedule", {
    qty(frm) {
        calculate_total_order_qty(frm);
        refresh_schedule_grid(frm);
    },

    ex_factory_date(frm) {
        refresh_schedule_grid(frm);
    },

    schedules_add(frm) {
        calculate_total_order_qty(frm);
        refresh_schedule_grid(frm);
    },

    schedules_remove(frm) {
        calculate_total_order_qty(frm);
        refresh_schedule_grid(frm);
    }
});


function fetch_order_information(frm) {
    frappe.db.get_value(
        "Order Sheet Entry",
        frm.doc.order_sheet_entry,
        [
            "buyer",
            "season",
            "style_name",
            "gauge"
        ]
    ).then(function (response) {
        const values = response.message || {};

        frm.set_value("buyer", values.buyer || "");
        frm.set_value("season", values.season || "");
        frm.set_value(
            "style_name",
            values.style_name || ""
        );
        frm.set_value("gauge", values.gauge || "");
    });
}


function clear_order_information(frm) {
    frm.set_value("buyer", "");
    frm.set_value("season", "");
    frm.set_value("style_name", "");
    frm.set_value("gauge", "");
}


function calculate_total_order_qty(frm) {
    const schedules = frm.doc.schedules || [];

    const total = schedules.reduce(
        function (sum, row) {
            return sum + flt(row.qty || 0);
        },
        0
    );

    frm.set_value(
        "total_order_qty",
        Math.round(total)
    );
}


function add_report_group_indicator(frm) {
    frm.dashboard.clear_headline();

    const group = frm.doc.row_group || "None";

    const color_map = {
        Green: "green",
        Red: "red",
        None: "grey"
    };

    frm.dashboard.add_indicator(
        __("Report Group: {0}", [group]),
        color_map[group] || "grey"
    );
}


function add_report_buttons(frm) {
    frm.add_custom_button(
        __("Open Production Report"),
        function () {
            frappe.route_options = {
                buyer: frm.doc.buyer || "",
                season: frm.doc.season || "",
                report_date:
                    frm.doc.report_date ||
                    frappe.datetime.get_today()
            };

            frappe.set_route(
                "query-report",
                "PRODUCTION STATUS REPORT"
            );
        },
        __("Report")
    );
}


function initialize_schedule_grid(frm) {
    const field = frm.fields_dict.schedules;

    if (!field || !field.grid) {
        return;
    }

    field.grid.update_docfield_property(
        "qty",
        "columns",
        5
    );

    field.grid.update_docfield_property(
        "ex_factory_date",
        "columns",
        5
    );

    field.grid.update_docfield_property(
        "qty",
        "in_list_view",
        1
    );

    field.grid.update_docfield_property(
        "ex_factory_date",
        "in_list_view",
        1
    );

    frm.refresh_field("schedules");

    setTimeout(function () {
        apply_schedule_grid_design(frm);
    }, 150);
}


function refresh_schedule_grid(frm) {
    frm.refresh_field("schedules");

    setTimeout(function () {
        apply_schedule_grid_design(frm);
    }, 100);
}


function apply_schedule_grid_design(frm) {
    const field = frm.fields_dict.schedules;

    if (!field || !field.grid) {
        return;
    }

    const wrapper = field.grid.wrapper;

    wrapper.css({
        "border": "1px solid #d9e0e8",
        "border-radius": "10px",
        "overflow": "hidden",
        "background": "#ffffff",
        "box-shadow":
            "0 2px 8px rgba(16, 24, 40, 0.05)"
    });

    wrapper.find(".grid-heading-row").css({
        "min-height": "44px",
        "background": "#f4f6f9",
        "border-bottom": "1px solid #d9e0e8",
        "font-weight": "700",
        "color": "#182230"
    });

    wrapper
        .find(".grid-heading-row .grid-static-col")
        .css({
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "min-height": "44px",
            "padding": "8px 10px",
            "font-size": "12px"
        });

    wrapper.find(".grid-row").each(function (
        index
    ) {
        const row = $(this);

        row.css({
            "min-height": "46px",
            "background":
                index % 2 === 0
                    ? "#ffffff"
                    : "#fafbfd",
            "border-bottom":
                "1px solid #edf0f4"
        });

        row.find(".grid-static-col").css({
            "display": "flex",
            "align-items": "center",
            "min-height": "46px",
            "padding": "7px 10px",
            "font-size": "13px"
        });
    });

    wrapper
        .find('[data-fieldname="qty"]')
        .css({
            "justify-content": "flex-end",
            "text-align": "right",
            "font-weight": "650",
            "font-variant-numeric":
                "tabular-nums"
        });

    wrapper
        .find(
            '[data-fieldname="ex_factory_date"]'
        )
        .css({
            "justify-content": "center",
            "text-align": "center",
            "font-weight": "500",
            "font-variant-numeric":
                "tabular-nums"
        });

    wrapper.find(".grid-add-row").css({
        "margin": "10px",
        "min-height": "34px",
        "border-radius": "7px",
        "font-weight": "650"
    });

    wrapper.find(".grid-footer").css({
        "background": "#ffffff",
        "border-top": "1px solid #edf0f4"
    });
}


function style_production_form(frm) {
    const wrapper = frm.page.wrapper;

    wrapper.find(".form-section").css({
        "border": "1px solid var(--border-color)",
        "border-radius": "10px",
        "background": "var(--card-bg)",
        "margin-bottom": "14px",
        "padding": "8px 12px"
    });

    wrapper.find(".section-head").css({
        "font-weight": "700",
        "letter-spacing": "0.15px"
    });

    [
        "yarn_status",
        "pps_status",
        "knitting",
        "linking"
    ].forEach(function (fieldname) {
        wrapper
            .find(
                `[data-fieldname="${fieldname}"] textarea`
            )
            .css({
                "min-height": "88px",
                "line-height": "1.5"
            });
    });

    wrapper
        .find('[data-fieldname="remarks"] textarea')
        .css({
            "min-height": "125px",
            "line-height": "1.5"
        });
}