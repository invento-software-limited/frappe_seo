import frappe
from frappe import _

def get_setup_wizard_stages(stages=None):
	"""
	Appends the SEO Configuration stage to the Frappe Setup Wizard.
	"""
	seo_stage = {
		"name": "seo_configuration",
		"title": _("SEO Configuration"),
		"fields": [
			{
				"fieldname": "seo_site_name",
				"label": _("Site Name"),
				"fieldtype": "Data",
				"placeholder": _("e.g. My Awesome Company"),
				"description": _("This will appear in your page titles.")
			},
			{
				"fieldname": "seo_site_description",
				"label": _("Site Description"),
				"fieldtype": "Small Text",
				"description": _("A brief description of your website for search engines.")
			},
			{
				"fieldname": "enable_seo_automation",
				"label": _("Enable SEO Automation"),
				"fieldtype": "Check",
				"default": 1,
				"description": _("Automatically generate meta descriptions and social tags.")
			},
			{
				"fieldname": "enable_schema_markup",
				"label": _("Enable Schema.org Markup"),
				"fieldtype": "Check",
				"default": 1,
				"description": _("Generate structured data (JSON-LD) for better search visibility.")
			},
			{
				"fieldname": "process_existing",
				"label": _("Initialize SEO for existing pages"),
				"fieldtype": "Check",
				"default": 1,
				"description": _("Apply SEO automation to all currently published pages.")
			}
		]
	}
	
	if stages is None:
		return [seo_stage]
	
	stages.append(seo_stage)
	return stages

@frappe.whitelist()
def setup_wizard_complete(args):
	"""
	Processes the SEO configuration data once the Setup Wizard is finished.
	"""
	if isinstance(args, str):
		import json
		args = json.loads(args)

	if not args.get("seo_site_name"):
		return

	settings = frappe.get_doc("SEO Settings")
	settings.site_name = args.get("seo_site_name")
	settings.site_description = args.get("seo_site_description")
	settings.enable_seo_automation = args.get("enable_seo_automation", 1)
	settings.enable_schema_markup = args.get("enable_schema_markup", 1)
	settings.save(ignore_permissions=True)
	
	frappe.db.commit()

	# Trigger background job to initialize SEO on existing pages
	if args.get("process_existing"):
		frappe.enqueue(
			"frappe_seo.setup.wizard.initialize_seo_on_existing_pages",
			now=frappe.flags.in_test,
			enqueue_after_commit=True
		)

def initialize_seo_on_existing_pages():
	"""
	Iterates through all published Web Pages, Blog Posts, and Builder Pages
	to apply initial SEO automation.
	"""
	doctypes_to_process = {
		"Web Page": {"published": 1},
		"Blog Post": {"published": 1},
		"Builder Page": {"published": 1}
	}

	for doctype, filters in doctypes_to_process.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		
		# Fetch all names matching the filter
		names = frappe.get_all(doctype, filters=filters, pluck="name")
		
		for name in names:
			try:
				doc = frappe.get_doc(doctype, name)
				# doc.save() will trigger before_save in automation.py
				doc.save(ignore_permissions=True)
			except Exception:
				frappe.log_error(f"SEO Initialization Failed for {doctype} {name}")
