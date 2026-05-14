"""
Competitor Research Tool
========================
Takes the discovered competitors list and performs deep research on each one.
Scrapes websites, gathers info on offerings, pricing, messaging, and more.
Uses OpenAI to summarize and structure findings.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Load environment
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "workflows" / "config"
TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def load_competitors():
    """Load discovered competitors from Phase 2 output."""
    path = TMP_DIR / "competitors_raw.json"
    if not path.exists():
        print("ERROR: competitors_raw.json not found. Run discover_competitors.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_business_profile():
    """Load the business profile from config."""
    path = CONFIG_DIR / "business_profile.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scrape_page(url, timeout=15):
    """Scrape a webpage and return cleaned text content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts, styles, nav, footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:5000]  # Cap at 5000 chars
    except Exception as e:
        return f"[Scraping failed: {e}]"


def scrape_competitor_pages(competitor):
    """Scrape key pages from a competitor's website."""
    base_url = competitor["url"]
    domain = competitor["domain"]
    base = f"https://{domain}"

    pages = {}
    
    # Try common pages
    urls_to_try = {
        "homepage": base,
        "about": [f"{base}/about", f"{base}/about-us", f"{base}/company"],
        "pricing": [f"{base}/pricing", f"{base}/plans"],
        "products": [f"{base}/products", f"{base}/services", f"{base}/solutions", f"{base}/features"],
    }

    # Homepage
    print(f"    Scraping homepage...")
    pages["homepage"] = scrape_page(base)
    time.sleep(1)

    # Try other pages
    for page_type, urls in urls_to_try.items():
        if page_type == "homepage":
            continue
        if isinstance(urls, str):
            urls = [urls]
        for url in urls:
            print(f"    Trying {page_type}: {url}")
            content = scrape_page(url)
            if "[Scraping failed" not in content and len(content) > 100:
                pages[page_type] = content
                time.sleep(0.5)
                break
        else:
            pages[page_type] = "[Page not found]"

    return pages


def analyze_competitor_with_ai(competitor, scraped_data, business_profile):
    """Use OpenAI to analyze scraped competitor data and produce structured insights."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Build the analysis prompt
    scraped_summary = ""
    for page, content in scraped_data.items():
        scraped_summary += f"\n--- {page.upper()} ---\n{content[:2000]}\n"

    prompt = f"""Analyze this competitor based on the scraped website data below.

COMPETITOR: {competitor['name']} ({competitor['domain']})
INITIAL DESCRIPTION: {competitor.get('description', 'N/A')}

OUR BUSINESS FOR CONTEXT:
- Name: {business_profile.get('name', 'N/A')}
- Industry: {business_profile.get('industry', 'N/A')}
- Offerings: {', '.join(business_profile.get('offerings', []))}

SCRAPED DATA:
{scraped_summary}

Produce a JSON analysis with these exact keys:
{{
    "company_name": "string",
    "website": "string",
    "tagline": "their main tagline or value proposition",
    "overview": "2-3 sentence company overview",
    "products_services": ["list of their main products/services"],
    "pricing_model": "description of pricing approach (free, freemium, subscription, etc.) or 'Unknown'",
    "target_audience": "who they serve",
    "key_messaging": "how they position themselves — their main selling points",
    "strengths": ["list of 3-5 things they do well"],
    "weaknesses": ["list of 2-4 apparent gaps or weaknesses"],
    "content_strategy": "brief assessment of their content/blog/social approach",
    "unique_differentiators": ["what makes them stand out"],
    "threat_level": "low / medium / high — how much of a competitive threat they pose to our business",
    "opportunities_for_us": ["2-3 specific opportunities we could capitalize on based on their gaps"]
}}

Return ONLY valid JSON, no markdown formatting or code blocks."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a competitive intelligence analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        result_text = response.choices[0].message.content.strip()
        # Clean potential markdown wrapping
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        print(f"    Warning: AI returned invalid JSON: {e}")
        return {"error": "Failed to parse AI analysis", "raw": result_text[:500]}
    except Exception as e:
        print(f"    Warning: AI analysis failed: {e}")
        return {"error": str(e)}


def research_all_competitors():
    """Main function: research every discovered competitor."""
    data = load_competitors()
    profile = load_business_profile()
    competitors = data.get("competitors", [])

    if not competitors:
        print("No competitors to research.")
        return

    print(f"Researching {len(competitors)} competitors...\n")
    results = []

    for i, comp in enumerate(competitors, 1):
        print(f"[{i}/{len(competitors)}] Researching: {comp['name']} ({comp['domain']})")
        
        # Scrape their website
        scraped = scrape_competitor_pages(comp)
        
        # Analyze with AI
        print(f"    Analyzing with AI...")
        analysis = analyze_competitor_with_ai(comp, scraped, profile)
        
        # Save individual result
        safe_name = comp["domain"].replace(".", "_").replace("-", "_")
        individual_path = TMP_DIR / f"competitor_{safe_name}.json"
        with open(individual_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        results.append(analysis)
        print(f"    Done. Saved to {individual_path}\n")
        
        # Rate limit between competitors
        if i < len(competitors):
            time.sleep(2)

    # Save combined results
    combined_path = TMP_DIR / "competitors_researched.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump({
            "business": profile.get("name", "Unknown"),
            "total_researched": len(results),
            "competitors": results
        }, f, indent=2, ensure_ascii=False)

    print(f"All research complete. Combined results: {combined_path}")
    return results


def main():
    research_all_competitors()


if __name__ == "__main__":
    main()
