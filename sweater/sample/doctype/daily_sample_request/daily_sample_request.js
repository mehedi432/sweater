// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt
frappe.ui.form.on("Daily Sample Request", {
    onload: function(frm) {
        fill_merchandiser(frm);
    },
    refresh: function(frm) {
        fill_merchandiser(frm);
    }
});

// Helper function
function fill_merchandiser(frm) {
    if (!frm.doc.merchandiser) {
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Employee",
                filters: { user_id: frappe.session.user },
                fieldname: ["name", "employee_number", "employee_name"]
            },
            callback: function(r) {
                if (r.message) {
                    // Save Employee docname in Link field (required for backend)
                    frm.set_value("merchandiser", r.message.name);

                    // Show card number + name in display field
                    frm.set_value("merchandiser_display", r.message.employee_number + " - " + r.message.employee_name);
                }
            }
        });
    }
}





  

