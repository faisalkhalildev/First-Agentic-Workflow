"""
Competitor Discovery Tool
=========================
Uses Tavily search API to find competitors based on the business profile.
Outputs a list of competitors with name, URL, and description.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "workflows" / "config"
TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)


def load_business_profile():
    """Load the business profile from config."""
    profile_path = CONFIG_DIR / "business_profile.json"
    if not profile_path.exists():
        print("ERROR: Business profile not found. Run setup_profile.py first.")
        sys.exit(1)
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_search_queries(profile):
    """Build search queries from the business profile to find competitors."""
    queries = []
    industry = profile.get("industry", "")
    offerings = profile.get("offerings", [])
    keywords = profile.get("keywords", [])
    target = profile.get("target_audience", "")

    # Primary query: direct competitor search
    if industry:
        queries.append(f"top companies in {industry} industry competitors")
        queries.append(f"best {industry} companies 2025 2026")

    # Offering-based queries
    for offering in offerings[:3]:  # Limit to top 3 offerings
        queries.append(f"best {offering} providers competitors")

    # Keyword-based queries
    for keyword in keywords[:2]:
        queries.append(f"{keyword} market leaders competitors")

    # Audience-based query
    if target and industry:
        queries.append(f"{industry} solutions for {target}")

    return queries[:6]  # Cap at 6 queries to stay within free tier


def discover_competitors(profile, max_competitors=10):
    """Search for competitors using Tavily API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY not found in .env")
        sys.exit(1)

    client = TavilyClient(api_key=api_key)
    queries = build_search_queries(profile)
    
    if not queries:
        print("ERROR: Business profile is incomplete — need industry, offerings, or keywords.")
        sys.exit(1)

    print(f"Running {len(queries)} search queries...")
    
    all_results = []
    seen_urls = set()

    for query in queries:
        print(f"  Searching: {query}")
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True
            )
            for result in response.get("results", []):
                url = result.get("url", "")
                # Deduplicate by domain
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace("www.", "")
                
                # Skip our own website
                own_site = profile.get("website", "")
                own_domain = urlparse(own_site).netloc.replace("www.", "") if own_site else ""
                
                if domain and domain not in seen_urls and domain != own_domain:
                    seen_urls.add(domain)
                    all_results.append({
                        "name": result.get("title", "").split(" - ")[0].split(" | ")[0].strip(),
                        "url": url,
                        "domain": domain,
                        "description": result.get("content", "")[:300],
                        "search_query": query
                    })
        except Exception as e:
            print(f"  Warning: Search failed for '{query}': {e}")
            continue

    # Limit to max_competitors
    competitors = all_results[:max_competitors]
    
    # Save results
    output_path = TMP_DIR / "competitors_raw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "business": profile.get("name", "Unknown"),
            "total_found": len(competitors),
            "competitors": competitors
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nFound {len(competitors)} competitors. Saved to {output_path}")
    return competitors


def main():
    profile = load_business_profile()
    competitors = discover_competitors(profile)
    
    print("\n--- Discovered Competitors ---")
    for i, comp in enumerate(competitors, 1):
        print(f"  {i}. {comp['name']}")
        print(f"     {comp['domain']}")
        print(f"     {comp['description'][:100]}...")
        print()


if __name__ == "__main__":
    main()
