app_name = "frappe_seo"
app_title = "Frappe SEO"
app_publisher = "Invento Software Limited"
app_description = "Premium all-in-one SEO for Frappe: meta tags, OG/Twitter cards, Schema.org, live analysis, and XML sitemap."
app_email = "hello@invento.com.bd"
app_license = "mit"

# ── Desk JS/CSS ────────────────────────────────────────────────────────────
app_include_js = ["/assets/frappe_seo/js/frappe_seo.js"]

# ── Website Head Injection ─────────────────────────────────────────────────
update_website_context = ["frappe_seo.website.context.inject_seo_context"]

# ── Document Events ────────────────────────────────────────────────────────
doc_events = {
	"Web Page": {
		"before_save": "frappe_seo.doc_events.automation.before_save",
	},
	"Blog Post": {
		"before_save": "frappe_seo.doc_events.automation.before_save",
	},
	"Builder Page": {
		"before_save": "frappe_seo.doc_events.automation.before_save",
	},
}

# ── Scheduled Tasks ────────────────────────────────────────────────────────
scheduler_events = {
	"daily": [
		"frappe_seo.website.sitemap.generate_sitemap",
	],
}

# ── After Install ──────────────────────────────────────────────────────────
after_install = "frappe_seo.setup.install.setup_seo_fields"
