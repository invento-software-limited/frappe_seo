import frappe
from frappe_seo.website.seo_engine import get_seo_context


def inject_seo_context(context):
	"""
	Called by Frappe's website rendering for EVERY public page.
	Resolves the underlying doc from context and injects SEO variables.
	The actual HTML is rendered via our override of templates/includes/meta_block.html
	"""
	doc = context.get("doc")
	if not doc:
		doc = frappe._dict(context)

	get_seo_context(context, doc)
