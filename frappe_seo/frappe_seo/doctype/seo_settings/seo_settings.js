frappe.ui.form.on("SEO Settings", {
	refresh: function (frm) {
		frm.add_custom_button(__("Run Setup Wizard"), function () {
			let d = new frappe.ui.Dialog({
				title: __("SEO Setup Wizard"),
				fields: [
					{
						fieldname: "seo_site_name",
						label: __("Site Name"),
						fieldtype: "Data",
						default: frm.doc.site_name || frappe.boot.sysdefaults.site_name,
						reqd: 1,
					},
					{
						fieldname: "seo_site_description",
						label: __("Site Description"),
						fieldtype: "Small Text",
						default: frm.doc.site_description,
					},
					{
						fieldname: "enable_seo_automation",
						label: __("Enable SEO Automation"),
						fieldtype: "Check",
						default: frm.doc.enable_seo_automation,
					},
					{
						fieldname: "enable_schema_markup",
						label: __("Enable Schema.org Markup"),
						fieldtype: "Check",
						default: frm.doc.enable_schema_markup,
					},
					{
						fieldtype: "Section Break",
						label: __("Existing Pages"),
					},
					{
						fieldname: "process_existing",
						label: __("Initialize SEO for all existing published pages"),
						fieldtype: "Check",
						default: 1,
						description: __(
							"This will run a background job to update Web Pages, Blog Posts, and Builder Pages."
						),
					},
				],
				primary_action_label: __("Complete Setup"),
				primary_action(values) {
					frappe.call({
						method: "frappe_seo.setup.wizard.setup_wizard_complete",
						args: {
							args: values,
						},
						callback: function (r) {
							d.hide();
							frappe.show_alert({
								message: __("SEO Setup Complete! Background job started."),
								indicator: "green",
							});
							frm.reload_doc();
						},
					});
				},
			});
			d.show();
		}).addClass("btn-primary");
	},
});
