# Copyright (c) 2025, Abdullah Al Mehedi and contributors
# For license information, please see license.txt

# daily_sample_request.py

import frappe
from frappe.model.document import Document

class DailySampleRequest(Document):
    pass
    # def autoname(self):
    #     buyer = (self.buyer or "NO-BUYER").upper()
    #     style = (self.style or "NO-STYLE").upper()
    #     gauge = (self.gauge or "NO-GAUGE").upper()

    #     # Add random sequence (optional)
    #     seq = frappe.generate_hash(length=5).upper()

    #     self.name = f"{buyer} - {style} - {gauge} - {seq}"



