// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Sample Request", {
    onload: function(frm) {
        frappe.msgprint("Development in Progress..");
        
        
    }
});


frappe.ui.form.on("Daily Sample Request", {
    
    before_save: function(frm) {
        if (!frm.doc.merchandiser) {
            // Get current user
            let user = frappe.session.user;

            // Get Employee linked to this user
            frappe.db.get_value("Employee", {"user_id": user}, ["name", "employee_number", "employee_name"])
                .then(r => {
                    if (r.message) {
                        let emp_no = r.message.employee_number || "";
                        let emp_name = r.message.employee_name || "";
                        let merch_text = `${emp_no} - ${emp_name}`;

                        // Set Merchandiser field
                        // frm.set_value("merchandiser", merch_text);
                        frm.set_value("merchandiser", emp_no);  
                    }
                });
        }
        // ----------- Auto Set Name Pattern -----------
        let buyer = frm.doc.buyer ? frm.doc.buyer.toUpperCase() : "NO-BUYER";
        let style = frm.doc.style ? frm.doc.style.toUpperCase() : "NO-STYLE";
        let gauge = frm.doc.gauge ? frm.doc.gauge.toUpperCase() : "NO-GAUGE";

        // generate a 5-digit random number
        let seq = Math.floor(10000 + Math.random() * 90000);

        frm.doc.name = `${buyer} - ${style} - ${gauge} - ${seq}`;
    }
});   

