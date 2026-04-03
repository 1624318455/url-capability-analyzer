#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

from scanner import LocalScanner
from matcher import Matcher
from report import ReportGenerator
from utils import fetch_webpage_info

def main():
    parser = argparse.ArgumentParser(description="Analyze MCP/Skill URL against local capabilities")
    parser.add_argument("url", help="URL of the MCP or Skill webpage")
    parser.add_argument("--output", "-o", help="Output report file (default: stdout)")
    parser.add_argument("--embedding", action="store_true", help="Use sentence-transformers for matching (requires extra dependencies)")
    parser.add_argument("--browser", "-b", action="store_true", help="Use headless browser for dynamic pages (requires Playwright)")
    parser.add_argument("--no-emoji", action="store_true", help="Disable emoji in output (for Windows console)")
    args = parser.parse_args()

    # 1. Fetch target info
    print(f"Fetching {args.url} ...", file=sys.stderr)
    try:
        target = fetch_webpage_info(args.url, use_headless_browser=args.browser)
        print(f"Fetched successfully. Title: {target.get('name', 'Unknown')}", file=sys.stderr)
    except Exception as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        target = {
            "name": "Unknown",
            "type": "unknown",
            "url": args.url,
            "description": "Failed to fetch page content",
            "full_text": "",
            "github_url": None
        }

    # 2. Scan local capabilities
    print("Scanning local Skills and MCPs...", file=sys.stderr)
    scanner = LocalScanner()
    local_all = scanner.scan_all()
    local_list = local_all["skills"] + local_all["mcps"]
    print(f"Found {len(local_list)} local capabilities", file=sys.stderr)

    # 3. Matching
    print("Analyzing overlaps and synergies...", file=sys.stderr)
    try:
        matcher = Matcher(use_embedding=args.embedding)
        overlap = matcher.analyze_overlap(target, local_list)
        synergy = matcher.analyze_synergy(target, local_list)
        recommendation, reason = matcher.suggest_install(overlap, synergy)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        overlap = []
        synergy = []
        recommendation = "Analysis failed"
        reason = str(e)

    # 4. Generate report
    report_gen = ReportGenerator(use_emoji=not args.no_emoji)
    report = report_gen.generate(target, overlap, synergy, recommendation, reason)

    # 5. Output
    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        # Try to print, but handle encoding errors gracefully
        try:
            print(report)
        except UnicodeEncodeError:
            # Fallback: save to file
            fallback_file = Path("analysis_report.md")
            fallback_file.write_text(report, encoding='utf-8')
            print(f"Report saved to {fallback_file} (console output failed due to encoding)", file=sys.stderr)

if __name__ == "__main__":
    main()
