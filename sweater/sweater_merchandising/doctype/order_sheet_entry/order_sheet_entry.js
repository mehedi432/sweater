// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Order Sheet Entry", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Order Sheet Yarn Detail", {
    quantity(frm, cdt, cdn) { calculate_total(frm, cdt, cdn); },
    consumption(frm, cdt, cdn) { calculate_total(frm, cdt, cdn); },
    wastage(frm, cdt, cdn) { calculate_total(frm, cdt, cdn); }
});

function calculate_total(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    let qty = parseFloat(row.quantity) || 0;
    let cons = parseFloat(row.consumption) || 0; // in grams
    let wastage = parseFloat(row.wastage) || 0;

    // Total in grams
    let total_grams = qty * cons * (1 + wastage / 100);

    // Convert to lbs
    row.total_yarn = total_grams / 453.59237;

    frm.refresh_field("order_sheet_yarn_detail"); // refresh child table
}