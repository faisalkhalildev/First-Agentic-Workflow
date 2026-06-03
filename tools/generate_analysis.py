"""
Analysis & Insights Generator
==============================
Takes researched competitor data and the business profile,
produces a structured comparative analysis with actionable insights.
Uses OpenAI to generate the strategic analysis.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "workflows" / "config"
TMP_DIR = ROOT / ".tmp"
TMP_DIR.mkdir(exist_ok=True)


def load_researched_competitors():
    """Load the researched competitor data from Phase 3."""
    path = TMP_DIR / "competitors_researched.json"
    if not path.exists():
        print("ERROR: competitors_researched.json not found. Run research_competitor.py first.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_business_profile():
    """Load the business profile."""
    path = CONFIG_DIR / "business_profile.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_analysis(profile, competitor_data):
    """Use Gemini (via OpenAI-compatible endpoint) to produce a comprehensive competitive analysis report."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai")
    competitors = competitor_data.get("competitors", [])

    # Filter out any competitors that failed research (have an "error" key)
    valid_competitors = [c for c in competitors if isinstance(c, dict) and "error" not in c]
    errored = len(competitors) - len(valid_competitors)
    if errored:
        print(f"  Note: Skipping {errored} competitor(s) that had research errors.")
    if not valid_competitors:
        print("ERROR: No valid competitor data found. Re-run research phase.")
        sys.exit(1)

    # Build competitor summaries for the prompt
    comp_summaries = ""
    for i, comp in enumerate(valid_competitors, 1):
        if isinstance(comp, dict) and "error" not in comp:
            comp_summaries += f"""
--- Competitor {i}: {comp.get('company_name', 'Unknown')} ---
Website: {comp.get('website', 'N/A')}
Overview: {comp.get('overview', 'N/A')}
Products/Services: {json.dumps(comp.get('products_services', []))}
Pricing: {comp.get('pricing_model', 'Unknown')}
Target Audience: {comp.get('target_audience', 'N/A')}
Messaging: {comp.get('key_messaging', 'N/A')}
Strengths: {json.dumps(comp.get('strengths', []))}
Weaknesses: {json.dumps(comp.get('weaknesses', []))}
Differentiators: {json.dumps(comp.get('unique_differentiators', []))}
Threat Level: {comp.get('threat_level', 'N/A')}
Opportunities: {json.dumps(comp.get('opportunities_for_us', []))}
"""

    prompt = f"""You are a senior competitive intelligence strategist. Produce a comprehensive competitive analysis report.

OUR BUSINESS:
- Name: {profile.get('name', 'N/A')}
- Industry: {profile.get('industry', 'N/A')}
- Website: {profile.get('website', 'N/A')}
- Offerings: {json.dumps(profile.get('offerings', []))}
- Target Audience: {profile.get('target_audience', 'N/A')}
- Differentiators: {json.dumps(profile.get('differentiators', []))}

COMPETITOR DATA:
{comp_summaries}

Generate a JSON report with this EXACT structure:
{{
    "report_title": "Competitive Analysis Report — [Business Name]",
    "generated_date": "YYYY-MM-DD",
    "executive_summary": "3-4 paragraph executive summary covering the competitive landscape, key findings, and top recommendations",
    "market_overview": {{
        "landscape_description": "2-3 paragraphs about the overall market",
        "market_trends": ["list of 4-6 current market trends"],
        "market_size_signals": "any indicators about market size or growth"
    }},
    "competitor_profiles": [
        {{
            "name": "string",
            "website": "string",
            "overview": "string",
            "products_services": ["list"],
            "pricing_model": "string",
            "target_audience": "string",
            "strengths": ["list"],
            "weaknesses": ["list"],
            "threat_level": "low/medium/high",
            "key_takeaway": "one sentence summarizing what we should learn from them"
        }}
    ],
    "comparison_matrix": {{
        "categories": ["list of comparison categories like Pricing, Features, UX, etc."],
        "ratings": {{
            "competitor_name": {{
                "category": "strong / moderate / weak"
            }}
        }}
    }},
    "strategic_insights": {{
        "our_strengths": ["things we do better than competitors"],
        "areas_to_improve": ["specific areas where competitors outperform us"],
        "market_gaps": ["underserved needs or segments no one is addressing well"],
        "threats": ["competitive threats we should monitor"],
        "quick_wins": ["easy improvements we can make immediately"],
        "long_term_plays": ["strategic initiatives for the next 6-12 months"]
    }},
    "action_items": [
        {{
            "priority": "high/medium/low",
            "action": "specific action to take",
            "rationale": "why this matters",
            "effort": "low/medium/high"
        }}
    ]
}}

Return ONLY valid JSON. Be specific, data-driven, and actionable."""

    print("Generating comprehensive analysis with AI...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": "You are a senior competitive intelligence strategist. Return only valid JSON. Be thorough and specific."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=8000
            )
            result_text = response.choices[0].message.content
            if result_text is None:
                print(f"  Warning: AI returned empty response (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                    continue
                print("ERROR: AI returned empty response after retries")
                sys.exit(1)
            result_text = result_text.strip()
            # Clean potential markdown wrapping
            if result_text.startswith("```"):
                result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            
            analysis = json.loads(result_text)
            
            # Save analysis
            output_path = TMP_DIR / "analysis_report.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"Analysis complete. Saved to {output_path}")
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"  Warning: AI returned invalid JSON (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(5)
                continue
            # Save raw output for debugging
            error_path = TMP_DIR / "analysis_raw_output.txt"
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(result_text)
            print(f"Raw output saved to {error_path}")
            sys.exit(1)
        except Exception as e:
            print(f"  Warning: Analysis generation failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(5)
                continue
            print(f"ERROR: Analysis generation failed after retries: {e}")
            sys.exit(1)


def main():
    profile = load_business_profile()
    competitor_data = load_researched_competitors()
    analysis = generate_analysis(profile, competitor_data)
    
    # Print summary
    print("\n" + "=" * 50)
    print("ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Report: {analysis.get('report_title', 'N/A')}")
    print(f"Competitors analyzed: {len(analysis.get('competitor_profiles', []))}")
    print(f"Action items: {len(analysis.get('action_items', []))}")
    
    insights = analysis.get("strategic_insights", {})
    print(f"\nQuick wins identified: {len(insights.get('quick_wins', []))}")
    print(f"Market gaps found: {len(insights.get('market_gaps', []))}")
    print(f"Threats to monitor: {len(insights.get('threats', []))}")


if __name__ == "__main__":
    main()
