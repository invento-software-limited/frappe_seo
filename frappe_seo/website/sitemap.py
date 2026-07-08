import xml.etree.ElementTree as ET

import frappe
from frappe.utils import now_datetime

from frappe_seo.website.seo_engine import _get_settings


def generate_sitemap():
	"""
	Generates an XML sitemap of all published pages and writes it to
	sites/<site>/public/sitemap.xml so it's served at /sitemap.xml.
	"""
	settings = _get_settings()
	if not settings.get("enable_sitemap"):
		return

	base_url = (settings.canonical_url or "").rstrip("/")
	if not base_url:
		frappe.log_error(
			"Frappe SEO: No canonical_url set in SEO Settings — cannot generate sitemap.", "SEO Sitemap"
		)
		return

	urls = _collect_urls(base_url)

	# Build XML
	urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

	for entry in urls:
		url_el = ET.SubElement(urlset, "url")
		ET.SubElement(url_el, "loc").text = entry["loc"]
		if entry.get("lastmod"):
			ET.SubElement(url_el, "lastmod").text = str(entry["lastmod"])[:10]
		ET.SubElement(url_el, "changefreq").text = entry.get("changefreq", "weekly")
		ET.SubElement(url_el, "priority").text = str(entry.get("priority", 0.5))

	tree = ET.ElementTree(urlset)
	ET.indent(tree, space="  ")

	site_path = frappe.get_site_path()
	sitemap_path = f"{site_path}/public/sitemap.xml"

	import os

	os.makedirs(f"{site_path}/public", exist_ok=True)

	with open(sitemap_path, "wb") as f:
		tree.write(f, xml_declaration=True, encoding="utf-8")

	frappe.logger().info(f"Frappe SEO: Sitemap generated with {len(urls)} URLs → {sitemap_path}")


def _collect_urls(base_url):
	urls = []

	# ── Web Pages ─────────────────────────────────────────────────────────────
	web_pages = frappe.db.get_all(
		"Web Page",
		filters={"published": 1},
		fields=["route", "modified", "seo_noindex"],
	)
	for page in web_pages:
		if page.get("seo_noindex"):
			continue
		if not page.route:
			continue
		urls.append(
			{
				"loc": f"{base_url}/{page.route.lstrip('/')}",
				"lastmod": page.modified,
				"changefreq": "weekly",
				"priority": 0.8,
			}
		)

	# ── Blog Posts ────────────────────────────────────────────────────────────
	if frappe.db.exists("DocType", "Blog Post"):
		blog_posts = frappe.db.get_all(
			"Blog Post",
			filters={"published": 1},
			fields=["route", "modified", "seo_noindex"],
		)
		for post in blog_posts:
			if post.get("seo_noindex"):
				continue
			if not post.route:
				continue
			urls.append(
				{
					"loc": f"{base_url}/{post.route.lstrip('/')}",
					"lastmod": post.modified,
					"changefreq": "monthly",
					"priority": 0.6,
				}
			)

	# ── Builder Pages ─────────────────────────────────────────────────────────
	if frappe.db.exists("DocType", "Builder Page"):
		builder_pages = frappe.db.get_all(
			"Builder Page",
			filters={"published": 1},
			fields=["route", "modified", "seo_noindex"],
		)
		for page in builder_pages:
			if page.get("seo_noindex"):
				continue
			if not page.route:
				continue
			urls.append(
				{
					"loc": f"{base_url}/{page.route.lstrip('/')}",
					"lastmod": page.modified,
					"changefreq": "weekly",
					"priority": 0.7,
				}
			)

	return urls
