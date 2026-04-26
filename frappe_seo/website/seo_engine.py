import frappe
import os
import json
import re
import html
from frappe import _
from collections import Counter
from frappe.utils import strip_html_tags

def get_seo_context(context, doc):
	"""
	Core function: enriches the Jinja context with SEO data for any page type.
	Called by get_context hooks for Web Page, Blog Post, and Builder Page.
	"""
	settings = _get_settings()
	route = getattr(doc, "route", "") or ""

	# ── 1. Custom Meta Tags Override ──────────────────────────────────────────
	# Respect manual tags set via the "Set Meta Tags" button
	custom_tags = {}
	if doc.get("meta_tags"):
		try:
			custom_tags = json.loads(doc.meta_tags)
		except:
			pass

	# ── 2. Title Logic ────────────────────────────────────────────────────────
	# Priority: Custom Tag > SEO Title Field > Document Title
	title_val = (
		custom_tags.get("title") 
		or getattr(doc, "meta_title", None) 
		or getattr(doc, "seo_title", None)
		or getattr(doc, "page_title", None)
		or getattr(doc, "title", "")
	)
	
	# Strip HTML just in case
	title_val = strip_html_tags(str(title_val)).strip()
	
	separator = settings.title_separator or "|"
	site_name = settings.site_name or ""
	
	if site_name and title_val and site_name not in title_val:
		title_val = f"{title_val} {separator} {site_name}"

	context.title = title_val
	context.seo_title = title_val

	# ── 3. Meta Description ───────────────────────────────────────────────────
	meta_desc = (
		custom_tags.get("description")
		or getattr(doc, _get_description_field(doc.doctype), None)
		or _auto_generate_description(doc)
		or settings.site_description
	)
	if meta_desc:
		meta_desc = strip_html_tags(str(meta_desc)).strip()[:160]
	
	context.meta_description = meta_desc or ""

	# ── 4. Canonical URL ──────────────────────────────────────────────────────
	base = (settings.canonical_url or "").rstrip("/")
	context.seo_canonical_url = (
		custom_tags.get("canonical")
		or getattr(doc, _get_canonical_field(doc.doctype), None)
		or (f"{base}/{route.lstrip('/')}" if base and route else "")
	)

	# ── 5. Open Graph & Twitter ───────────────────────────────────────────────
	og_title = custom_tags.get("og:title") or getattr(doc, "seo_og_title", None) or title_val
	og_desc = custom_tags.get("og:description") or getattr(doc, "seo_og_description", None) or meta_desc
	
	og_image = (
		custom_tags.get("og:image") 
		or getattr(doc, _get_image_field(doc.doctype), None) 
		or settings.site_image 
		or settings.default_og_image
	)
	
	context.og_title = og_title
	context.og_description = (og_desc or "")[:200]
	context.og_image = og_image
	context.og_type = "website"

	context.twitter_title = custom_tags.get("twitter:title") or getattr(doc, "seo_twitter_title", None) or og_title
	context.twitter_description = custom_tags.get("twitter:description") or getattr(doc, "seo_twitter_description", None) or og_desc
	context.twitter_image = custom_tags.get("twitter:image") or og_image
	context.twitter_card = "summary_large_image"

	# ── 6. Robots ─────────────────────────────────────────────────────────────
	noindex = getattr(doc, "seo_noindex", 0)
	nofollow = getattr(doc, "seo_nofollow", 0)
	robots_parts = []
	if noindex:
		robots_parts.append("noindex")
	if nofollow:
		robots_parts.append("nofollow")
	context.seo_robots = ", ".join(robots_parts) if robots_parts else "index, follow"

	# ── 7. Schema.org ─────────────────────────────────────────────────────────
	if settings.enable_schema_markup:
		context.seo_schema_json = _build_schema(doc, settings, context)
	else:
		context.seo_schema_json = ""

	# ── 8. Webmaster Verifications ────────────────────────────────────────────
	context.google_search_console_id = settings.google_search_console_id or ""
	context.bing_webmaster_id = settings.bing_webmaster_id or ""
	context.yandex_verification_id = settings.yandex_verification_id or ""
	context.baidu_verification_id = settings.baidu_verification_id or ""

	# ── 9. Custom Meta Tags List (for template loop) ──────────────────────────
	meta_tag_list = []
	if doc.get("meta_tags"):
		try:
			tags_data = json.loads(doc.meta_tags)
			for name, val in tags_data.items():
				tag_type = "property" if ":" in name else "name"
				meta_tag_list.append({"type": tag_type, "name": name, "content": val})
		except:
			pass
	context.custom_meta_tags = meta_tag_list

	return context


def _get_settings():
	try:
		return frappe.get_single("SEO Settings")
	except Exception:
		return frappe._dict()


def _auto_generate_description(doc):
	"""Extract a high-quality plain-text description from the page content."""
	if not _get_settings().get("enable_auto_description"):
		return ""

	content = ""
	# Standard fields
	for field in ("content", "main_section", "intro", "main_section_md", "main_section_html"):
		val = getattr(doc, field, None)
		if val:
			content = val
			break
	
	# Builder Page Special Case
	if not content and doc.doctype == "Builder Page":
		blocks_json = doc.get("blocks") or doc.get("draft_blocks") or "[]"
		try:
			blocks = json.loads(blocks_json)
			
			def extract_text_from_blocks(block_list):
				texts = []
				if not isinstance(block_list, list):
					block_list = [block_list]
				
				for b in block_list:
					# Skip navigation and footer noise
					block_name = (b.get("blockName") or "").lower()
					if any(x in block_name for x in ["navbar", "footer", "nav", "menu"]):
						continue

					# Skip technical elements
					if b.get("element") in ["img", "svg", "button"]:
						continue

					# 1. Focus on innerHTML (headings and paragraphs)
					val = b.get("innerHTML")
					if val and isinstance(val, str) and len(val.strip()) > 5:
						clean_val = strip_html_tags(val).strip()
						# Filter technical paths
						if (not clean_val.startswith("/") and 
							not clean_val.startswith("{") and
							"." not in clean_val[:15]):
							texts.append(clean_val)
					
					# 2. Recursively check children
					if b.get("children"):
						texts.extend(extract_text_from_blocks(b.get("children")))
				return texts

			content = " ".join(extract_text_from_blocks(blocks))
		except:
			pass

	if not content:
		return ""

	# Clean HTML
	content = re.sub(r"<(script|style|head|footer|nav|header).*?>.*?</\1>", " ", content, flags=re.DOTALL | re.IGNORECASE)
	content = re.sub(r"<(p|div|h[1-6]|li|br|tr|section|article).*?>", ". ", content, flags=re.IGNORECASE)
	plain = strip_html_tags(content)
	plain = html.unescape(plain)
	plain = re.sub(r"\s+", " ", plain).strip()

	return _summarize_text(plain)


def _summarize_text(text):
	sentences = re.split(r'(?<=[.!?]) +', text)
	if len(sentences) <= 1:
		return text[:157].strip()

	stop_words = {"the", "and", "is", "of", "to", "in", "a", "with", "for", "on", "this", "our", "we", "you", "your", "are", "at"}
	words = re.findall(r'\w+', text.lower())
	words = [w for w in words if w not in stop_words and len(w) > 3]
	
	word_frequencies = Counter(words)
	if not word_frequencies:
		return sentences[0][:157].strip()

	max_freq = max(word_frequencies.values())
	for word in word_frequencies:
		word_frequencies[word] = word_frequencies[word] / max_freq

	sentence_scores = {}
	for sent in sentences:
		if len(sent.split()) < 5 or len(sent.split()) > 40:
			continue
		for word in re.findall(r'\w+', sent.lower()):
			if word in word_frequencies:
				sentence_scores[sent] = sentence_scores.get(sent, 0) + word_frequencies[word]

	if not sentence_scores:
		return sentences[0][:157].strip()

	return max(sentence_scores, key=sentence_scores.get).strip()[:157]


def _extract_focus_keyphrase(doc):
	content = _auto_generate_description(doc)
	if not content: return ""
	
	stop_words = {"the", "and", "is", "of", "to", "in", "a", "with", "for", "on", "this", "our", "we", "you", "your", "are", "at", "from", "that"}
	words = re.findall(r'\w+', content.lower())
	words = [w for w in words if w not in stop_words and len(w) > 4]
	
	if not words: return ""
	common = Counter(words).most_common(2)
	if len(common) >= 2:
		return f"{common[0][0]} {common[1][0]}"
	return common[0][0]


def _get_description_field(doctype):
	if doctype == "Web Page": return "meta_description"
	if doctype == "Blog Post": return "seo_meta_description"
	if doctype == "Builder Page": return "meta_description"
	return "meta_description"

def _get_canonical_field(doctype):
	if doctype == "Builder Page": return "canonical_url"
	return "seo_canonical_url"

def _get_image_field(doctype):
	if doctype == "Builder Page": return "meta_image"
	return "seo_og_image"


def _infer_schema_type(doc):
	if doc.get("seo_schema_type"): return doc.seo_schema_type
	if doc.doctype == "Blog Post": return "BlogPosting"
	return "WebPage"


def _build_schema(doc, settings, context):
	schema_type = _infer_schema_type(doc)
	url = context.get("seo_canonical_url") or ""
	schema = {
		"@context": "https://schema.org",
		"@type": schema_type,
		"name": context.get("seo_title", ""),
		"description": context.get("meta_description", ""),
		"url": url,
	}
	if context.get("og_image"):
		schema["image"] = frappe.utils.get_url(context["og_image"])
	return json.dumps(schema, indent=2)
