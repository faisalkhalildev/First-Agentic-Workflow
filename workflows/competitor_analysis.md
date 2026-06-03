# Competitor Analysis Workflow

## Objective
Discover competitors, research their offerings and positioning, produce a comparative analysis, and generate a branded PDF report.

## Prerequisites
- Business profile filled in at `workflows/config/business_profile.json`
- Brand config at `workflows/config/brand_config.json`
- Logo at `workflows/config/logo.png`
- API keys in `.env`:
  - `TAVILY_API_KEY` — for competitor discovery (free tier: https://tavily.com)
  - `GOOGLE_API_KEY` — for AI-powered analysis via Gemini 2.0 Flash (https://aistudio.google.com)

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
- Scrapes competitor websites and uses Gemini 2.0 Flash for structured analysis
- ⚠️ Uses Google Gemini API credits — confirm with user before running if cost is a concern
- ⚠️ Free tier has rate limits — the tool automatically waits 15s between competitors and uses exponential backoff on 429 errors

### Phase 4: Generate Analysis
- **Tool:** `tools/generate_analysis.py`
- **Input:** `.tmp/competitors_researched.json` + business profile
- **Output:** `.tmp/analysis_report.json`
- Uses Gemini 2.0 Flash for comprehensive strategic analysis
- ⚠️ Competitors with research errors (e.g. from quota limits in Phase 3) are automatically skipped
- ⚠️ Uses Google Gemini API credits

### Phase 5: Generate Branded PDF
- **Tool:** `tools/generate_pdf.py`
- **Input:** `.tmp/analysis_report.json` + brand config + logo
- **Output:** `Competitive_Analysis_{company}_{date}.pdf` in project root
- Also saves `.tmp/report_preview.html` for debugging

## Error Handling
- If Tavily search fails: check API key, check rate limits (1000 searches/mo on free tier)
- If scraping fails: some sites block scrapers — the tool handles this gracefully and continues
- If Gemini returns 429 (quota exceeded): the tool waits and retries with exponential backoff; if the free daily limit is hit, wait until the next day or upgrade your plan
- If Gemini analysis fails for a competitor: that competitor is saved as `{"error": "..."}` and skipped in Phase 4
- If PDF generation fails: check `.tmp/report_preview.html` to debug HTML issues; all template fields use safe `.get()` defaults so missing AI fields won't crash the render

## Improvements Log
- Fixed Jinja2 template to use `.get()` defaults on all competitor/analysis fields — prevents crashes when AI returns partial data
- Added 429 rate limit detection with exponential backoff in research phase
- Increased inter-competitor delay to 15s to respect Gemini free tier limits
- Analysis phase now filters out errored competitor entries before building the AI prompt
- Updated doc: replaced all OpenAI/GPT-4o references with Gemini 2.0 Flash / GOOGLE_API_KEY
