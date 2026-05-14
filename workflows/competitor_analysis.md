# Competitor Analysis Workflow

## Objective
Discover competitors, research their offerings and positioning, produce a comparative analysis, and generate a branded PDF report.

## Prerequisites
- Business profile filled in at `workflows/config/business_profile.json`
- Brand config at `workflows/config/brand_config.json`
- Logo at `workflows/config/logo.png`
- API keys in `.env`:
  - `TAVILY_API_KEY` — for competitor discovery (free tier: https://tavily.com)
  - `OPENAI_API_KEY` — for AI-powered analysis

## Execution Sequence

### Phase 1: Verify Profile & Brand
- Check that `business_profile.json` has industry, offerings, and target_audience filled in
- Check that `brand_config.json` and `logo.png` exist
- If anything is missing, ask the user for the information

### Phase 2: Discover Competitors
- **Tool:** `tools/discover_competitors.py`
- **Input:** Business profile (auto-loaded)
- **Output:** `.tmp/competitors_raw.json`
- Finds 5-10 competitors via Tavily search
- Review the list with the user — they may want to add/remove competitors

### Phase 3: Research Each Competitor
- **Tool:** `tools/research_competitor.py`
- **Input:** `.tmp/competitors_raw.json`
- **Output:** `.tmp/competitor_{name}.json` per competitor + `.tmp/competitors_researched.json`
- Scrapes competitor websites and uses GPT-4o-mini for structured analysis
- ⚠️ Uses OpenAI API credits — confirm with user before running if cost is a concern

### Phase 4: Generate Analysis
- **Tool:** `tools/generate_analysis.py`
- **Input:** `.tmp/competitors_researched.json` + business profile
- **Output:** `.tmp/analysis_report.json`
- Uses GPT-4o for comprehensive strategic analysis
- ⚠️ Uses OpenAI API credits

### Phase 5: Generate Branded PDF
- **Tool:** `tools/generate_pdf.py`
- **Input:** `.tmp/analysis_report.json` + brand config + logo
- **Output:** `Competitive_Analysis_{company}_{date}.pdf` in project root
- Also saves `.tmp/report_preview.html` for debugging

## Error Handling
- If Tavily search fails: check API key, check rate limits (1000 searches/mo on free tier)
- If scraping fails: some sites block scrapers — the tool handles this gracefully and continues
- If OpenAI fails: check API key, check credits
- If PDF generation fails: check `.tmp/report_preview.html` to debug HTML issues

## Improvements Log
- *(Add learnings here as the workflow evolves)*
