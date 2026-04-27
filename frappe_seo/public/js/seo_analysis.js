frappe.provide('frappe_seo.analysis');

frappe_seo.analysis.SEOAnalyzer = class {
    constructor(frm) {
        this.frm = frm;
        this.setup_events();
    }

    setup_events() {
        const fields = ['title', 'meta_title', 'meta_description', 'seo_meta_description', 'focus_keyphrase', 'content', 'main_section'];
        fields.forEach(field => {
            if (this.frm.fields_dict[field]) {
                this.frm.fields_dict[field].$wrapper.on('change', () => this.run_analysis());
            }
        });
        this.run_analysis();
    }

    run_analysis() {
        const data = this.get_data();
        const results = this.calculate_score(data);
        this.render_results(results);
    }

    get_data() {
        return {
            title: this.frm.doc.meta_title || this.frm.doc.title || '',
            description: this.frm.doc.meta_description || this.frm.doc.seo_meta_description || '',
            keyword: this.frm.doc.focus_keyphrase || '',
            content: this.frm.doc.content || this.frm.doc.main_section || this.get_builder_content() || ''
        };
    }

    get_builder_content() {
        if (this.frm.doc.doctype !== 'Builder Page') return '';
        try {
            const blocks = JSON.parse(this.frm.doc.blocks || '[]');
            const extractText = (list) => {
                let t = '';
                list.forEach(b => {
                    t += (b.innerHTML || '') + ' ';
                    if (b.children) t += extractText(b.children);
                });
                return t;
            };
            return extractText(blocks);
        } catch (e) { return ''; }
    }

    calculate_score(data) {
        let score = 0;
        let checks = [];
        const kw = data.keyword.toLowerCase();

        // 1. Keyword Presence
        if (kw) {
            const inTitle = data.title.toLowerCase().includes(kw);
            const inDesc = data.description.toLowerCase().includes(kw);
            const inContent = data.content.toLowerCase().includes(kw);

            checks.push({ label: 'Keyphrase in Title', status: inTitle ? 'success' : 'danger' });
            if (inTitle) score += 25;

            checks.push({ label: 'Keyphrase in Description', status: inDesc ? 'success' : 'danger' });
            if (inDesc) score += 25;

            checks.push({ label: 'Keyphrase in Content', status: inContent ? 'success' : 'danger' });
            if (inContent) score += 20;
        } else {
            checks.push({ label: 'Focus Keyphrase missing', status: 'warning' });
        }

        // 2. Length Checks
        const titleLen = data.title.length;
        const titleStatus = (titleLen >= 40 && titleLen <= 60) ? 'success' : (titleLen > 0 ? 'warning' : 'danger');
        checks.push({ label: `Title length (${titleLen} chars)`, status: titleStatus });
        if (titleStatus === 'success') score += 15;

        const descLen = data.description.length;
        const descStatus = (descLen >= 120 && descLen <= 160) ? 'success' : (descLen > 0 ? 'warning' : 'danger');
        checks.push({ label: `Description length (${descLen} chars)`, status: descStatus });
        if (descStatus === 'success') score += 15;

        return { score, checks };
    }

    render_results({ score, checks }) {
        const color = score > 70 ? '#2ecc71' : (score > 40 ? '#f1c40f' : '#e74c3c');
        let html = `
            <div style="padding: 15px; border: 1px solid #d1d8dd; border-radius: 8px; background: #f8fafc;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div style="width: 50px; height: 50px; border-radius: 50%; border: 4px solid ${color}; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2em; color: ${color}; margin-right: 15px;">
                        ${score}%
                    </div>
                    <div>
                        <h4 style="margin: 0; color: #1e293b;">SEO Health Score</h4>
                        <p style="margin: 0; font-size: 0.9em; color: #64748b;">Live analysis based on current content</p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        `;

        checks.forEach(c => {
            const icon = c.status === 'success' ? '✅' : (c.status === 'danger' ? '❌' : '⚠️');
            html += `
                <div style="font-size: 0.85em; display: flex; align-items: center;">
                    <span style="margin-right: 5px;">${icon}</span>
                    <span style="color: #475569;">${c.label}</span>
                </div>
            `;
        });

        html += `</div></div>`;
        this.frm.set_df_property('seo_score_html', 'options', html);
        this.frm.refresh_field('seo_score_html');
    }
};
