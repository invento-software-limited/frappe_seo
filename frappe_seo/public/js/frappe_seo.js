const FRAPPE_SEO_DOCTYPES = ["Web Page", "Blog Post", "Builder Page"];

const FIELD_MAP = {
	"Web Page": {
		title: "meta_title",
		description: "meta_description",
		route: "route",
		keyphrase: "focus_keyphrase"
	},
	"Blog Post": {
		title: "meta_title",
		description: "meta_description",
		route: "route",
		keyphrase: "focus_keyphrase"
	},
	"Builder Page": {
		title: "meta_title",
		description: "meta_description",
		route: "route",
		keyphrase: "focus_keyphrase"
	}
};

// ── Analysis Logic ──────────────────────────────────────────────────────────
function runChecks(frm, fields) {
	const checks = [];
	const content = stripHtml(frm.doc.main_section || frm.doc.content || "");
	const title = frm.doc[fields.title] || "";
	const desc = frm.doc[fields.description] || "";
	const keyphrase = frm.doc[fields.keyphrase] || "";

	// 1. Meta Description Length
	if (!desc) {
		checks.push({ label: "Meta Description", status: "bad", message: "Missing meta description." });
	} else if (desc.length < 120) {
		checks.push({ label: "Meta Description", status: "ok", message: "Too short (aim for 120-160 chars)." });
	} else if (desc.length > 160) {
		checks.push({ label: "Meta Description", status: "ok", message: "Too long (aim for 120-160 chars)." });
	} else {
		checks.push({ label: "Meta Description", status: "good", message: "Length is perfect. ✓" });
	}

	// 2. Title Length
	if (!title) {
		checks.push({ label: "Meta Title", status: "bad", message: "Missing meta title." });
	} else if (title.length > 60) {
		checks.push({ label: "Meta Title", status: "ok", message: "Too long (aim for < 60 chars)." });
	} else {
		checks.push({ label: "Meta Title", status: "good", message: "Title length is good. ✓" });
	}

	// 3. Keyphrase Checks
	if (keyphrase) {
		const keyphraseLower = keyphrase.toLowerCase();
		
		// Keyphrase in Title
		if (title.toLowerCase().includes(keyphraseLower)) {
			checks.push({ label: "Keyphrase in Title", status: "good", message: "Found in title. ✓" });
		} else {
			checks.push({ label: "Keyphrase in Title", status: "bad", message: "Not found in title." });
		}

		// Keyphrase in Description
		if (desc.toLowerCase().includes(keyphraseLower)) {
			checks.push({ label: "Keyphrase in Description", status: "good", message: "Found in description. ✓" });
		} else {
			checks.push({ label: "Keyphrase in Description", status: "ok", message: "Consider adding it to description." });
		}

		// Keyphrase Density
		const count = countOccurrences(content.toLowerCase(), keyphraseLower);
		if (count === 0) {
			checks.push({ label: "Keyphrase Density", status: "bad", message: "Not found in page content." });
		} else {
			checks.push({ label: "Keyphrase Density", status: "good", message: `Found ${count} times. ✓` });
		}

		// Keyphrase in URL
		const route = frm.doc[fields.route] || "";
		const routeHasKeyphrase = route.toLowerCase().includes(keyphrase.replace(/\s+/g, "-"));
		checks.push({
			label: "Keyphrase in URL",
			status: routeHasKeyphrase ? "good" : "ok",
			message: routeHasKeyphrase
				? "Keyphrase found in URL slug. ✓"
				: "Consider including the keyphrase in the URL.",
		});
	}

	return checks;
}

// ── Score Calculation ───────────────────────────────────────────────────────
function calcScore(checks) {
	if (!checks.length) return 0;
	const points = checks.reduce((acc, c) => {
		return acc + (c.status === "good" ? 10 : c.status === "ok" ? 5 : 0);
	}, 0);
	return Math.round((points / (checks.length * 10)) * 100);
}

// ── Render ──────────────────────────────────────────────────────────────────
function renderPanel(frm, doctype) {
	const fields = FIELD_MAP[doctype];
	if (!fields) return;

	const checks = runChecks(frm, fields);
	const score = calcScore(checks);
	const scoreColor = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
	const scoreLabel = score >= 70 ? "Good" : score >= 40 ? "Needs Work" : "Poor";

	// Google SERP Preview
	const title = (frm.doc[fields.title] || "Untitled Page").slice(0, 60);
	const desc = (frm.doc[fields.description] || "No description set.").slice(0, 160);
	const route = frm.doc[fields.route] || frm.doc.name || "";

	const html = `
<div class="frappe-seo-panel" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">

	<!-- Score Header -->
	<div style="display:flex; align-items:center; gap:12px; margin-bottom:16px; padding:14px 16px; background:#f8fafc; border-radius:10px; border:1px solid #e2e8f0;">
		<div style="position:relative; width:56px; height:56px; flex-shrink:0;">
			<svg viewBox="0 0 36 36" style="width:56px;height:56px;transform:rotate(-90deg)">
				<circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" stroke-width="3"/>
				<circle cx="18" cy="18" r="15.9" fill="none" stroke="${scoreColor}" stroke-width="3"
					stroke-dasharray="${score} ${100 - score}" stroke-linecap="round"/>
			</svg>
			<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:13px;font-weight:700;color:${scoreColor}">${score}</div>
		</div>
		<div style="flex-grow:1;">
			<div style="font-size:14px; font-weight:700; color:#1e293b;">SEO Score: <span style="color:${scoreColor}">${scoreLabel}</span></div>
			<div style="font-size:12px; color:#64748b; margin-top:2px;">${checks.length} checks · ${checks.filter(c=>c.status==="good").length} passed</div>
		</div>
	</div>

	<!-- SERP Preview -->
	<div style="margin-bottom:16px; padding:14px 16px; background:#fff; border:1px solid #e2e8f0; border-radius:10px;">
		<div style="font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:#94a3b8; margin-bottom:10px;">Google Preview</div>
		<div style="font-size:12px; color:#4ade80; margin-bottom:2px; word-break:break-all;">🌐 yourdomain.com › ${route}</div>
		<div style="font-size:18px; color:#1a0dab; margin-bottom:4px; line-height:1.3; cursor:pointer; text-decoration:underline dotted;">${title}</div>
		<div style="font-size:14px; color:#4d5156; line-height:1.5;">${desc}</div>
	</div>

	<!-- Check List -->
	<div style="margin-bottom:8px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:#94a3b8;">Analysis</div>
	<div style="display:flex; flex-direction:column; gap:6px;">
		${checks.map(c => `
		<div style="display:flex; align-items:flex-start; gap:10px; padding:10px 12px; background:#fff; border:1px solid #e2e8f0; border-radius:8px;">
			<span style="flex-shrink:0; width:10px; height:10px; border-radius:50%; margin-top:3px; background:${c.status==="good"?"#22c55e":c.status==="ok"?"#f59e0b":"#ef4444"};"></span>
			<div>
				<div style="font-size:12px; font-weight:600; color:#374151;">${c.label}</div>
				<div style="font-size:11px; color:#6b7280; margin-top:2px;">${c.message}</div>
			</div>
		</div>`).join("")}
	</div>
</div>`;

	frm.set_df_property("seo_score_html", "options", html);
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function stripHtml(html) {
	if (!html) return "";
	// Remove script and style tags completely
	let clean = html.replace(/<(script|style|head|footer|nav|header).*?>.*?<\/\1>/gi, " ");
	// Replace block tags with spaces
	clean = clean.replace(/<(p|div|h[1-6]|li|br|tr|section|article).*?>/gi, " ");
	// Strip all other tags
	clean = clean.replace(/<[^>]*>/g, " ");
	// Normalize whitespace
	return clean.replace(/\s+/g, " ").trim();
}

function countOccurrences(text, phrase) {
	if (!phrase) return 0;
	const escaped = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	return (text.match(new RegExp(escaped, "gi")) || []).length;
}

// ── Frappe Hook Registration ─────────────────────────────────────────────────
function registerHooks(doctype) {
	const triggerFields = Object.values(FIELD_MAP[doctype] || {}).filter(Boolean);

	const refresh = function(frm) {
		// Debounce so it doesn't fire on every keystroke
		if (frm._seo_render_timeout) clearTimeout(frm._seo_render_timeout);
		frm._seo_render_timeout = setTimeout(() => renderPanel(frm, doctype), 300);
	};

	const hooks = { refresh };

	triggerFields.forEach(field => {
		hooks[field] = refresh;
	});

	frappe.ui.form.on(doctype, hooks);
}

// Register for all supported DocTypes
FRAPPE_SEO_DOCTYPES.forEach(dt => registerHooks(dt));
