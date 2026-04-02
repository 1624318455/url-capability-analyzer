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
    args = parser.parse_args()

    # 1. Fetch target info
    print(f"Fetching {args.url} ...", file=sys.stderr)
    target = fetch_webpage_info(args.url)

    # 2. Scan local capabilities
    print("Scanning local Skills and MCPs...", file=sys.stderr)
    scanner = LocalScanner()
    local_all = scanner.scan_all()
    local_list = local_all["skills"] + local_all["mcps"]

    # 3. Matching
    print("Analyzing overlaps and synergies...", file=sys.stderr)
    matcher = Matcher(use_embedding=args.embedding)
    overlap = matcher.analyze_overlap(target, local_list)
    synergy = matcher.analyze_synergy(target, local_list)
    recommendation, reason = matcher.suggest_install(overlap, synergy)

    # 4. Generate report
    report_gen = ReportGenerator()
    report = report_gen.generate(target, overlap, synergy, recommendation, reason)

    # 5. Output
    if args.output:
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(report)

if __name__ == "__main__":
    main()