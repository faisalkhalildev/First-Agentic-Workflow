"""
Branded PDF Report Generator
=============================
Premium white-background report with gold + slate design system.
Built specifically for xhtml2pdf constraints:
  - No floats, no border-radius, no position:absolute
  - No body background-color (always white in xhtml2pdf)
  - No ::before / ::after pseudo-elements
  - Tables for ALL multi-column layouts
  - Explicit widths on every table/cell
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
    path = CONFIG_DIR / "brand_config.json"
    if not path.exists():
        print("ERROR: brand_config.json not found.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_analysis():
    path = TMP_DIR / "analysis_report.json"
    if not path.exists():
        print("ERROR: analysis_report.json not found. Run generate_analysis.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_logo_base64():
    logo_path = CONFIG_DIR / "logo.png"
    if not logo_path.exists():
        return None
    with open(logo_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


# =============================================================================
#  DESIGN SYSTEM  (xhtml2pdf-safe, white-canvas professional report)
#
#  Canvas:      #FFFFFF  white page
#  Ink:         #1A1A2E  deep navy — primary text
#  Secondary:   #4A4A6A  slate — body text
#  Muted:       #8888AA  light slate — captions/meta
#  Gold:        #C9A84C  warm gold — primary accent
#  Gold light:  #F5E6B8  gold tint — backgrounds
#  Gold dark:   #8B6914  dark gold — small text on gold bg
#  Navy:        #1A1A2E  header bands, cover
#  Navy mid:    #2D2D4E  section headers
#  Navy light:  #E8E8F4  very light navy — zebra rows
#  Green:       #1E7E4A  positive
#  Green light: #D4F5E4  green tint
#  Amber:       #C97B00  medium/warning
#  Amber light: #FFF3CC  amber tint
#  Red:         #B02020  high/danger
#  Red light:   #FAE0E0  red tint
#  Blue:        #1A6EB5  opportunity
#  Blue light:  #DCF0FF  blue tint
#  Border:      #DDDDEE  subtle line
# =============================================================================

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>

@page {
    size: A4;
    margin: 0;
    @frame content_frame {
        left: 54pt; right: 54pt;
        top: 54pt; bottom: 64pt;
    }
    @frame footer_frame {
        -pdf-frame-content: footer-block;
        left: 54pt; right: 54pt;
        bottom: 16pt; height: 28pt;
    }
}

body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    color: #2D2D4E;
    background-color: #FFFFFF;
    line-height: 1.6;
    margin: 0; padding: 0;
}

/* ── HEADINGS ── */
h1 {
    font-size: 17pt; font-weight: bold;
    color: #1A1A2E;
    margin: 0 0 4pt 0; padding: 0;
    line-height: 1.2;
}
h2 {
    font-size: 11pt; font-weight: bold;
    color: #1A1A2E;
    margin: 16pt 0 6pt 0;
}
h3 {
    font-size: 9pt; font-weight: bold;
    color: #4A4A6A;
    margin: 10pt 0 4pt 0;
    text-transform: uppercase;
    letter-spacing: 0.8pt;
}
p {
    margin: 0 0 8pt 0;
    color: #4A4A6A;
    text-align: justify;
}

/* ── SECTION DIVIDER LINE ── */
.rule-gold {
    border: none; border-top: 2pt solid #C9A84C;
    margin: 0 0 14pt 0;
}
.rule-thin {
    border: none; border-top: 1pt solid #DDDDEE;
    margin: 12pt 0;
}

/* ── PAGE BREAK ── */
.pb { page-break-before: always; }

/* ── EYEBROW (small label above heading) ── */
.eyebrow {
    font-size: 7.5pt;
    letter-spacing: 3pt;
    color: #8B6914;
    text-transform: uppercase;
    margin: 0 0 4pt 0;
    display: block;
}

/* ── FOOTER ── */
.footer-bar {
    border-top: 1pt solid #DDDDEE;
    padding-top: 5pt;
    text-align: center;
    font-size: 7.5pt;
    color: #AAAACC;
}
.footer-brand { color: #C9A84C; font-weight: bold; }

/* ── PAGE HEADER BAND ── */
.page-hdr-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16pt;
}
.page-hdr-left {
    font-size: 7.5pt;
    color: #AAAACC;
    letter-spacing: 2pt;
    text-transform: uppercase;
    padding: 0 0 6pt 0;
    border-bottom: 2pt solid #C9A84C;
    vertical-align: bottom;
}
.page-hdr-right {
    text-align: right;
    padding: 0 0 6pt 0;
    border-bottom: 2pt solid #C9A84C;
    vertical-align: bottom;
    width: 42pt;
}
.page-hdr-logo {
    width: 36pt;
    height: 36pt;
}

/* ── TOC ── */
.toc-num {
    font-size: 20pt; font-weight: bold;
    color: #E8E8F4;
    width: 36pt;
    padding: 10pt 8pt 10pt 0;
    vertical-align: middle;
}
.toc-title {
    font-size: 11pt; font-weight: bold;
    color: #1A1A2E;
    padding: 10pt 0;
    vertical-align: middle;
}
.toc-pill-cell {
    width: 80pt;
    text-align: right;
    vertical-align: middle;
    padding: 10pt 0;
}
.toc-pill {
    font-size: 7.5pt;
    background-color: #F5E6B8;
    color: #8B6914;
    padding: 2pt 8pt;
    border: 1pt solid #C9A84C;
}

/* ── COMPETITOR CARD ── */
.comp-card {
    border: 1pt solid #DDDDEE;
    margin-bottom: 16pt;
}
.comp-card-header {
    background-color: #1A1A2E;
    padding: 10pt 14pt;
    width: 100%;
    border-collapse: collapse;
}
.comp-card-name {
    font-size: 13pt; font-weight: bold;
    color: #FFFFFF;
    vertical-align: middle;
}
.comp-card-badge-cell {
    text-align: right;
    vertical-align: middle;
    width: 110pt;
}
.comp-card-url {
    font-size: 8pt;
    color: #8888AA;
    padding: 4pt 14pt 0 14pt;
    background-color: #F8F8FC;
    border-bottom: 1pt solid #EBEBF5;
    padding-bottom: 4pt;
}
.comp-card-body {
    padding: 12pt 14pt;
}

/* ── STAT STRIP ── */
.stat-strip {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0 10pt 0;
}
.stat-cell-left {
    width: 50%;
    background-color: #F8F8FC;
    border: 1pt solid #EBEBF5;
    border-right: none;
    padding: 8pt 11pt;
    vertical-align: top;
}
.stat-cell-right {
    width: 50%;
    background-color: #F8F8FC;
    border: 1pt solid #EBEBF5;
    padding: 8pt 11pt;
    vertical-align: top;
}
.stat-label {
    font-size: 6.5pt;
    color: #AAAACC;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 3pt;
    display: block;
}
.stat-value {
    font-size: 9pt;
    color: #1A1A2E;
    font-weight: bold;
}

/* ── STRENGTHS / WEAKNESSES ── */
.sw-table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0;
}
.sw-hdr-s {
    background-color: #D4F5E4;
    color: #1E7E4A;
    font-size: 7.5pt; font-weight: bold;
    text-transform: uppercase; letter-spacing: 1pt;
    padding: 6pt 10pt;
    width: 50%;
    border-bottom: 2pt solid #1E7E4A;
}
.sw-hdr-w {
    background-color: #FAE0E0;
    color: #B02020;
    font-size: 7.5pt; font-weight: bold;
    text-transform: uppercase; letter-spacing: 1pt;
    padding: 6pt 10pt;
    border-left: 1pt solid #DDDDEE;
    border-bottom: 2pt solid #B02020;
}
.sw-body-s {
    background-color: #F2FBF6;
    vertical-align: top;
    padding: 8pt 10pt;
    border-right: 1pt solid #DDDDEE;
    border-bottom: 1pt solid #DDDDEE;
}
.sw-body-w {
    background-color: #FDF5F5;
    vertical-align: top;
    padding: 8pt 10pt;
    border-bottom: 1pt solid #DDDDEE;
}
.sw-item {
    font-size: 8.5pt;
    color: #4A4A6A;
    margin-bottom: 4pt;
    padding-left: 10pt;
}

/* ── TAKEAWAY ── */
.takeaway {
    background-color: #FFFBEE;
    border-left: 3pt solid #C9A84C;
    border-top: 1pt solid #F0DFA0;
    border-right: 1pt solid #F0DFA0;
    border-bottom: 1pt solid #F0DFA0;
    padding: 8pt 12pt;
    margin-top: 10pt;
}
.takeaway-lbl {
    font-size: 7pt; font-weight: bold;
    color: #8B6914;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 3pt;
    display: block;
}
.takeaway p { color: #5A4A10; margin: 0; font-style: italic; }

/* ── DATA TABLE (matrix, actions) ── */
table.dt {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    font-size: 8.5pt;
}
table.dt th {
    background-color: #1A1A2E;
    color: #C9A84C;
    padding: 8pt 10pt;
    text-align: left;
    font-weight: bold;
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    border-right: 1pt solid #2D2D4E;
}
table.dt td {
    padding: 7pt 10pt;
    border-bottom: 1pt solid #EBEBF5;
    border-right: 1pt solid #F0F0F8;
    color: #4A4A6A;
    vertical-align: top;
}
table.dt tr:nth-child(even) td {
    background-color: #F8F8FC;
}
table.dt .td-name {
    font-weight: bold;
    color: #1A1A2E;
}

/* ── RATING PILLS ── */
.r-strong {
    font-size: 7.5pt; font-weight: bold;
    background-color: #D4F5E4;
    color: #1E7E4A;
    border: 1pt solid #1E7E4A;
    padding: 2pt 7pt;
}
.r-moderate {
    font-size: 7.5pt; font-weight: bold;
    background-color: #FFF3CC;
    color: #C97B00;
    border: 1pt solid #C97B00;
    padding: 2pt 7pt;
}
.r-weak {
    font-size: 7.5pt; font-weight: bold;
    background-color: #FAE0E0;
    color: #B02020;
    border: 1pt solid #B02020;
    padding: 2pt 7pt;
}

/* ── STATUS BADGES ── */
.badge {
    font-size: 7pt; font-weight: bold;
    letter-spacing: 0.5pt;
    padding: 2pt 8pt;
    text-transform: uppercase;
    color: #FFFFFF;
}
.badge-high   { background-color: #B02020; }
.badge-medium { background-color: #C97B00; }
.badge-low    { background-color: #1E7E4A; }

/* ── CALLOUT / HIGHLIGHT BOX ── */
.callout {
    background-color: #FFFBEE;
    border: 1pt solid #F0DFA0;
    border-left: 3pt solid #C9A84C;
    padding: 10pt 14pt;
    margin: 10pt 0;
}
.callout-title {
    font-size: 7.5pt; font-weight: bold;
    color: #8B6914;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 5pt;
    display: block;
}
.callout p { color: #5A4A10; margin: 0; }

/* ── QUADRANT TABLE ── */
.quad-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
}
.q-cell {
    width: 50%;
    vertical-align: top;
    padding: 12pt 13pt;
    border: 1pt solid #DDDDEE;
}
.q-green { background-color: #F2FBF6; border-top: 2.5pt solid #1E7E4A; }
.q-amber { background-color: #FFFCF0; border-top: 2.5pt solid #C97B00; }
.q-blue  { background-color: #F0F7FF; border-top: 2.5pt solid #1A6EB5; }
.q-red   { background-color: #FDF5F5; border-top: 2.5pt solid #B02020; }
.q-title {
    font-size: 8pt; font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 8pt;
    display: block;
}
.q-title-green { color: #1E7E4A; }
.q-title-amber { color: #C97B00; }
.q-title-blue  { color: #1A6EB5; }
.q-title-red   { color: #B02020; }
.q-item {
    font-size: 8.5pt;
    color: #4A4A6A;
    margin-bottom: 5pt;
    padding-left: 12pt;
}
.q-item-s::before { content: "+ "; color: #1E7E4A; font-weight: bold; margin-left: -12pt; }
.q-item-a::before { content: "- "; color: #C97B00; font-weight: bold; margin-left: -12pt; }
.q-item-b::before { content: "> "; color: #1A6EB5; font-weight: bold; margin-left: -12pt; }
.q-item-r::before { content: "! "; color: #B02020; font-weight: bold; margin-left: -12pt; }

/* ── STYLED LIST ── */
ul.sl {
    margin: 4pt 0 8pt 16pt;
    padding: 0;
}
ul.sl li {
    color: #4A4A6A;
    font-size: 9pt;
    margin-bottom: 4pt;
    padding-left: 4pt;
}

/* ── MARKET TREND ITEM ── */
.trend-item {
    background-color: #F8F8FC;
    border-left: 2pt solid #C9A84C;
    padding: 6pt 10pt;
    margin-bottom: 5pt;
    font-size: 9pt;
    color: #2D2D4E;
}

</style>
</head>
<body>

<!-- FOOTER BLOCK -->
<div id="footer-block">
    <div class="footer-bar">
        <span class="footer-brand">{{ company_name }}</span>
        &nbsp;&bull;&nbsp;Competitive Intelligence Report&nbsp;&bull;&nbsp;{{ date }}
    </div>
</div>


<!-- =====================================================
     COVER PAGE
===================================================== -->
<table style="width:100%;height:720pt;border-collapse:collapse;">
    <!-- Gold top stripe -->
    <tr>
        <td style="height:8pt;background-color:#C9A84C;padding:0;"></td>
    </tr>
    <!-- Navy header band -->
    <tr>
        <td style="background-color:#1A1A2E;padding:40pt 54pt 36pt 54pt;vertical-align:middle;">
            {% if logo_b64 %}
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="vertical-align:middle;">
                        <img src="data:image/png;base64,{{ logo_b64 }}" style="width:72pt;height:72pt;" />
                    </td>
                    <td style="vertical-align:middle;text-align:right;">
                        <span style="font-size:8pt;letter-spacing:3pt;color:#C9A84C;text-transform:uppercase;">Competitive Intelligence</span>
                    </td>
                </tr>
            </table>
            {% else %}
            <span style="font-size:8pt;letter-spacing:3pt;color:#C9A84C;text-transform:uppercase;">Competitive Intelligence</span>
            {% endif %}
        </td>
    </tr>
    <!-- White body -->
    <tr>
        <td style="background-color:#FFFFFF;padding:54pt 54pt 40pt 54pt;vertical-align:top;">
            <span style="font-size:8pt;letter-spacing:3pt;color:#8B6914;text-transform:uppercase;display:block;margin-bottom:10pt;">Market Analysis Report</span>
            <div style="font-size:26pt;font-weight:bold;color:#1A1A2E;line-height:1.2;margin-bottom:8pt;">{{ report.get('report_title', 'Competitive Analysis Report') }}</div>
            <div style="width:48pt;height:2pt;background-color:#C9A84C;margin:14pt 0;"></div>
            <p style="font-size:12pt;color:#4A4A6A;margin:0 0 6pt 0;">Prepared for <strong style="color:#1A1A2E;">{{ company_name }}</strong></p>
            <p style="font-size:9pt;color:#8888AA;margin:0;">AI-Powered Market Intelligence &nbsp;&bull;&nbsp; WAT Framework</p>
            <div style="margin-top:40pt;background-color:#F5E6B8;border:1pt solid #C9A84C;padding:7pt 18pt;display:inline-block;">
                <span style="font-size:9pt;font-weight:bold;color:#8B6914;letter-spacing:1pt;">{{ date }}</span>
            </div>
        </td>
    </tr>
    <!-- Light footer band -->
    <tr>
        <td style="background-color:#F8F8FC;border-top:1pt solid #DDDDEE;padding:16pt 54pt;vertical-align:middle;">
            <span style="font-size:8pt;color:#AAAACC;">Confidential — For internal use only</span>
        </td>
    </tr>
    <!-- Gold bottom stripe -->
    <tr>
        <td style="height:8pt;background-color:#C9A84C;padding:0;"></td>
    </tr>
</table>


<!-- =====================================================
     TABLE OF CONTENTS
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Contents</td>
        <td class="page-hdr-right">
            {% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}
        </td>
    </tr>
</table>

<span class="eyebrow">Navigation</span>
<h1>Table of Contents</h1>
<hr class="rule-gold" />

<table style="width:100%;border-collapse:collapse;margin-top:6pt;">
    {% for num, title, tag in [
        ('01','Executive Summary','Overview'),
        ('02','Market Overview','Landscape'),
        ('03','Competitor Profiles','Profiles'),
        ('04','Comparison Matrix','Matrix'),
        ('05','Strategic Insights','Strategy'),
        ('06','Action Items','Actions')
    ] %}
    <tr style="border-bottom:1pt solid #EBEBF5;">
        <td class="toc-num">{{ num }}</td>
        <td class="toc-title">{{ title }}</td>
        <td class="toc-pill-cell"><span class="toc-pill">{{ tag }}</span></td>
    </tr>
    {% endfor %}
</table>


<!-- =====================================================
     01  EXECUTIVE SUMMARY
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Executive Summary</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 01</span>
<h1>Executive Summary</h1>
<hr class="rule-gold" />

{% set summary = report.get('executive_summary', '') %}
{% for para in summary.split('\n') %}
    {% if para.strip() %}<p>{{ para.strip() }}</p>{% endif %}
{% endfor %}


<!-- =====================================================
     02  MARKET OVERVIEW
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Market Overview</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 02</span>
<h1>Market Overview</h1>
<hr class="rule-gold" />

{% set landscape = report.get('market_overview', {}).get('landscape_description', '') %}
{% for para in landscape.split('\n') %}
    {% if para.strip() %}<p>{{ para.strip() }}</p>{% endif %}
{% endfor %}

<h2>Market Trends</h2>
{% for trend in report.get('market_overview', {}).get('market_trends', []) %}
<div class="trend-item">{{ trend }}</div>
{% endfor %}

{% set signals = report.get('market_overview', {}).get('market_size_signals', '') %}
{% if signals %}
<div class="callout" style="margin-top:14pt;">
    <span class="callout-title">Market Size Signals</span>
    <p>{{ signals }}</p>
</div>
{% endif %}


<!-- =====================================================
     03  COMPETITOR PROFILES
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Competitor Profiles</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 03</span>
<h1>Competitor Profiles</h1>
<hr class="rule-gold" />

{% for comp in report.get('competitor_profiles', []) %}

{% if loop.index > 1 %}
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Competitor Profiles — Continued</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>
{% endif %}

{% set tl = comp.get('threat_level', 'low') | lower %}

<div class="comp-card">
    <!-- Dark header band -->
    <table class="comp-card-header" style="width:100%;border-collapse:collapse;">
        <tr>
            <td class="comp-card-name">{{ comp.get('name', 'Unknown') }}</td>
            <td class="comp-card-badge-cell">
                <span class="badge badge-{{ tl }}">
                    {% if tl == 'high' %}HIGH THREAT{% elif tl == 'medium' %}MED THREAT{% else %}LOW THREAT{% endif %}
                </span>
            </td>
        </tr>
    </table>
    <!-- URL subheader -->
    <div class="comp-card-url">{{ comp.get('website', '') }}</div>
    <!-- Body -->
    <div class="comp-card-body">

        <p style="margin-bottom:10pt;">{{ comp.get('overview', '') }}</p>

        <!-- Pricing + Audience stat strip -->
        <table class="stat-strip">
            <tr>
                <td class="stat-cell-left">
                    <span class="stat-label">Pricing Model</span>
                    <span class="stat-value">{{ comp.get('pricing_model', 'Unknown') }}</span>
                </td>
                <td class="stat-cell-right">
                    <span class="stat-label">Target Audience</span>
                    <span class="stat-value">{{ comp.get('target_audience', 'N/A') }}</span>
                </td>
            </tr>
        </table>

        <!-- Products & Services -->
        <h3>Products &amp; Services</h3>
        <ul class="sl">
        {% for item in comp.get('products_services', []) %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>

        <!-- Strengths / Weaknesses two-col -->
        <table class="sw-table">
            <tr>
                <td class="sw-hdr-s">+ Strengths</td>
                <td class="sw-hdr-w" style="border-left:1pt solid #DDDDEE;">- Weaknesses</td>
            </tr>
            <tr>
                <td class="sw-body-s">
                {% for s in comp.get('strengths', []) %}
                    <div class="sw-item">+ &nbsp;{{ s }}</div>
                {% endfor %}
                </td>
                <td class="sw-body-w">
                {% for w in comp.get('weaknesses', []) %}
                    <div class="sw-item">- &nbsp;{{ w }}</div>
                {% endfor %}
                </td>
            </tr>
        </table>

        <!-- Key Takeaway -->
        <div class="takeaway">
            <span class="takeaway-lbl">Key Takeaway</span>
            <p>{{ comp.get('key_takeaway', '') }}</p>
        </div>

    </div>
</div>

{% endfor %}


<!-- =====================================================
     04  COMPARISON MATRIX
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Comparison Matrix</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 04</span>
<h1>Comparison Matrix</h1>
<hr class="rule-gold" />

{% if report.get('comparison_matrix') and report.comparison_matrix.get('categories') %}
<table class="dt">
    <tr>
        <th style="width:22%;">Competitor</th>
        {% for cat in report.comparison_matrix.categories %}
        <th>{{ cat }}</th>
        {% endfor %}
    </tr>
    {% for comp_name, ratings in report.comparison_matrix.get('ratings', {}).items() %}
    <tr>
        <td class="td-name">{{ comp_name }}</td>
        {% for cat in report.comparison_matrix.categories %}
        <td style="text-align:center;">
            {% if ratings is mapping %}{% set rating = ratings.get(cat, 'N/A') %}{% else %}{% set rating = 'N/A' %}{% endif %}
            {% if rating | lower == 'strong' %}<span class="r-strong">Strong</span>
            {% elif rating | lower == 'moderate' %}<span class="r-moderate">Moderate</span>
            {% elif rating | lower == 'weak' %}<span class="r-weak">Weak</span>
            {% else %}<span style="color:#AAAACC;font-size:8pt;">{{ rating }}</span>{% endif %}
        </td>
        {% endfor %}
    </tr>
    {% endfor %}
</table>

<div style="margin-top:8pt;padding:6pt 10pt;background-color:#F8F8FC;border:1pt solid #EBEBF5;">
    <span style="font-size:7.5pt;color:#AAAACC;">Legend: &nbsp;</span>
    <span class="r-strong">Strong</span>&nbsp;
    <span class="r-moderate">Moderate</span>&nbsp;
    <span class="r-weak">Weak</span>
    <span style="font-size:7.5pt;color:#AAAACC;margin-left:10pt;">— Relative competitive position per category</span>
</div>
{% endif %}


<!-- =====================================================
     05  STRATEGIC INSIGHTS
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Strategic Insights</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 05</span>
<h1>Strategic Insights</h1>
<hr class="rule-gold" />

{% if report.get('strategic_insights') %}
{% set ins = report.strategic_insights %}

<table class="quad-table">
    <tr>
        <td class="q-cell q-green">
            <span class="q-title q-title-green">+ Our Strengths</span>
            {% for item in ins.get('our_strengths', []) %}
            <div class="q-item">+ &nbsp;{{ item }}</div>
            {% endfor %}
        </td>
        <td class="q-cell q-amber" style="border-left:none;">
            <span class="q-title q-title-amber">~ Areas to Improve</span>
            {% for item in ins.get('areas_to_improve', []) %}
            <div class="q-item">- &nbsp;{{ item }}</div>
            {% endfor %}
        </td>
    </tr>
    <tr>
        <td class="q-cell q-blue" style="border-top:none;">
            <span class="q-title q-title-blue">&gt; Market Gaps</span>
            {% for item in ins.get('market_gaps', []) %}
            <div class="q-item">&gt; &nbsp;{{ item }}</div>
            {% endfor %}
        </td>
        <td class="q-cell q-red" style="border-top:none;border-left:none;">
            <span class="q-title q-title-red">! Threats</span>
            {% for item in ins.get('threats', []) %}
            <div class="q-item">! &nbsp;{{ item }}</div>
            {% endfor %}
        </td>
    </tr>
</table>

<hr class="rule-thin" />

<h2>Quick Wins</h2>
<div class="callout">
    <span class="callout-title">Immediate Opportunities — Act Now</span>
    <ul class="sl">
    {% for item in ins.get('quick_wins', []) %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</div>

<h2>Long-Term Strategic Plays</h2>
<div class="callout" style="border-left-color:#1A6EB5;background-color:#F0F7FF;border-color:#B0D4F0;">
    <span class="callout-title" style="color:#1A6EB5;">6–12 Month Initiatives</span>
    <ul class="sl">
    {% for item in ins.get('long_term_plays', []) %}
        <li>{{ item }}</li>
    {% endfor %}
    </ul>
</div>
{% endif %}


<!-- =====================================================
     06  ACTION ITEMS
===================================================== -->
<div class="pb"></div>
<table class="page-hdr-table">
    <tr>
        <td class="page-hdr-left">Action Items</td>
        <td class="page-hdr-right">{% if logo_b64 %}<img src="data:image/png;base64,{{ logo_b64 }}" class="page-hdr-logo" />{% endif %}</td>
    </tr>
</table>

<span class="eyebrow">Section 06</span>
<h1>Action Items</h1>
<hr class="rule-gold" />

{% if report.get('action_items') %}
<div style="margin-bottom:10pt;padding:6pt 10pt;background-color:#F8F8FC;border:1pt solid #EBEBF5;">
    <span style="font-size:7.5pt;color:#AAAACC;">Priority / Effort: &nbsp;</span>
    <span class="badge badge-high">High</span>&nbsp;
    <span class="badge badge-medium">Medium</span>&nbsp;
    <span class="badge badge-low">Low</span>
</div>

<table class="dt">
    <tr>
        <th style="width:10%;">Priority</th>
        <th style="width:33%;">Action</th>
        <th style="width:42%;">Rationale</th>
        <th style="width:15%;">Effort</th>
    </tr>
    {% for item in report.action_items %}
    {% set pr = item.get('priority', 'low') | lower %}
    {% set ef = item.get('effort', 'low') | lower %}
    <tr>
        <td style="text-align:center;"><span class="badge badge-{{ pr }}">{{ pr | upper }}</span></td>
        <td style="font-weight:bold;color:#1A1A2E;font-size:9pt;">{{ item.get('action', '') }}</td>
        <td style="color:#6A6A8A;font-size:8.5pt;">{{ item.get('rationale', '') }}</td>
        <td style="text-align:center;"><span class="badge badge-{{ ef }}">{{ ef | upper }}</span></td>
    </tr>
    {% endfor %}
</table>
{% endif %}


<!-- =====================================================
     BACK COVER
===================================================== -->
<div class="pb"></div>
<table style="width:100%;height:720pt;border-collapse:collapse;">
    <tr>
        <td style="height:8pt;background-color:#C9A84C;padding:0;"></td>
    </tr>
    <tr>
        <td style="background-color:#1A1A2E;padding:60pt 54pt;vertical-align:middle;text-align:center;">
            {% if logo_b64 %}
            <img src="data:image/png;base64,{{ logo_b64 }}" style="width:80pt;height:80pt;" /><br/>
            {% endif %}
            <div style="width:36pt;height:2pt;background-color:#C9A84C;margin:20pt auto 16pt auto;"></div>
            <div style="font-size:16pt;font-weight:bold;color:#FFFFFF;margin-bottom:6pt;">{{ company_name }}</div>
            <div style="font-size:9pt;color:#8888AA;margin-bottom:30pt;">AI-Powered Competitive Intelligence</div>
            <div style="font-size:8pt;color:#555577;">
                Generated by the WAT Framework &nbsp;&bull;&nbsp; {{ date }}<br/>
                &copy; {{ year }} {{ company_name }}. All rights reserved.
            </div>
        </td>
    </tr>
    <tr>
        <td style="height:8pt;background-color:#C9A84C;padding:0;"></td>
    </tr>
</table>


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

    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        report=analysis,
        colors=colors,
        company_name=brand.get("company_name", "Company"),
        logo_b64=logo_b64,
        date=date_str,
        year=now.year
    )

    # Save HTML preview for debugging
    html_path = TMP_DIR / "report_preview.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML preview saved to {html_path}")

    if not output_filename:
        safe_name = brand.get("company_name", "report").replace(" ", "_")
        output_filename = f"Competitive_Analysis_{safe_name}_{now.strftime('%Y%m%d')}.pdf"

    output_path = ROOT / output_filename

    print(f"Generating PDF: {output_path}")
    with open(output_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_file,
            encoding="utf-8"
        )

    if pisa_status.err:
        print(f"ERROR: PDF generation had {pisa_status.err} error(s). Check {html_path} to debug.")
        return None

    size_kb = output_path.stat().st_size / 1024
    print(f"PDF generated: {output_path}  ({size_kb:.1f} KB)")
    return str(output_path)


def main():
    result = generate_pdf()
    if result:
        print(f"\n[OK] Report ready: {result}")
    else:
        print("\n[FAIL] PDF generation failed.")


if __name__ == "__main__":
    main()
