# User Guide

## Installation

Install the app using the Frappe Bench CLI:

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Get the app
bench get-app https://github.com/invento-software-limited/frappe_seo

# Install on your site
bench --site your-site.com install-app frappe_seo
```

### Prerequisites

- Frappe Bench v16+
- Python 3.14+

---

## Setup Wizard

After installation, navigate to **SEO Optimizer** in your Frappe Desk. A 2-minute setup wizard will guide you through:

1. **Site Name Configuration** — Set your brand name and title separator
2. **Auto-Branding** — Enable/disable automatic site name appending
3. **Social Profiles** — Add your social media URLs for Schema.org markup
4. **Sitemap Settings** — Configure sitemap generation frequency

---

## Configuration

### SEO Settings

Go to **SEO Settings** from the ERPNext Awesome Bar to configure:

| Setting | Description |
|---|---|
| **Site Name** | Your brand name appended to page titles |
| **Title Separator** | Character between page title and site name (`\|`, `-`, etc.) |
| **Auto Branding** | Automatically append site name to all page titles |
| **Auto Description** | Automatically generate meta descriptions from content |
| **Default OG Image** | Fallback Open Graph image for social sharing |
| **Twitter Handle** | Your Twitter username for Twitter Cards |
| **Facebook App ID** | For Facebook Insights integration |
| **Enable Sitemap** | Toggle automatic XML sitemap generation |

---

## Auto-Meta Tags

When **Auto Description** is enabled, Frappe SEO automatically:

1. Extracts the most meaningful content from your page
2. Generates a concise meta description (120–160 characters)
3. Falls back to page content if no explicit description is set

When **Auto Branding** is enabled, Frappe SEO appends your Site Name using your chosen separator to every page title.

### Per-Page Override

You can override auto-generated meta tags on any Web Page, Blog Post, or Builder Page:

| Field | Description |
|---|---|
| **Meta Title** | Custom page title (overrides auto-branding) |
| **Meta Description** | Custom meta description (overrides auto-generated) |
| **Focus Keyphrase** | Primary keyword for SEO analysis |
| **OG Image** | Page-specific Open Graph image |
| **Robots** | `index`, `noindex`, `nofollow`, or `none` |

---

## Social Cards (Open Graph & Twitter)

Frappe SEO automatically generates Open Graph and Twitter Card markup for every supported content type.

### Open Graph Properties

```html
<meta property="og:title" content="Page Title — Site Name" />
<meta property="og:description" content="Automatically generated or custom description" />
<meta property="og:image" content="https://yoursite.com/page-specific-or-default-og-image.jpg" />
<meta property="og:type" content="article" />
<meta property="og:url" content="https://yoursite.com/page-path" />
```

### Twitter Cards

```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Page Title — Site Name" />
<meta name="twitter:description" content="Page description" />
<meta name="twitter:image" content="https://yoursite.com/og-image.jpg" />
```

---

## Schema.org JSON-LD

Frappe SEO injects structured data markup to help search engines understand your content.

### Automatic Schemas

| Schema Type | Applied To |
|---|---|
| **WebPage** | All web pages |
| **Article** | Blog posts |
| **Organization** | Site-wide (from SEO Settings) |
| **BreadcrumbList** | Navigation structure |

### Example Output

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Page Title",
  "description": "Page description",
  "author": {
    "@type": "Organization",
    "name": "Your Company"
  },
  "datePublished": "2026-07-08",
  "image": "https://yoursite.com/og-image.jpg"
}
```

---

## SEO Health Dashboard

Navigate to **SEO Optimizer** workspace to view your SEO Health Dashboard.

### Dashboard Components

- **Donut Chart** — Visual breakdown of pages by SEO health status
  - **Healthy** (green): Pages scoring 80–100%
  - **Warning** (amber): Pages scoring 50–79%
  - **Critical** (red): Pages scoring 0–49%
- **Quick Actions** — One-click shortcuts to edit pages that need attention
- **System Summary** — Total page count with average SEO health score

### SEO Analysis Criteria

| Criteria | Target |
|---|---|
| Title length | 50–60 characters |
| Meta description length | 120–160 characters |
| Focus keyphrase in title | ✓ |
| Focus keyphrase in description | ✓ |
| Focus keyphrase in content | At least 1–2 times |
| OG image present | ✓ |
| Canonical URL set | ✓ |

---

## XML Sitemaps

Frappe SEO automatically generates and updates your XML sitemap daily via a scheduled task.

### Sitemap Configuration

- **Frequency**: Daily (automatic via Frappe scheduler)
- **Included**: All Web Pages, Blog Posts, and Builder Pages
- **Excluded**: Pages marked with `noindex`

The sitemap is accessible at `/sitemap.xml` on your site.

---

## Troubleshooting

| Issue | Possible Cause | Solution |
|---|---|---|
| Meta tags not appearing | SEO Settings not configured | Run the setup wizard |
| OG image not showing | No default OG image set | Add a default OG image in SEO Settings |
| Sitemap not updating | Scheduler not running | Check Frappe scheduler status |
| SEO score shows 0% | Page content may be empty | Add content to the page |
| Auto-branding not working | Feature disabled | Enable in SEO Settings |
| Twitter card not rendering | Twitter handle not set | Add your Twitter handle in SEO Settings |

---

## FAQ

**Q: Does Frappe SEO work with custom DocTypes?**
A: Currently it supports Web Page, Blog Post, and Builder Page. Custom DocType support is on the roadmap.

**Q: Will this slow down my site?**
A: No. Frappe SEO is lightweight and uses Frappe's built-in hooks — no external API calls or heavy processing on page load.

**Q: Can I disable specific features?**
A: Yes. Each feature (auto-branding, auto-description, social cards, Schema.org, sitemaps) can be toggled independently in SEO Settings.

**Q: Does it support multi-tenant sites?**
A: Yes — each site has its own SEO Settings configuration.

**Q: Is the app free?**
A: Yes, it's open source under the MIT license. Premium features (keyword research, bulk audits, content gap analysis) are planned.

---

## API Reference

Frappe SEO provides the following hooks for developers:

### Website Context

```python
# In your custom app's hooks.py
update_website_context = ["frappe_seo.website.context.inject_seo_context"]
```

### Document Events

```python
# Automatically processes SEO on save
doc_events = {
    "Web Page": {
        "before_save": "frappe_seo.doc_events.automation.before_save",
    },
}
```

### Scheduled Tasks

```python
# Daily sitemap generation
scheduler_events = {
    "daily": [
        "frappe_seo.website.sitemap.generate_sitemap",
    ],
}
```

---

## Support

For issues, feature requests, or professional support:

- 📧 **Email:** [hello@invento.com.bd](mailto:hello@invento.com.bd)
- 🐞 **GitHub Issues:** [Submit an issue](https://github.com/invento-software-limited/frappe_seo/issues)
- 🌟 **Contribute:** Star the repo and submit pull requests
