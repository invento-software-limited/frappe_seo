import frappe
from frappe_seo.website.seo_engine import (
	_auto_generate_description, 
	_get_settings, 
	_get_description_field,
	_get_image_field,
	_get_canonical_field
)

def before_save(doc, method=None):
	"""
	Auto-populates SEO meta fields before saving.
	Handles title branding, automated descriptions, and social tag synchronization 
	for Web Page, Blog Post, and Builder Page DocTypes.
	"""
	settings = _get_settings()
	if not settings.get("enable_seo_automation", 1):
		return

	# 1. Infer Schema Type if missing
	if settings.get("enable_schema_markup", 1) and not doc.get("seo_schema_type"):
		doc.seo_schema_type = _infer_schema_type(doc)

	# 2. Handle Meta Description
	desc_field = _get_description_field(doc.doctype)
	if settings.get("enable_auto_description", 1) and desc_field:
		current_val = doc.get(desc_field) or ""
		# Only overwrite if empty or looks like junk/placeholder
		is_junk = "builder_assets" in current_val or current_val.startswith("/home") or "/assets/" in current_val
		if not current_val or is_junk:
			auto_desc = _auto_generate_description(doc)
			if auto_desc:
				doc.set(desc_field, auto_desc)

	# 3. Synchronize Social Tags
	# OG Title
	if not doc.get("seo_og_title"):
		doc.seo_og_title = doc.get("meta_title") or doc.get("page_title") or doc.get("title")
	
	# OG Description
	if not doc.get("seo_og_description") and desc_field:
		doc.seo_og_description = doc.get(desc_field)
	
	# Twitter Card
	if not doc.get("seo_twitter_title"):
		doc.seo_twitter_title = doc.get("seo_og_title")
	if not doc.get("seo_twitter_description"):
		doc.seo_twitter_description = doc.get("seo_og_description")

	# 4. Handle Focus Keyphrase suggestion if empty
	if not doc.get("focus_keyphrase") and settings.get("enable_auto_keyphrase", 1):
		doc.focus_keyphrase = _extract_focus_keyphrase(doc)

	# 5. Calculate SEO Score
	doc.seo_score = _calculate_seo_score(doc, desc_field)


def _calculate_seo_score(doc, desc_field):
	"""Calculates a numeric SEO health score (0-100) based on presence and quality of meta tags."""
	score = 0
	
	# 1. Meta Title (25 points)
	title = doc.get("meta_title") or doc.get("page_title") or doc.get("title")
	if title:
		score += 15
		if 40 <= len(str(title)) <= 65: # Ideal length
			score += 10
	
	# 2. Meta Description (25 points)
	if desc_field:
		desc = doc.get(desc_field)
		if desc:
			score += 15
			if 120 <= len(str(desc)) <= 160: # Ideal length
				score += 10
	
	# 3. Focus Keyphrase (30 points)
	keyphrase = doc.get("focus_keyphrase")
	if keyphrase:
		score += 10
		keyphrase = keyphrase.lower()
		# Check if keyphrase is in title
		if title and keyphrase in title.lower():
			score += 10
		# Check if keyphrase is in description
		if desc and keyphrase in str(desc).lower():
			score += 10
			
	# 4. Meta Image (10 points)
	if doc.get("seo_og_image") or doc.get("meta_image"):
		score += 10

	# 5. Schema Type (10 points)
	if doc.get("seo_schema_type"):
		score += 10

	return min(score, 100)


def _infer_schema_type(doc):
	"""Logic to guess the most appropriate Schema.org type based on DocType."""
	if doc.doctype == "Blog Post":
		return "BlogPosting"
	if doc.doctype == "Web Page":
		return "WebPage"
	if doc.doctype == "Builder Page":
		return "WebPage"
	return "WebPage"

def _extract_focus_keyphrase(doc):
	"""Basic logic to suggest a focus keyphrase from the title."""
	title = doc.get("meta_title") or doc.get("page_title") or doc.get("title") or ""
	if title:
		# Clean and take first few words
		words = [w for w in title.split() if len(w) > 3]
		return " ".join(words[:2]).lower()
	return ""
