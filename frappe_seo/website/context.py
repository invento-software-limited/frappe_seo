import frappe
from frappe_seo.website.seo_engine import get_seo_context


def inject_seo_context(context):
	"""
	Called by Frappe's website rendering for EVERY public page.
	Resolves the underlying doc from context and injects SEO fields.
	"""
	doc = context.get("doc")
	if not doc:
		# Fallback for pages not backed by a DocType (e.g. www/ pages)
		doc = frappe._dict(context)

	get_seo_context(context, doc)

	# Render our premium SEO template	
	seo_html = frappe.get_template("frappe_seo/templates/includes/seo_meta_tags.html").render(context)
	
	# Inject our tags into head_html
	context.head_html = (context.head_html or "") + "\n" + seo_html


