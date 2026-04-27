const FRAPPE_SEO_DOCTYPES = ["Web Page", "Blog Post", "Builder Page"];

const FIELD_MAP = {
	"Web Page": {
		title: "meta_title",
		description: "meta_description",
		route: "route",
		keyphrase: "focus_keyphrase",
		content_fields: ["main_section"]
	},
	"Blog Post": {
		title: "meta_title",
		description: "seo_meta_description",
		route: "route",
		keyphrase: "focus_keyphrase",
		content_fields: ["content"]
	},
	"Builder Page": {
		title: "page_title",
		description: "meta_description",
		route: "route",
		keyphrase: "focus_keyphrase",
		content_fields: ["blocks", "draft_blocks"]
	}
};

const STOP_WORDS = new Set(["a", "an", "the", "and", "or", "but", "is", "if", "then", "else", "at", "by", "from", "for", "in", "out", "over", "to", "with", "this", "that", "it", "of", "on", "my", "your", "are", "be", "was", "were"]);

function getSuggestions(content) {
	const words = content.toLowerCase().replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(w => w.length > 2 && !STOP_WORDS.has(w));
	const ngrams = {};

	for (let i = 0; i < words.length - 1; i++) {
		// 2-word phrases
		const bigram = `${words[i]} ${words[i+1]}`;
		ngrams[bigram] = (ngrams[bigram] || 0) + 1;
		
		// 3-word phrases
		if (i < words.length - 2) {
			const trigram = `${bigram} ${words[i+2]}`;
			ngrams[trigram] = (ngrams[trigram] || 0) + 1;
		}
	}

	return Object.entries(ngrams)
		.filter(([phrase, count]) => count > 1)
		.sort((a, b) => b[1] - a[1])
		.slice(0, 3)
		.map(entry => entry[0]);
}

function runChecks(frm, fields) {
	const checks = [];
	const content = getFullContent(frm, fields);
	const title = frm.doc[fields.title] || frm.doc.page_title || frm.doc.title || "";
	const desc = frm.doc[fields.description] || frm.doc.meta_description || "";
	const keyphrase = (frm.doc[fields.keyphrase] || "").toLowerCase();

	// Suggestions
	const suggestions = getSuggestions(content);

	// 1. Word Count
	const wordCount = content.split(/\s+/).filter(Boolean).length;
	if (wordCount < 300) {
		checks.push({ label: "Text Length", status: "ok", message: `Contains ${wordCount} words. Aim for 300+ for better ranking.` });
	} else {
		checks.push({ label: "Text Length", status: "good", message: `Excellent! ${wordCount} words. ✓` });
	}

	// 2. Meta Description
	if (!desc) {
		checks.push({ label: "Meta Description", status: "bad", message: "Missing meta description." });
	} else if (desc.length < 120 || desc.length > 160) {
		checks.push({ label: "Meta Description", status: "ok", message: `Length is ${desc.length}. Aim for 120-160 chars.` });
	} else {
		checks.push({ label: "Meta Description", status: "good", message: "Length is perfect. ✓" });
	}

	// 3. Title Length
	if (!title) {
		checks.push({ label: "Meta Title", status: "bad", message: "Missing meta title." });
	} else if (title.length > 60) {
		checks.push({ label: "Meta Title", status: "ok", message: "Title too long (aim for < 60 chars)." });
	} else {
		checks.push({ label: "Meta Title", status: "good", message: "Title length is good. ✓" });
	}

	// 4. Keyphrase Checks
	if (keyphrase) {
		if (title.toLowerCase().includes(keyphrase)) {
			checks.push({ label: "Keyphrase in Title", status: "good", message: "Found in title. ✓" });
		} else {
			checks.push({ label: "Keyphrase in Title", status: "bad", message: "Not found in title." });
		}

		if (desc.toLowerCase().includes(keyphrase)) {
			checks.push({ label: "Keyphrase in Description", status: "good", message: "Found in description. ✓" });
		} else {
			checks.push({ label: "Keyphrase in Description", status: "ok", message: "Consider adding it to description." });
		}

		const count = (content.toLowerCase().match(new RegExp(keyphrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi")) || []).length;
		const density = ((count / (wordCount || 1)) * 100).toFixed(1);
		if (count === 0) {
			checks.push({ label: "Keyphrase Density", status: "bad", message: "Not found in content." });
		} else {
			checks.push({ label: "Keyphrase Density", status: "good", message: `${density}% density (${count} times). ✓` });
		}
	}

	return { checks, suggestions };
}

function getFullContent(frm, fields) {
	let raw = "";
	fields.content_fields.forEach(f => {
		let val = frm.doc[f] || "";
		if (f.includes("blocks")) {
			try {
				const blocks = typeof val === 'string' ? JSON.parse(val || "[]") : val;
				const extract = (list) => {
					let t = "";
					(Array.isArray(list) ? list : [list]).forEach(b => {
						t += (b.innerHTML || "") + " ";
						if (b.children) t += extract(b.children);
					});
					return t;
				};
				val = extract(blocks);
			} catch (e) { val = ""; }
		}
		raw += val + " ";
	});
	return stripHtml(raw);
}

function calcScore(checks) {
	if (!checks.length) return 0;
	const points = checks.reduce((acc, c) => acc + (c.status === "good" ? 10 : c.status === "ok" ? 5 : 0), 0);
	return Math.round((points / (checks.length * 10)) * 100);
}

function renderPanel(frm, doctype) {
	const fields = FIELD_MAP[doctype];
	if (!fields || !frm.fields_dict.seo_score_html) return;

	const { checks, suggestions } = runChecks(frm, fields);
	const score = calcScore(checks);
	const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
	const label = score >= 70 ? "Good" : score >= 40 ? "Needs Work" : "Poor";

	const previewTitle = (frm.doc[fields.title] || frm.doc.page_title || frm.doc.title || frm.doc.name || "Untitled").slice(0, 60);
	const previewDesc = (frm.doc[fields.description] || frm.doc.meta_description || "No description set.").slice(0, 160);
	const previewRoute = frm.doc[fields.route] || frm.doc.name || "";

	let html = `
<div class="frappe-seo-panel" style="font-family: -apple-system, sans-serif;">
	<div style="display:flex; align-items:center; gap:12px; margin-bottom:16px; padding:14px; background:#f8fafc; border-radius:10px; border:1px solid #e2e8f0;">
		<div style="position:relative; width:50px; height:50px;">
			<svg viewBox="0 0 36 36" style="width:50px;height:50px;transform:rotate(-90deg)">
				<circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" stroke-width="3"/>
				<circle cx="18" cy="18" r="15.9" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="${score} ${100 - score}" />
			</svg>
			<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-weight:700;color:${color}">${score}</div>
		</div>
		<div>
			<div style="font-size:14px; font-weight:700;">SEO Score: <span style="color:${color}">${label}</span></div>
			<div style="font-size:12px; color:#64748b;">${checks.filter(c => c.status === "good").length}/${checks.length} checks passed</div>
		</div>
	</div>

	<div style="margin-bottom:16px; padding:14px; background:#fff; border:1px solid #e2e8f0; border-radius:10px;">
		<div style="font-size:11px; font-weight:600; color:#94a3b8; margin-bottom:8px; text-transform:uppercase;">Google Preview</div>
		<div style="font-size:13px; color:#1a0dab; margin-bottom:4px; text-decoration:none; display:block; font-weight:500;">🌐 yourdomain.com › ${previewRoute}</div>
		<div style="font-size:18px; color:#1a0dab; margin-bottom:4px; text-decoration:underline; line-height:1.2;">${previewTitle}</div>
		<div style="font-size:14px; color:#4d5156; line-height:1.4;">${previewDesc}</div>
	</div>

	<div style="margin-bottom:16px; font-size:11px; font-weight:600; text-transform:uppercase; color:#94a3b8;">Analysis</div>
	<div style="display:flex; flex-direction:column; gap:6px; margin-bottom:16px;">
		${checks.map(c => `
		<div style="display:flex; align-items:center; gap:10px; padding:8px 12px; background:#fff; border:1px solid #e2e8f0; border-radius:8px;">
			<span style="width:8px; height:8px; border-radius:50%; background:${c.status === "good" ? "#22c55e" : c.status === "ok" ? "#f59e0b" : "#ef4444"};"></span>
			<div style="font-size:12px; font-weight:500;">${c.label}: <span style="font-weight:400; color:#64748b;">${c.message}</span></div>
		</div>`).join("")}
	</div>`;

	if (suggestions.length > 0) {
		html += `
		<div style="margin-bottom:8px; font-size:11px; font-weight:600; text-transform:uppercase; color:#94a3b8;">Suggested Keyphrases</div>
		<div style="display:flex; flex-wrap:wrap; gap:6px;">
			${suggestions.map(s => `
				<span class="seo-suggestion" style="cursor:pointer; padding:4px 10px; background:#eff6ff; color:#2563eb; border:1px solid #dbeafe; border-radius:14px; font-size:11px; font-weight:500;" onclick="cur_frm.set_value('focus_keyphrase', '${s}')">
					+ ${s}
				</span>
			`).join("")}
		</div>`;
	}

	html += `</div>`;

	frm.set_df_property("seo_score_html", "options", html);
}

function stripHtml(h) {
	return (h || "").replace(/<(script|style).*?>.*?<\/\1>/gi, " ").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function registerHooks(dt) {
	const fields = FIELD_MAP[dt];
	const refresh = (frm) => {
		if (frm._seo_to) clearTimeout(frm._seo_to);
		frm._seo_to = setTimeout(() => renderPanel(frm, dt), 300);
	};

	const hooks = { refresh };
	[fields.title, fields.description, fields.keyphrase, ...fields.content_fields, "page_title", "title", "meta_description"].forEach(f => {
		if (f) hooks[f] = refresh;
	});
	frappe.ui.form.on(dt, hooks);
}

FRAPPE_SEO_DOCTYPES.forEach(registerHooks);
