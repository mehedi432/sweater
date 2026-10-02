import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ProductionStatus(Document):
    def validate(self):
        self.set_defaults()
        self.fetch_order_information()
        self.validate_schedules()
        self.calculate_total_order_qty()

    def set_defaults(self):
        if not self.report_date:
            self.report_date = nowdate()

        # Do not force Green after the user selects Red.
        if not self.row_group:
            self.row_group = "Green"

    def fetch_order_information(self):
        if not self.order_sheet_entry:
            return

        order = frappe.db.get_value(
            "Order Sheet Entry",
            self.order_sheet_entry,
            [
                "buyer",
                "season",
                "style_name",
                "gauge"
            ],
            as_dict=True
        )

        if not order:
            frappe.throw(
                _("Order Sheet Entry {0} was not found.").format(
                    frappe.bold(self.order_sheet_entry)
                )
            )

        self.buyer = order.get("buyer") or ""
        self.season = order.get("season") or ""
        self.style_name = order.get("style_name") or ""
        self.gauge = order.get("gauge") or ""

    def validate_schedules(self):
        if not self.schedules:
            frappe.throw(
                _("Add at least one Qty and Ex-Factory Date row.")
            )

        for row_number, row in enumerate(
            self.schedules,
            start=1
        ):
            row.qty = parse_quantity(row.qty)

            if row.qty <= 0:
                frappe.throw(
                    _(
                        "Schedule row {0}: Qty must be greater than zero."
                    ).format(row_number)
                )

            if not row.ex_factory_date:
                frappe.throw(
                    _(
                        "Schedule row {0}: Ex-Factory Date is required."
                    ).format(row_number)
                )

    def calculate_total_order_qty(self):
        self.total_order_qty = sum(
            parse_quantity(row.qty)
            for row in self.schedules
        )


def parse_quantity(value):
    if value in (None, ""):
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return int(flt(value))

    cleaned_value = str(value).strip().replace(",", "")

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        cleaned_value
    )

    if not match:
        return 0

    return int(flt(match.group()))