// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Sample Work Order", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Sample Work Order', {
    fetch_daily_sample_request: function(frm) {
        if (!frm.doc.fetch_daily_sample_request) return;

        frappe.db.get_doc('Daily Sample Request', frm.doc.fetch_daily_sample_request).then(dsr => {
            // Clear child tables first
            frm.clear_table('raw_material');
            frm.clear_table('sample_request_quantity');
            frm.clear_table('available_comments');
            frm.clear_table('job_card_distribution');

            // Copy simple fields
            frm.set_value('buyer', dsr.buyer);
            frm.set_value('style', dsr.style);
            frm.set_value('gauge', dsr.gauge);
            frm.set_value('designer', dsr.designer);
            frm.set_value('sample_type', dsr.sample_type.toUpperCase());
            frm.set_value('urgency_priority', dsr.urgency_priority.toUpperCase());
            frm.set_value('approximate_delivery_date', dsr.approximate_delivery_date);

            // Copy child tables
            dsr.raw_material.forEach(row => {
                const new_row = frm.add_child('raw_material');
                Object.keys(row).forEach(key => {
                    if (key !== 'name') new_row[key] = row[key];
                });
            });

            dsr.sample_request_quantity.forEach(row => {
                const new_row = frm.add_child('sample_request_quantity');
                Object.keys(row).forEach(key => {
                    if (key !== 'name') new_row[key] = row[key];
                });
            });

            dsr.available_comments.forEach(row => {
                const new_row = frm.add_child('available_comments');
                Object.keys(row).forEach(key => {
                    if (key !== 'name') new_row[key] = row[key];
                });
            });

            dsr.job_card_distribution.forEach(row => {
                const new_row = frm.add_child('job_card_distribution');
                Object.keys(row).forEach(key => {
                    if (key !== 'name') new_row[key] = row[key];
                });
            });

            frm.refresh_fields();
        });
    }
});


