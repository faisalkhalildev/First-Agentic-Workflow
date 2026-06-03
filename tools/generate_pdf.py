"""
Branded PDF Report Generator
=============================
Takes the analysis report data, brand config, and logo to produce
a polished, multi-page branded PDF report.
Uses Jinja2 for HTML templating and xhtml2pdf for PDF conversion.
"""

import json
import os
import sys
import base64
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from xhtml2pdf import pisa

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "workflows" / "config"
TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)


def load_brand_config():
    """Load brand configuration."""
    path = CONFIG_DIR / "brand_config.json"
    if not path.exists():
        print("ERROR: brand_config.json not found.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_analysis():
    """Load the analysis report from Phase 4."""
    path = TMP_DIR / "analysis_report.json"
    if not path.exists():
        print("ERROR: analysis_report.json not found. Run generate_analysis.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_logo_base64():
    """Load logo and convert to base64 for embedding in HTML."""
    logo_path = CONFIG_DIR / "logo.png"
    if not logo_path.exists():
        return None
    with open(logo_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def get_threat_color(level, colors=None):
    """Return color based on threat level."""
    level = (level or "").lower()
    if level == "high":
        return "#E74C3C"
    elif level == "medium":
        return "#F39C12"
    return "#2ECC71"


def get_priority_color(priority):
    """Return color based on action item priority."""
    priority = (priority or "").lower()
    if priority == "high":
        return "#E74C3C"
    elif priority == "medium":
        return "#F39C12"
    return "#2ECC71"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 0;
        @frame content {
            left: 50pt;
            right: 50pt;
            top: 50pt;
            bottom: 60pt;
        }
        @frame footer {
            -pdf-frame-content: page-footer;
            left: 50pt;
            right: 50pt;
            bottom: 20pt;
            height: 30pt;
        }
    }

    body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 10pt;
        color: {{ colors.text_white }};
        background-color: {{ colors.background_dark }};
        line-height: 1.6;
    }

    /* ===== COVER PAGE ===== */
    .cover-page {
        text-align: center;
        padding-top: 120pt;
        page-break-after: always;
    }
    .cover-logo {
        width: 140pt;
        margin-bottom: 40pt;
        background-color: #FFFFFF;
        padding: 10pt;
        border-radius: 8px;
    }
    .cover-title {
        font-size: 26pt;
        font-weight: bold;
        color: {{ colors.primary_gold }};
        margin-bottom: 15pt;
        letter-spacing: 1pt;
    }
    .cover-subtitle {
        font-size: 13pt;
        color: {{ colors.text_muted }};
        margin-bottom: 8pt;
    }
    .cover-date {
        font-size: 11pt;
        color: {{ colors.border_gold }};
        margin-top: 40pt;
    }
    .cover-line {
        width: 200pt;
        height: 2pt;
        background-color: {{ colors.primary_gold }};
        margin: 30pt auto;
    }

    /* ===== HEADERS ===== */
    h1 {
        font-size: 20pt;
        color: {{ colors.primary_gold }};
        border-bottom: 2pt solid {{ colors.primary_gold }};
        padding-bottom: 8pt;
        margin-top: 30pt;
        margin-bottom: 15pt;
        letter-spacing: 0.5pt;
    }
    h2 {
        font-size: 14pt;
        color: {{ colors.primary_gold_light }};
        margin-top: 22pt;
        margin-bottom: 10pt;
    }
    h3 {
        font-size: 12pt;
        color: {{ colors.text_white }};
        margin-top: 16pt;
        margin-bottom: 8pt;
    }

    /* ===== CONTENT ===== */
    p {
        margin-bottom: 8pt;
        text-align: justify;
    }
    .section {
        margin-bottom: 20pt;
    }

    /* ===== PAGE HEADER ===== */
    .page-header {
        text-align: right;
        margin-bottom: 20pt;
    }
    .page-header img {
        width: 50pt;
        background-color: #FFFFFF;
        padding: 4pt;
        border-radius: 4px;
    }

    /* ===== CARDS ===== */
    .card {
        background-color: {{ colors.surface_dark }};
        border: 1pt solid {{ colors.accent_charcoal }};
        border-left: 3pt solid {{ colors.primary_gold }};
        padding: 12pt 15pt;
        margin-bottom: 15pt;
    }
    .card-title {
        font-size: 13pt;
        font-weight: bold;
        color: {{ colors.primary_gold }};
        margin-bottom: 6pt;
    }
    .card-subtitle {
        font-size: 9pt;
        color: {{ colors.text_muted }};
        margin-bottom: 8pt;
    }

    /* ===== TABLES ===== */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12pt 0;
        font-size: 9pt;
    }
    th {
        background-color: {{ colors.accent_charcoal }};
        color: {{ colors.primary_gold }};
        padding: 8pt 10pt;
        text-align: left;
        font-weight: bold;
        border-bottom: 2pt solid {{ colors.primary_gold }};
    }
    td {
        padding: 7pt 10pt;
        border-bottom: 1pt solid {{ colors.accent_charcoal }};
        color: {{ colors.text_light }};
    }
    tr:nth-child(even) td {
        background-color: {{ colors.surface_dark }};
    }

    /* ===== LISTS ===== */
    ul {
        margin-left: 15pt;
        margin-bottom: 10pt;
    }
    li {
        margin-bottom: 4pt;
        color: {{ colors.text_light }};
    }
    .gold-bullet {
        color: {{ colors.primary_gold }};
        font-weight: bold;
    }

    /* ===== BADGES ===== */
    .badge {
        display: inline-block;
        padding: 2pt 8pt;
        font-size: 8pt;
        font-weight: bold;
        color: {{ colors.background_dark }};
        letter-spacing: 0.5pt;
    }
    .badge-high { background-color: #E74C3C; }
    .badge-medium { background-color: #F39C12; }
    .badge-low { background-color: #2ECC71; }

    /* ===== INSIGHT BOXES ===== */
    .insight-box {
        background-color: {{ colors.surface_dark }};
        border: 1pt solid {{ colors.border_gold }};
        padding: 12pt 15pt;
        margin: 10pt 0;
    }
    .insight-box-title {
        color: {{ colors.primary_gold }};
        font-weight: bold;
        font-size: 11pt;
        margin-bottom: 6pt;
    }

    /* ===== FOOTER ===== */
    .footer {
        font-size: 8pt;
        color: {{ colors.text_muted }};
        text-align: center;
        border-top: 1pt solid {{ colors.accent_charcoal }};
        padding-top: 5pt;
    }

    /* ===== DIVIDER ===== */
    .divider {
        height: 1pt;
        background-color: {{ colors.accent_charcoal }};
        margin: 20pt 0;
    }

    .page-break {
        page-break-before: always;
    }
</style>
</head>
<body>

<!-- FOOTER (referenced by @frame) -->
<div id="page-footer">
    <div class="footer">
        {{ company_name }} &bull; Competitive Analysis Report &bull; {{ date }}
    </div>
</div>

<!-- ===== COVER PAGE ===== -->
<div class="cover-page">
    {% if logo_b64 %}
    <img class="cover-logo" src="data:image/png;base64,{{ logo_b64 }}" />
    {% endif %}
    <div class="cover-title">{{ report.report_title }}</div>
    <div class="cover-line"></div>
    <div class="cover-subtitle">Competitive Intelligence Report</div>
    <div class="cover-subtitle">Prepared for {{ company_name }}</div>
    <div class="cover-date">{{ date }}</div>
</div>

<!-- ===== TABLE OF CONTENTS ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>Table of Contents</h1>
<table>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">01</td><td>Executive Summary</td></tr>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">02</td><td>Market Overview</td></tr>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">03</td><td>Competitor Profiles</td></tr>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">04</td><td>Comparison Matrix</td></tr>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">05</td><td>Strategic Insights</td></tr>
    <tr><td style="color: {{ colors.primary_gold }}; font-weight: bold;">06</td><td>Action Items</td></tr>
</table>

<!-- ===== EXECUTIVE SUMMARY ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>01 &mdash; Executive Summary</h1>
<div class="section">
    {% for paragraph in report.executive_summary.split('\n') %}
        {% if paragraph.strip() %}
        <p>{{ paragraph.strip() }}</p>
        {% endif %}
    {% endfor %}
</div>

<!-- ===== MARKET OVERVIEW ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>02 &mdash; Market Overview</h1>
<div class="section">
    {% set landscape = report.get('market_overview', {}).get('landscape_description', '') %}
    {% for paragraph in landscape.split('\n') %}
        {% if paragraph.strip() %}
        <p>{{ paragraph.strip() }}</p>
        {% endif %}
    {% endfor %}
</div>

<h2>Market Trends</h2>
<ul>
{% for trend in report.get('market_overview', {}).get('market_trends', []) %}
    <li><span class="gold-bullet">&bull;</span> {{ trend }}</li>
{% endfor %}
</ul>

{% set market_signals = report.get('market_overview', {}).get('market_size_signals', '') %}
{% if market_signals %}
<div class="insight-box">
    <div class="insight-box-title">Market Size Signals</div>
    <p>{{ market_signals }}</p>
</div>
{% endif %}

<!-- ===== COMPETITOR PROFILES ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>03 &mdash; Competitor Profiles</h1>

{% for comp in report.get('competitor_profiles', []) %}
<div class="card">
    <div class="card-title">{{ comp.get('name', 'Unknown') }}</div>
    <div class="card-subtitle">{{ comp.get('website', '') }} &bull; Threat: 
        <span class="badge badge-{{ comp.get('threat_level', 'low') | lower }}">{{ comp.get('threat_level', 'N/A') | upper }}</span>
    </div>
    <p>{{ comp.get('overview', '') }}</p>
    
    <h3>Products &amp; Services</h3>
    <ul>
    {% for item in comp.get('products_services', []) %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
    
    <table>
        <tr>
            <th>Pricing</th>
            <th>Target Audience</th>
        </tr>
        <tr>
            <td>{{ comp.get('pricing_model', 'Unknown') }}</td>
            <td>{{ comp.get('target_audience', 'N/A') }}</td>
        </tr>
    </table>
    
    <table>
        <tr><th>Strengths</th><th>Weaknesses</th></tr>
        <tr>
            <td>
                <ul>
                {% for s in comp.get('strengths', []) %}
                    <li>{{ s }}</li>
                {% endfor %}
                </ul>
            </td>
            <td>
                <ul>
                {% for w in comp.get('weaknesses', []) %}
                    <li>{{ w }}</li>
                {% endfor %}
                </ul>
            </td>
        </tr>
    </table>
    
    <div class="insight-box">
        <div class="insight-box-title">Key Takeaway</div>
        <p>{{ comp.get('key_takeaway', '') }}</p>
    </div>
</div>

{% if not loop.last and loop.index % 2 == 0 %}
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
{% endif %}
{% endfor %}

<!-- ===== COMPARISON MATRIX ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>04 &mdash; Comparison Matrix</h1>

{% if report.get('comparison_matrix') and report.comparison_matrix.get('categories') %}
<table>
    <tr>
        <th>Competitor</th>
        {% for cat in report.comparison_matrix.categories %}
        <th>{{ cat }}</th>
        {% endfor %}
    </tr>
    {% for comp_name, ratings in report.comparison_matrix.get('ratings', {}).items() %}
    <tr>
        <td style="font-weight: bold; color: {{ colors.primary_gold }};">{{ comp_name }}</td>
        {% for cat in report.comparison_matrix.categories %}
        <td>
            {% if ratings is mapping %}
                {% set rating = ratings.get(cat, 'N/A') %}
            {% else %}
                {% set rating = 'N/A' %}
            {% endif %}
            {% if rating | lower == 'strong' %}
                <span style="color: #2ECC71; font-weight: bold;">[Strong]</span>
            {% elif rating | lower == 'moderate' %}
                <span style="color: #F39C12; font-weight: bold;">[Moderate]</span>
            {% elif rating | lower == 'weak' %}
                <span style="color: #E74C3C; font-weight: bold;">[Weak]</span>
            {% else %}
                {{ rating }}
            {% endif %}
        </td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>
{% endif %}

<!-- ===== STRATEGIC INSIGHTS ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>05 &mdash; Strategic Insights</h1>

{% if report.get('strategic_insights') %}
{% set insights = report.strategic_insights %}

<h2>Our Strengths</h2>
<ul>
{% for item in insights.get('our_strengths', []) %}
    <li><span style="color: #2ECC71; font-weight: bold;">[+]</span> {{ item }}</li>
{% endfor %}
</ul>

<h2>Areas to Improve</h2>
<ul>
{% for item in insights.get('areas_to_improve', []) %}
    <li><span style="color: #F39C12; font-weight: bold;">[-]</span> {{ item }}</li>
{% endfor %}
</ul>

<h2>Market Gaps &amp; Opportunities</h2>
<div class="insight-box">
    <ul>
    {% for item in insights.get('market_gaps', []) %}
        <li><span class="gold-bullet">&bull;</span> {{ item }}</li>
    {% endfor %}
    </ul>
</div>

<h2>Threats to Monitor</h2>
<ul>
{% for item in insights.get('threats', []) %}
    <li><span style="color: #E74C3C; font-weight: bold;">[!]</span> {{ item }}</li>
{% endfor %}
</ul>

<div class="divider"></div>

<h2>Quick Wins</h2>
<div class="insight-box">
    <div class="insight-box-title">Immediate Opportunities</div>
    <ul>
    {% for item in insights.get('quick_wins', []) %}
        <li><span class="gold-bullet">&bull;</span> {{ item }}</li>
    {% endfor %}
    </ul>
</div>

<h2>Long-Term Strategic Plays</h2>
<div class="insight-box">
    <div class="insight-box-title">6-12 Month Initiatives</div>
    <ul>
    {% for item in insights.get('long_term_plays', []) %}
        <li><span class="gold-bullet">&bull;</span> {{ item }}</li>
    {% endfor %}
    </ul>
</div>
{% endif %}

<!-- ===== ACTION ITEMS ===== -->
<div class="page-break"></div>
{% if logo_b64 %}
<div class="page-header"><img src="data:image/png;base64,{{ logo_b64 }}" /></div>
{% endif %}
<h1>06 &mdash; Action Items</h1>

{% if report.get('action_items') %}
<table>
    <tr>
        <th style="width: 12%;">Priority</th>
        <th style="width: 35%;">Action</th>
        <th style="width: 40%;">Rationale</th>
        <th style="width: 13%;">Effort</th>
    </tr>
    {% for item in report.action_items %}
    <tr>
        <td><span class="badge badge-{{ item.get('priority', 'low') | lower }}">{{ item.get('priority', 'N/A') | upper }}</span></td>
        <td style="font-weight: bold;">{{ item.get('action', '') }}</td>
        <td>{{ item.get('rationale', '') }}</td>
        <td><span class="badge badge-{{ item.get('effort', 'low') | lower }}">{{ item.get('effort', 'N/A') | upper }}</span></td>
    </tr>
    {% endfor %}
</table>
{% endif %}

<div class="divider"></div>
<div style="text-align: center; margin-top: 30pt;">
    {% if logo_b64 %}
    <img style="width: 60pt;" src="data:image/png;base64,{{ logo_b64 }}" />
    {% endif %}
    <p style="color: {{ colors.text_muted }}; font-size: 9pt; margin-top: 10pt;">
        This report was generated as part of the WAT Framework competitive intelligence workflow.<br/>
        &copy; {{ year }} {{ company_name }}. All rights reserved.
    </p>
</div>

</body>
</html>
"""


def generate_pdf(output_filename=None):
    """Generate the branded PDF report."""
    brand = load_brand_config()
    analysis = load_analysis()
    logo_b64 = get_logo_base64()
    colors = brand.get("colors", {})
    
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")
    
    # Render HTML
    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        report=analysis,
        colors=colors,
        company_name=brand.get("company_name", "Company"),
        logo_b64=logo_b64,
        date=date_str,
        year=now.year
    )
    
    # Save HTML for debugging
    html_path = TMP_DIR / "report_preview.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML preview saved to {html_path}")
    
    # Generate PDF
    if not output_filename:
        safe_name = brand.get("company_name", "report").replace(" ", "_")
        output_filename = f"Competitive_Analysis_{safe_name}_{now.strftime('%Y%m%d')}.pdf"
    
    output_path = ROOT / output_filename
    
    print(f"Generating PDF...")
    with open(output_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_file,
            encoding="utf-8"
        )
    
    if pisa_status.err:
        print(f"ERROR: PDF generation had {pisa_status.err} errors.")
        return None
    
    print(f"PDF generated successfully: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    return str(output_path)


def main():
    result = generate_pdf()
    if result:
        print(f"\n✓ Report ready: {result}")
    else:
        print("\n✗ PDF generation failed.")


if __name__ == "__main__":
    main()
