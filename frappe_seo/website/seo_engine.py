import html
import json
import os
import re

import frappe
from frappe import _
from frappe.utils import get_url, strip_html_tags
from frappe.utils.caching import site_cache


def get_seo_context(context, doc):
	"""Enriches the website context with premium SEO data and intelligent fallback logic."""
	settings = _get_settings()
	tags = frappe._dict(context.get("metatags") or {})

	item = context.get("item")
	is_dynamic = getattr(doc, "dynamic_route", 0)

	custom_overrides = {}
	if doc.get("meta_tags"):
		try:
			custom_overrides = json.loads(doc.meta_tags)
		except Exception:
			pass

	title_val = (
		custom_overrides.get("title")
		or (item.get("meta_title") or item.get("seo_title") or item.get("item_name") if item else None)
		or (tags.get("title") if (is_dynamic or item) else None)
		or getattr(doc, "meta_title", None)
		or getattr(doc, "seo_title", None)
		or getattr(doc, "page_title", None)
		or getattr(doc, "item_name", None)
		or getattr(doc, "title", "")
		or context.get("title")
		or context.get("name")
	)
	title_val = strip_html_tags(str(title_val)).strip()

	separator = getattr(settings, "title_separator", "|") or "|"
	site_name = getattr(settings, "site_name", "") or ""

	if site_name and title_val and site_name not in title_val:
		title_val = f"{title_val} {separator} {site_name}"

	tags.title = title_val
	context.seo_title = title_val

	item_desc = None
	if item:
		item_desc = item.get("meta_description") or (
			strip_html_tags(str(item.get("description") or "")).strip()[:160]
			if item.get("description")
			else None
		)

	desc_val = (
		custom_overrides.get("description")
		or item_desc
		or (tags.get("description") if (is_dynamic or item) else None)
		or getattr(doc, _get_description_field(doc.doctype), None)
		or (
			strip_html_tags(str(getattr(doc, "description", "") or "")).strip()[:160]
			if getattr(doc, "description", None)
			else None
		)
		or context.get("description")
		or _auto_generate_description(doc)
		or getattr(settings, "site_description", "")
	)
	if desc_val:
		desc_val = strip_html_tags(str(desc_val)).strip()[:160]

	tags.description = desc_val
	context.meta_description = desc_val

	item_image = None
	if item:
		item_image = (
			item.get("meta_image")
			or item.get("seo_og_image")
			or item.get("item_image")
			or item.get("image")
		)

	image_val = (
		custom_overrides.get("og:image")
		or custom_overrides.get("image")
		or item_image
		or (tags.get("image") if (is_dynamic or item) else None)
		or getattr(doc, _get_image_field(doc.doctype), None)
		or getattr(doc, "image", None)
		or context.get("image")
		or getattr(settings, "default_og_image", None)
	)
	if image_val:
		image_val = get_url(image_val)

	tags.image = image_val
	context.og_image = image_val

	base_url = (getattr(settings, "canonical_url", "") or get_url()).rstrip("/")
	route = (
		getattr(doc, "custom_route", None)
		or (item.get("custom_route") if item else None)
		or getattr(doc, "route", "")
		or ""
	)
	if route and not route.startswith("/") and not route.startswith("shop/") and (item or doc.doctype == "Item"):
		route = f"shop/{route}"

	canonical = (
		custom_overrides.get("canonical")
		or (item.get("seo_canonical_url") if item else None)
		or getattr(doc, _get_canonical_field(doc.doctype), None)
		or (f"{base_url}/{route.lstrip('/')}" if base_url and route else "")
		or context.get("canonical_url")
	)
	tags.canonical = canonical
	context.seo_canonical_url = canonical

	is_item_page = bool(item or doc.doctype == "Item")
	tags["og:type"] = custom_overrides.get("og:type") or tags.get("og:type") or (
		"article" if doc.doctype == "Blog Post" else ("product" if is_item_page else "website")
	)
	tags["og:title"] = (
		custom_overrides.get("og:title")
		or (item.get("seo_og_title") if item else None)
		or getattr(doc, "seo_og_title", None)
		or tags.title
	)
	tags["og:description"] = (
		custom_overrides.get("og:description")
		or (item.get("seo_og_description") if item else None)
		or getattr(doc, "seo_og_description", None)
		or tags.description
	)
	tags["og:image"] = (
		(get_url(item.get("seo_og_image")) if item and item.get("seo_og_image") else None)
		or (get_url(getattr(doc, "seo_og_image")) if getattr(doc, "seo_og_image", None) else None)
		or tags.image
	)
	tags["og:url"] = tags.canonical

	tags["twitter:card"] = "summary_large_image" if tags.image else "summary"
	tags["twitter:title"] = (
		custom_overrides.get("twitter:title")
		or (item.get("seo_twitter_title") if item else None)
		or getattr(doc, "seo_twitter_title", None)
		or tags.title
	)
	tags["twitter:description"] = (
		custom_overrides.get("twitter:description")
		or (item.get("seo_twitter_description") if item else None)
		or getattr(doc, "seo_twitter_description", None)
		or tags.description
	)
	tags["twitter:image"] = tags.image

	noindex = (
		(item.get("seo_noindex") if item else 0)
		or getattr(doc, "seo_noindex", 0)
	)
	nofollow = (
		(item.get("seo_nofollow") if item else 0)
		or getattr(doc, "seo_nofollow", 0)
	)
	if noindex or nofollow:
		robots = []
		if noindex:
			robots.append("noindex")
		if nofollow:
			robots.append("nofollow")
		tags.robots = ", ".join(robots)
	else:
		tags.robots = "index, follow"
	context.seo_robots = tags.robots

	_apply_website_route_meta(tags, route)

	if getattr(settings, "enable_schema_markup", False):
		context.seo_schema_json = _build_schema_graph(doc, settings, context)

	context.google_search_console_id = getattr(settings, "google_search_console_id", "")
	context.bing_webmaster_id = getattr(settings, "bing_webmaster_id", "")
	context.yandex_verification_id = getattr(settings, "yandex_verification_id", "")
	context.baidu_verification_id = getattr(settings, "baidu_site_verification", "")

	context.metatags = tags

	meta_tag_list = []
	for name, val in custom_overrides.items():
		if val:
			tag_type = "property" if ":" in name else "name"
			meta_tag_list.append({"type": tag_type, "name": name, "content": val})
	context.custom_meta_tags = meta_tag_list

	return context


def _get_settings():
	try:
		return frappe.get_single("SEO Settings")
	except Exception:
		return frappe._dict()


def _apply_website_route_meta(tags, route):
	if not route:
		route = frappe.get_website_settings("home_page")

	if route and not route.endswith((".js", ".css")):
		if has_meta_tags(route):
			website_route_meta = frappe.get_doc("Website Route Meta", route)
			for meta_tag in website_route_meta.meta_tags:
				d = meta_tag.get_meta_dict()
				tags.update(d)


@site_cache(ttl=10 * 60, maxsize=16)
def has_meta_tags(route):
	return bool(frappe.db.exists("Website Route Meta", route))


def _auto_generate_description(doc):
	settings = _get_settings()
	if not getattr(settings, "enable_auto_description", False):
		return ""

	content = ""
	for field in ("content", "main_section", "intro", "main_section_md", "main_section_html"):
		val = getattr(doc, field, None)
		if val:
			content = val
			break

	if not content and doc.doctype == "Builder Page":
		blocks_json = doc.get("blocks") or doc.get("draft_blocks") or "[]"
		try:
			blocks = json.loads(blocks_json)

			def extract_text_from_blocks(block_list):
				texts = []
				if not isinstance(block_list, list):
					block_list = [block_list]
				for b in block_list:
					block_name = (b.get("blockName") or "").lower()
					element = (b.get("element") or "").lower()
					if any(
						x in block_name
						for x in ["navbar", "footer", "nav", "menu", "sidebar", "link", "social"]
					):
						continue
					if element in ["nav", "header", "footer", "img", "svg", "button", "script", "style"]:
						continue

					val = b.get("innerHTML")
					if val and isinstance(val, str) and len(val.strip()) > 5:
						clean_val = strip_html_tags(val).strip()
						if clean_val and not clean_val.startswith("/") and not clean_val.startswith("{"):
							texts.append(clean_val)

					if b.get("children"):
						texts.extend(extract_text_from_blocks(b.get("children")))
				return texts

			all_texts = extract_text_from_blocks(blocks)
			# Prioritize longer, more descriptive blocks first
			all_texts.sort(key=len, reverse=True)
			content = " ".join(all_texts)
		except Exception:
			pass

	if not content:
		return ""
	content = re.sub(
		r"<(script|style|head|footer|nav|header).*?>.*?</\1>", " ", content, flags=re.DOTALL | re.IGNORECASE
	)
	plain = strip_html_tags(content)
	plain = html.unescape(plain)
	plain = re.sub(r"\s+", " ", plain).strip()

	if len(plain) <= 160:
		return plain

	# Try to find the last sentence ending within 160 chars
	truncated = plain[:160]
	match = re.search(r"(.+[.!?])\s", truncated)
	if match:
		return match.group(1)

	# Fallback: find the last space to avoid cutting a word
	match = re.search(r"(.+)\s", truncated)
	if match:
		return match.group(1).strip() + "..."

	return truncated[:157] + "..."


def _get_description_field(doctype):
	if doctype in ("Web Page", "Builder Page", "Item"):
		return "meta_description"
	if doctype == "Blog Post":
		return "seo_meta_description"
	return "meta_description"


def _get_canonical_field(doctype):
	if doctype == "Builder Page":
		return "canonical_url"
	return "seo_canonical_url"


def _get_image_field(doctype):
	if doctype in ("Builder Page", "Item"):
		return "meta_image"
	return "seo_og_image"


def _build_schema_graph(doc, settings, context):
	"""Builds a comprehensive Schema.org Graph including WebPage, Breadcrumbs, Organization, and Product."""
	graph = []
	base_url = get_url().rstrip("/")

	# 1. Organization (Global)
	graph.append(
		{
			"@type": "Organization",
			"@id": f"{base_url}/#organization",
			"name": settings.site_name or frappe.local.site,
			"url": base_url,
			"logo": get_url(settings.default_og_image) if settings.default_og_image else None,
		}
	)

	# 2. WebPage (Current)
	webpage = {
		"@type": "WebPage",
		"@id": context.get("seo_canonical_url", f"{base_url}/{doc.route}"),
		"url": context.get("seo_canonical_url", ""),
		"name": context.get("seo_title", ""),
		"description": context.get("meta_description", ""),
		"isPartOf": {"@id": f"{base_url}/#organization"},
	}
	if context.get("og_image"):
		webpage["primaryImageOfPage"] = {"@type": "ImageObject", "url": context["og_image"]}
	graph.append(webpage)

	# 3. Product (if Item or Item Page)
	item = context.get("item") or (doc if doc.doctype == "Item" else None)
	if item:
		product_schema = {
			"@type": "Product",
			"@id": f"{base_url}/#product-{item.get('name') or item.get('item_code') or 'item'}",
			"name": item.get("meta_title") or item.get("item_name") or context.get("seo_title", ""),
			"description": item.get("meta_description") or context.get("meta_description", ""),
			"url": context.get("seo_canonical_url", ""),
		}
		img = (
			item.get("meta_image")
			or item.get("seo_og_image")
			or item.get("item_image")
			or item.get("image")
			or context.get("og_image")
		)
		if img:
			product_schema["image"] = get_url(img)
		if item.get("brand"):
			product_schema["brand"] = {"@type": "Brand", "name": item.get("brand")}
		if item.get("formatted_price") or item.get("price_list_rate"):
			price_val = item.get("price_list_rate") or item.get("formatted_price")
			if isinstance(price_val, str):
				price_clean = re.sub(r"[^\d.]", "", price_val)
			else:
				price_clean = price_val
			product_schema["offers"] = {
				"@type": "Offer",
				"price": str(price_clean),
				"priceCurrency": getattr(settings, "currency", None) or "GBP",
				"availability": (
					"https://schema.org/InStock"
					if item.get("in_stock", True)
					else "https://schema.org/OutOfStock"
				),
				"url": context.get("seo_canonical_url", ""),
			}
		graph.append(product_schema)

	# 4. Breadcrumbs
	route = getattr(doc, "route", "") or (f"shop/{item.get('custom_route', '').lstrip('/')}" if item and item.get("custom_route") else "")
	if route and ":" not in route:
		parts = route.strip("/").split("/")
		items = []
		path = ""
		for i, part in enumerate(parts):
			path += f"/{part}"
			items.append(
				{
					"@type": "ListItem",
					"position": i + 1,
					"name": part.replace("-", " ").title(),
					"item": f"{base_url}{path}",
				}
			)
		graph.append({"@type": "BreadcrumbList", "itemListElement": items})

	return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)
