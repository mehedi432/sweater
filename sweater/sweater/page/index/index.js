frappe.pages['index'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Welcome to meek sweater & fashions ltd',
		single_column: true
	});
}