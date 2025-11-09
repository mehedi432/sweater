# Copyright (c) 2025, Abdullah Al Mehedi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SampleRequest(Document):
    def before_save(self):
        # Step 1: প্রয়োজনীয় ফিল্ড গুলো পূরণ করা হয়েছে কিনা তা যাচাই করা
        if not self.item_category or not self.customer or not self.style:
            frappe.throw("Item Category, Customer, এবং Style ফিল্ডগুলো পূরণ করুন।")

        # Step 2: Sweater আইটেমের কোড ও নাম জেনারেট করা
        item_code = f"{self.item_category} - {self.customer} - {self.style}".upper()
        item_name = item_code

        # Step 3: একটি ফাংশন ডিফাইন করা যা দেখে একটি নির্দিষ্ট item_code এর Item আগে থেকেই আছে কিনা
        def item_exists(code):
            return frappe.db.exists("Item", {"item_code": code})

        # Step 4: একটি ফাংশন যা নতুন Item তৈরি করে
        def create_item(code, name, group, desc, extra=None):
            if extra is None:
                extra = {}

            # নতুন Item ডক তৈরি করা
            item = frappe.new_doc("Item")
            item.update({
                "item_code": code,
                "item_name": name,
                "item_group": group,
                "description": desc,
                "stock_uom": "Nos",  # ইউনিট অফ মেজারমেন্ট
                "is_stock_item": 1,   # স্টক আইটেম কিনা
                "is_sweater": 1 if group.lower() == "sweater" else 0,  # Sweater হলে চিহ্নিত করা
                "item_category": self.item_category,
                **extra  # অতিরিক্ত তথ্য থাকলে যোগ করা
            })
            item.insert(ignore_permissions=True)  # পারমিশন উপেক্ষা করে Insert
            frappe.msgprint(f"{group} আইটেম তৈরি হয়েছে: {code}")

        # Step 5: যদি sweater আইটেমটি আগে না থাকে, তাহলে তৈরি করা
        if not item_exists(item_code):
            create_item(
                item_code,
                item_name,
                self.item_category,
                f"Item for Customer: {self.customer}",
                extra={"is_sweater": 1}  # Sweater হিসেবে চিহ্নিত করা
            )

        # Step 6: যদি material_requirement টেবিলে তথ্য থাকে, তাহলে yarn আইটেম তৈরি করা
        if self.material_requirement:
            for row in self.material_requirement:
                # যদি "category" Yarn হয় এবং "yarn_composition" ও "yarn_count" থাকে
                if row.category and row.category.lower() == "yarn" and row.yarn_composition and row.yarn_count:
                    # Yarn আইটেমের কোড তৈরি
                    yarn_code = f"YARN - {row.yarn_composition} - {row.yarn_count} - {self.customer} - {self.style}".upper()
                    yarn_name = yarn_code

                    # যদি আইটেম আগে না থাকে, তাহলে তৈরি করা
                    if not item_exists(yarn_code):
                        create_item(
                            yarn_code,
                            yarn_name,
                            "Yarn",
                            f"Yarn Composition: {row.yarn_composition}, Yarn Count: {row.yarn_count}"
                        )
