frappe.provide("frappe.setup");

frappe.setup.on("before_load", function () {
	// Only add the slide if we are in the setup wizard and it hasn't been added yet
	if (frappe.setup.slides.find((s) => s.name === "seo_configuration")) return;

	frappe.setup.add_slide({
		name: "seo_configuration",
		title: __("SEO Configuration"),
		icon: "fa fa-search",
		fields: [
			{
				fieldname: "seo_site_name",
				label: __("Site Name"),
				fieldtype: "Data",
				placeholder: __("e.g. My Awesome Company"),
				description: __(
					"This will appear at the end of your page titles (e.g., Home | My Awesome Company)."
				),
				reqd: 1,
			},
			{
				fieldname: "seo_site_description",
				label: __("Site Description"),
				fieldtype: "Small Text",
				placeholder: __("What is your website about?"),
				description: __("A general description of your site for search engines."),
			},
			{
				fieldname: "enable_seo_automation",
				label: __("Enable SEO Automation"),
				fieldtype: "Check",
				default: 1,
				description: __(
					"Automatically generate meta descriptions and social tags for new pages."
				),
			},
			{
				fieldname: "enable_schema_markup",
				label: __("Enable Schema.org Markup"),
				fieldtype: "Check",
				default: 1,
				description: __(
					"Add JSON-LD structured data to help search engines understand your content."
				),
			},
		],
		onload: function (slide) {
			// Pre-fill with existing site name if possible
			if (frappe.boot.sysdefaults.site_name) {
				slide.get_field("seo_site_name").set_input(frappe.boot.sysdefaults.site_name);
			}
		},
	});
});
