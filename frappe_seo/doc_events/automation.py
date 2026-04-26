import frappe
from frappe_seo.website.seo_engine import (
	_auto_generate_description, 
	_get_settings, 
	_infer_schema_type, 
	_extract_focus_keyphrase,
	_get_description_field,
	_get_image_field,
	_get_canonical_field
)


def before_save(doc, method=None):
	"""
	Auto-populate meta fields before saving if they're empty or contain junk.
	Works for Web Page, Blog Post, Builder Page.
	"""
	settings = _get_settings()
	if not settings.get("enable_seo_automation"):
		return

	# 1. Infer Schema Type if empty
	if settings.get("enable_schema_markup") and not doc.get("seo_schema_type"):
		doc.seo_schema_type = _infer_schema_type(doc)

	# 2. Auto-generate meta description if blank (or contains junk)
	desc_field = _get_description_field(doc.doctype)
	if settings.get("enable_auto_description") and desc_field:
		current_val = doc.get(desc_field) or ""
		# Detect technical noise from previous failed attempts
		is_junk = "builder_assets" in current_val or current_val.startswith("/home") or "/assets/" in current_val
		
		if not current_val or is_junk:
			generated_desc = _auto_generate_description(doc)
			if generated_desc:
				doc.set(desc_field, generated_desc[:160])

	# 3. Auto-populate focus keyphrase if empty or junk
	current_kp = doc.get("focus_keyphrase") or ""
	kp_is_junk = "builder_" in current_kp or "/" in current_kp
	if not current_kp or kp_is_junk:
		doc.focus_keyphrase = _extract_focus_keyphrase(doc)

	# 4. Branded Title Logic
	# Check all possible title fields: meta_title, page_title (Builder), or title (Web Page/Blog)
	raw_title = doc.get("meta_title") or doc.get("page_title") or doc.get("title") or ""
	
	if raw_title:
		separator = settings.title_separator or "|"
		site_name = settings.site_name or ""
		
		formatted_title = raw_title
		if site_name and site_name not in raw_title:
			formatted_title = f"{raw_title} {separator} {site_name}"

		# Update Meta Title if blank
		if not doc.get("meta_title"):
			doc.meta_title = formatted_title[:60]
		
		# Update Social Titles if blank
		if not doc.get("seo_og_title"):
			doc.seo_og_title = formatted_title[:95]
			
		if not doc.get("seo_twitter_title"):
			doc.seo_twitter_title = formatted_title[:70]

		# Special handling for Blog Post 'seo_title'
		if doc.doctype == "Blog Post" and not doc.get("seo_title"):
			doc.seo_title = formatted_title[:60]

	# 5. Sync Meta Description & Image to Social tags if blank
	img_field = _get_image_field(doc.doctype)

	# Sync Description to Social
	description_val = doc.get(desc_field) if desc_field else None
	if description_val:
		if not doc.get("seo_og_description"):
			doc.seo_og_description = description_val[:200]
		if not doc.get("seo_twitter_description"):
			doc.seo_twitter_description = description_val[:200]

	# Sync Image to Social
	image_val = doc.get(img_field) if img_field else None
	if image_val:
		if not doc.get("seo_og_image"):
			doc.seo_og_image = image_val
