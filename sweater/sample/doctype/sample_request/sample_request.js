// Copyright (c) 2025, Abdullah Al Mehedi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sample Request', {
    onload: function(frm) {
        // অনুরোধের তারিখ স্বয়ংক্রিয়ভাবে সেট করুন
        frm.set_value("request_date", frappe.datetime.now_datetime());

        // Workstation Details এর জন্য অপশন সেট করুন
        frappe.meta.get_docfield("Workstation Details", "process_name", frm.doc.name).options =
            "Design\nKnitting\nKnitting Manual\nLinking\nMending\nWash\nPrint\nIron\nSewing\nZip / Button\nPrint\nFinishing";

        frappe.meta.get_docfield("Workstation Details", "process_type", frm.doc.name).options =
            "Chart\nSwatch\nPanel\nBody";

        // যদি Child Table খালি থাকে তাহলে ডিফল্ট প্রসেস গুলো বসিয়ে দিন
        const default_process_names = [
            "Design", "Knitting", "Knitting Manual", "Linking", "Mending",
            "Wash", "Print", "Iron", "Sewing", "Zip / Button", "Print", "Finishing"
        ];
        const process_types = ["Chart", "Swatch", "Panel", "Body"]; // সম্ভাব্য টাইপ

        if (!frm.doc.workstation_details || frm.doc.workstation_details.length === 0) {
            default_process_names.forEach(process_name => {
                let child = frm.add_child("workstation_details");
                child.process_name = process_name;

                // এলোমেলোভাবে process_type দিন
                child.process_type = process_types[Math.floor(Math.random() * process_types.length)];
            });
            frm.refresh_field("workstation_details");
        }

        // এখানে set_requested_by ফাংশনটি কল করা হচ্ছে
        set_requested_by(frm);
    },
});

// এটি Employee ডক্টাইপ থেকে লগইন ইউজার অনুযায়ী requested_by ফিল্ড পূরণ করে
function set_requested_by(frm) {
    if (!frm.doc.requested_by) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Employee",
                filters: { user_id: frappe.session.user },
                fields: ["name", "employee_name"],
                limit_page_length: 1
            },
            callback: function (response) {
                if (response.message && response.message.length > 0) {
                    let employee = response.message[0];
                    frm.set_value("requested_by", employee.name);
                    frm.set_df_property("requested_by", "description", employee.employee_name);
                } else {
                    frappe.msgprint(__('এই ইউজারের জন্য কোন Employee রেকর্ড খুঁজে পাওয়া যায়নি।'));
                }
            }
        });
    }
}
