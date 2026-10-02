frappe.pages['chat-dashboard-'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'শুধু বাংলায় বলুন কি সমস্যা হচ্ছে !',
		single_column: true
	});
}