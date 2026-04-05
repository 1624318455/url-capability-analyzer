---
name: url-capability-analyzer
description: Analyze a URL pointing to an MCP or Skill, compare with locally installed capabilities, detect overlaps, suggest synergies, and recommend whether to install.
---

# URL Capability Analyzer

Analyzes any MCP or Skill URL and compares it with your locally installed capabilities.

## Recommended: MCP Mode

Configure in your agent's `opencode.json`:

```json
{
  "mcp": {
    "capability-analyzer": {
      "command": ["python", "path/to/url-capability-analyzer/server.py"],
      "enabled": true
    }
  }
}
```

Then just describe what you need:

```
"帮我分析这个MCP有没有重复：https://github.com/different-ai/opencode-scheduler"
"我需要定时任务MCP，哪个适合我？"
```

## Fallback: CLI Mode

```bash
python scripts/analyze.py https://github.com/xxx/yyy
```

## Requirements

- Python 3.8+
- `pip install requests beautifulsoup4 scikit-learn`

## Repository

https://github.com/1624318455/url-capability-analyzer