import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

NATIVE_FIELDS = {
	"Web Page": {"meta_title", "meta_description", "meta_image", "route", "title", "published"},
	"Blog Post": {"title", "route", "published", "blogger", "blog_category", "content", "meta_title", "meta_description", "meta_image"},
	"Builder Page": {"title", "route", "published", "meta_description", "meta_image", "canonical_url"},
}

def _existing_custom_fields(doctype):
	"""Returns a set of existing custom field names for a specific DocType."""
	return {r[0] for r in frappe.db.get_all("Custom Field", filters={"dt": doctype}, pluck="fieldname")}

def _build_seo_fields(insert_after, meta_description_fieldname=None):
	"""Generates a list of SEO-related custom field definitions organized into sections."""
	fields = [
		{
			"fieldname": "seo_section",
			"fieldtype": "Section Break",
			"label": "SEO",
			"collapsible": 1,
			"insert_after": insert_after,
		},
		{
			"fieldname": "focus_keyphrase",
			"fieldtype": "Data",
			"label": "Focus Keyphrase",
			"description": "The main keyword or phrase this page should rank for",
			"insert_after": "seo_section",
		},
	]

	if meta_description_fieldname:
		fields.append({
			"fieldname": meta_description_fieldname,
			"fieldtype": "Small Text",
			"label": "Meta Description",
			"description": "Ideal: 120–160 characters. Shown in Google search results.",
			"insert_after": "focus_keyphrase",
		})
		prev = meta_description_fieldname
	else:
		prev = "focus_keyphrase"

	fields += [
		{
			"fieldname": "seo_og_title",
			"fieldtype": "Data",
			"label": "OG Title (Facebook / LinkedIn)",
			"description": "Leave blank to use the page title",
			"insert_after": prev,
		},
		{
			"fieldname": "seo_og_description",
			"fieldtype": "Small Text",
			"label": "OG Description",
			"description": "Leave blank to use the meta description",
			"insert_after": "seo_og_title",
		},
		{
			"fieldname": "seo_og_image",
			"fieldtype": "Attach Image",
			"label": "Social Share Image (OG)",
			"description": "Recommended: 1200×630px. Leave blank to use default.",
			"insert_after": "seo_og_description",
		},
		{
			"fieldname": "seo_cb_1",
			"fieldtype": "Column Break",
			"insert_after": "seo_og_image",
		},
		{
			"fieldname": "seo_twitter_title",
			"fieldtype": "Data",
			"label": "Twitter Card Title",
			"description": "Leave blank to use OG title",
			"insert_after": "seo_cb_1",
		},
		{
			"fieldname": "seo_twitter_description",
			"fieldtype": "Small Text",
			"label": "Twitter Card Description",
			"description": "Leave blank to use OG description",
			"insert_after": "seo_twitter_title",
		},
		{
			"fieldname": "seo_schema_type",
			"fieldtype": "Select",
			"label": "Schema.org Type",
			"options": "\nWebPage\nArticle\nBlogPosting\nOrganization\nProduct\nFAQPage\nBreadcrumbList",
			"insert_after": "seo_twitter_description",
		},
		{
			"fieldname": "seo_canonical_url",
			"fieldtype": "Data",
			"label": "Canonical URL Override",
			"description": "Only set if this page has a canonical URL different from the route",
			"insert_after": "seo_schema_type",
		},
		{
			"fieldname": "seo_noindex",
			"fieldtype": "Check",
			"label": "No Index (Hide from Search Engines)",
			"insert_after": "seo_canonical_url",
		},
		{
			"fieldname": "seo_nofollow",
			"fieldtype": "Check",
			"label": "No Follow",
			"insert_after": "seo_noindex",
		},
		{
			"fieldname": "seo_analysis_section",
			"fieldtype": "Section Break",
			"label": "SEO Analysis",
			"collapsible": 1,
			"insert_after": "seo_nofollow",
		},
		{
			"fieldname": "seo_score_html",
			"fieldtype": "HTML",
			"label": "Live SEO Score",
			"insert_after": "seo_analysis_section",
		},
	]
	return fields

def setup_seo_fields():
	"""Ensures all required SEO custom fields are created for supported DocTypes."""
	doctypes_config = {
		"Web Page": {
			"insert_after": "meta_image",
			"meta_description_fieldname": None,
		}
	}

	if frappe.db.exists("DocType", "Blog Post"):
		doctypes_config["Blog Post"] = {
			"insert_after": "meta_image",
			"meta_description_fieldname": None,
		}

	if frappe.db.exists("DocType", "Builder Page"):
		doctypes_config["Builder Page"] = {
			"insert_after": "route",
			"meta_description_fieldname": None,
		}

	fields_to_create = {}

	for doctype, config in doctypes_config.items():
		existing_custom = _existing_custom_fields(doctype)
		native = NATIVE_FIELDS.get(doctype, set())
		skip = existing_custom | native

		raw_fields = _build_seo_fields(
			config["insert_after"],
			config.get("meta_description_fieldname"),
		)

		filtered = [f for f in raw_fields if f["fieldname"] not in skip]
		if filtered:
			fields_to_create[doctype] = filtered

	if fields_to_create:
		create_custom_fields(fields_to_create)
		frappe.db.commit()
