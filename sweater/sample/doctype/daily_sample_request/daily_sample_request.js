// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt
// frappe.ui.form.on("Daily Sample Request", {
    
// });
// frappe.ui.form.on("Daily Sample Request", {
//     refresh(frm) {
//         if (!frm.is_new()) {
//             frm.add_custom_button("Create Sample Work Order", () => {
//                 // Redirect user to a new Sample Work Order form
//                 frappe.new_doc("Sample Work Order", {
//                     fetch_daily_sample_request: frm.doc.name  // fieldname of your link field
//                 });
//             }, __("Create"));
//         }
//     }
// });

frappe.ui.form.on("Daily Sample Request", {
    refresh(frm) {
        if (!frm.is_new()) {

            // 🔹 1. Create Sample Work Order Button
            frm.add_custom_button(
                __("Sample Work Order"),
                function () {
                    frappe.new_doc("Sample Work Order", {
                        fetch_daily_sample_request: frm.doc.name
                    });
                },
                __("Create")
            );

            // 🔹 2. Create Cost Sheet Button
            frm.add_custom_button(
                __("Cost Sheet"),
                function () {
                    frappe.new_doc("Cost Sheet", {
                        daily_sample_request: frm.doc.name
                    });
                },
                __("Create")
            );

            // 🔹 3. (Optional) Create Style Development Sheet
            frm.add_custom_button(
                __("Style Development Sheet"),
                function () {
                    frappe.new_doc("Style Development Sheet", {
                        sample_request: frm.doc.name
                    });
                },
                __("Create")
            );
        }
    }
});
