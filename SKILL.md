---
name: url-capability-analyzer
description: Analyze a URL pointing to an MCP or Skill, compare with locally installed capabilities (across all common AI Agents), detect overlaps, suggest synergies, and recommend whether to install.
---

# URL Capability Analyzer

This skill automatically fetches and analyzes any MCP or Skill webpage, then compares it against all Skills and MCPs you have installed locally (from OpenCode, Claude Code, Cursor, OpenClaw, Qcalw, Continue, Cline, GitHub Copilot, Aider, etc.).

## Usage

Just send a URL to the agent:
Analyze this MCP: https://example.com/mcp-server

The skill will output a structured Markdown report containing:

- **Target introduction** (name, type, description)
- **Overlap analysis** (table of local capabilities with similarity scores)
- **Synergy possibilities** (how target could work with existing tools)
- **Installation recommendation** (with ready-to-run commands)

## Requirements

- Python 3.8+
- Install dependencies: `pip install requests beautifulsoup4 scikit-learn`
- (Optional) For better semantic matching, set `OPENAI_API_KEY` or `LOCAL_EMBEDDING` environment variable.

## Implementation

See the full open-source project at: https://github.com/yourusername/url-capability-analyzer