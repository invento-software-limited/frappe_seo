import frappe
from frappe_seo.setup.install import setup_seo_fields


def execute():
	"""Create SEO custom fields on Item if Item DocType exists."""
	if frappe.db.exists("DocType", "Item"):
		setup_seo_fields()

