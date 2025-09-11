# Copyright (c) 2025, Abdullah Al Mehedi and contributors
# For license information, please see license.txt
# Copyright (c) 2025, Abdullah Al Mehedi

import frappe
from frappe.model.document import Document

class DailySampleRequest(Document):

    def before_save(self):
        """Auto-create Sweater & Raw Material items on save"""

        if not self.buyer or not self.style or not self.gauge:
            frappe.throw("Buyer, Style, এবং Gauge ফিল্ডগুলো পূরণ করুন।")

        # ------------------ Sweater Item ------------------
        sweater_code = f"SWEATER - {self.buyer} - {self.style} - {self.gauge} GG".upper()
        if not frappe.db.exists("Item", {"item_code": sweater_code}):
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": sweater_code,
                "item_name": sweater_code,
                "item_group": "SWEATER",
                "is_stock_item": 1,
                "stock_uom": "Nos",
                "has_variants": 0,
                "disabled": 0,
                "is_sweater": 1,
                "is_sales_item":1
            })
            item.insert(ignore_permissions=True)
            frappe.db.commit()
            frappe.msgprint(f"Sweater Item তৈরি হয়েছে: {sweater_code}")

        self.sweater_item = sweater_code

        # ------------------ Raw Material Items ------------------
        if self.raw_material:
            for idx, row in enumerate(self.raw_material, start=1):
                if not row.category:
                    frappe.throw(f"Row {idx} এর Category খালি।")

                item_code_parts = [row.category.upper()]

                # Use known fields if they exist
                if getattr(row, "yarn_composition", None):
                    item_code_parts.append(row.yarn_composition.upper())
                if getattr(row, "yarn_count", None):
                    item_code_parts.append(row.yarn_count.upper())
                if getattr(row, "item_name", None):
                    item_code_parts.append(row.item_name.upper())
                if getattr(row, "colour", None):
                    item_code_parts.append(row.colour.upper())
                # if getattr(row, "quantity", None) and row.category.lower() != "yarn":
                #     item_code_parts.append(str(row.quantity))

                # Always append Buyer & Style
                item_code_parts.extend([self.buyer.upper(), self.style.upper()])
                item_code = " - ".join(item_code_parts)
                description = f"{row.category} Item for {self.buyer} - {self.style}"

                # Create item if not exists
                if not frappe.db.exists("Item", {"item_code": item_code}):
                    new_item = frappe.get_doc({
                        "doctype": "Item",
                        "item_code": item_code,
                        "item_name": item_code,
                        "item_group": row.category,
                        "description": description,
                        "stock_uom": "Nos",
                        "is_stock_item": 1
                    })
                    new_item.insert(ignore_permissions=True)
                    frappe.db.commit()
                    frappe.msgprint(f"{row.category} Item তৈরি হয়েছে: {item_code}")

                # Link the item code back to the child row
                row.item_name = item_code
