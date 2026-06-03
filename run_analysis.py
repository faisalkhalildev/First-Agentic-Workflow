"""
Competitor Analysis — Full Pipeline Runner
===========================================
Runs all phases of the competitor analysis workflow in sequence.
Can also run individual phases if specified.

Usage:
    python run_analysis.py              # Run full pipeline
    python run_analysis.py discover     # Phase 2 only
    python run_analysis.py research     # Phase 3 only
    python run_analysis.py analyze      # Phase 4 only
    python run_analysis.py pdf          # Phase 5 only
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "workflows" / "config"


def check_prerequisites():
    """Verify all required files and config exist."""
    issues = []
    
    # Check business profile
    profile_path = CONFIG_DIR / "business_profile.json"
    if not profile_path.exists():
        issues.append("Missing: workflows/config/business_profile.json")
    else:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        if not profile.get("industry"):
            issues.append("Business profile: 'industry' is empty")
        if not profile.get("offerings"):
            issues.append("Business profile: 'offerings' is empty")
    
    # Check brand config
    if not (CONFIG_DIR / "brand_config.json").exists():
        issues.append("Missing: workflows/config/brand_config.json")
    
    # Check logo
    if not (CONFIG_DIR / "logo.png").exists():
        issues.append("Missing: workflows/config/logo.png")
    
    # Check .env
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    if not os.getenv("TAVILY_API_KEY"):
        issues.append("Missing in .env: TAVILY_API_KEY")
    if not os.getenv("GOOGLE_API_KEY"):
        issues.append("Missing in .env: GOOGLE_API_KEY")
    
    return issues


def run_phase(phase_name):
    """Run a specific phase."""
    if phase_name == "discover":
        from tools.discover_competitors import main
        main()
    elif phase_name == "research":
        from tools.research_competitor import main
        main()
    elif phase_name == "analyze":
        from tools.generate_analysis import main
        main()
    elif phase_name == "pdf":
        from tools.generate_pdf import main
        main()
    else:
        print(f"Unknown phase: {phase_name}")
        print("Valid phases: discover, research, analyze, pdf")
        sys.exit(1)


def run_full_pipeline():
    """Run the complete competitor analysis pipeline."""
    print("=" * 60)
    print("   COMPETITOR ANALYSIS - FULL PIPELINE")
    print("=" * 60)
    
    # Prerequisites check
    print("\n[PRE-CHECK] Verifying prerequisites...")
    issues = check_prerequisites()
    if issues:
        print("\n[FAIL] Cannot proceed. Fix these issues first:\n")
        for issue in issues:
            print(f"  - {issue}")
        print()
        sys.exit(1)
    print("  [OK] All prerequisites met.\n")
    
    # Phase 2: Discover
    print("=" * 60)
    print("  PHASE 2: Competitor Discovery")
    print("=" * 60)
    from tools.discover_competitors import main as discover_main
    discover_main()
    
    # Phase 3: Research
    print("\n" + "=" * 60)
    print("  PHASE 3: Deep Research")
    print("=" * 60)
    from tools.research_competitor import main as research_main
    research_main()
    
    # Phase 4: Analysis
    print("\n" + "=" * 60)
    print("  PHASE 4: Analysis & Insights")
    print("=" * 60)
    from tools.generate_analysis import main as analysis_main
    analysis_main()
    
    # Phase 5: PDF
    print("\n" + "=" * 60)
    print("  PHASE 5: Branded PDF Generation")
    print("=" * 60)
    from tools.generate_pdf import main as pdf_main
    pdf_main()
    
    print("\n" + "=" * 60)
    print("  [OK] PIPELINE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_phase(sys.argv[1])
    else:
        run_full_pipeline()
