# URL Capability Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**A smart tool that analyzes any MCP or Skill URL and compares it with your locally installed capabilities.**

## Two Modes

### 1. CLI Mode (Python Script)
```bash
python scripts/analyze.py https://github.com/user/awesome-skill
```

### 2. MCP Server Mode (Recommended for OpenCode)
Run as an MCP server for seamless integration with OpenCode through natural language.

## MCP Server Installation

### OpenCode Configuration

Add to your `opencode.json`:

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

Or use `npx` directly:

```json
{
  "mcp": {
    "capability-analyzer": {
      "command": ["npx", "-y", "url-capability-analyzer"],
      "enabled": true
    }
  }
}
```

### npm Installation (Alternative)

```bash
npm install -g url-capability-analyzer
```

Then configure in your agent:

```json
{
  "mcp": {
    "capability-analyzer": {
      "command": ["url-capability-analyzer"],
      "enabled": true
    }
  }
}
```

## MCP Server Tools

When running as MCP server, you get these tools:

| Tool | Description |
|------|-------------|
| `analyze_capability` | Analyze a URL and compare with local capabilities |
| `list_local_capabilities` | List all installed Skills and MCP servers |
| `compare_urls` | Compare multiple URLs for overlap |

### Usage Examples (Natural Language)

```
"帮我分析这个MCP有没有重复：https://github.com/different-ai/opencode-scheduler"

"对比这两个工具：https://... 和 https://..."

"我需要哪些定时任务的MCP？列出本地已安装的"
```

## Features

- 🌐 **Fetches and parses** any MCP/Skill webpage (using `requests` + `BeautifulSoup`)
- 🔍 **Scans all common AI Agents** default directories to discover installed Skills & MCPs
- 🧠 **Intelligent overlap detection** using TF‑IDF cosine similarity (optional LLM/embedding)
- 🔗 **Synergy analysis** – suggests how the new capability could work with existing ones
- 📝 **Structured Markdown report** with clear recommendations
- ⚙️ **Extensible** – add custom paths, switch to semantic matching with OpenAI or local models

## Supported Agents (auto‑detected)

| Agent | Skill Path | MCP Path |
|-------|------------|----------|
| OpenCode | `~/.config/opencode/skills` | `~/.config/opencode/mcp_servers` |
| Claude Code | `~/.claude/skills` | `~/.claude/mcp_servers` |
| Cursor | `~/.cursor/skills` | `~/.cursor/mcp_servers` |
| OpenClaw | `~/.openclaw/skills` | `~/.openclaw/mcp_servers` |
| Qcalw | `~/.qcalw/skills` | `~/.qcalw/mcp_servers` |
| Continue | `~/.continue/skills` | `~/.continue/mcp_servers` |
| Cline | `~/.cline/skills` | `~/.cline/mcp_servers` |
| GitHub Copilot | `~/.github-copilot/skills` | `~/.github-copilot/mcp_servers` |
| Aider | `~/.aider/skills` | `~/.aider/mcp_servers` |

*You can add custom paths in `config/agent_paths.json`.*

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/1624318455/url-capability-analyzer.git
cd url-capability-analyzer
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install as a skill for your AI Agent

- **OpenCode**: Copy the whole folder to `~/.config/opencode/skills/url-capability-analyzer/`
- **Claude Code**: Copy to `~/.claude/skills/url-capability-analyzer/`
- **Other agents**: Refer to their skill installation docs.

### 4. (Optional) Enable advanced semantic matching

Set an environment variable:

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# Or for a local embedding model (sentence-transformers)
export LOCAL_EMBEDDING="all-MiniLM-L6-v2"
```

## Usage

Once installed, simply ask your agent:

```text
Analyze this Skill: https://github.com/user/awesome-skill
```

The agent will run the skill and return a report.

### Command Line Usage

```bash
# Basic analysis
python scripts/analyze.py https://github.com/user/some-skill

# Save report to file
python scripts/analyze.py https://github.com/user/some-skill --output report.md

# Use embedding models (requires sentence-transformers)
python scripts/analyze.py https://github.com/user/some-skill --embedding
```

## Output Report Example

The generated report includes:

```markdown
# 🔍 Capability Analysis Report

**Generated:** 2024-04-02 10:30:00

## 📦 Target: example-skill (skill)

- **URL:** https://github.com/user/example-skill
- **Description:** This skill provides example functionality for testing...

---

## 🔄 Overlap with Local Capabilities

| Local Capability | Type | Agent   | Similarity | Level  | Reason |
|------------------|------|---------|------------|--------|--------|
| test-skill       | skill| opencode| 0.92       | high   | Likely duplicate functionality |
| another-skill    | skill| cursor  | 0.65       | partial| Partial functional overlap |

---

## 🤝 Synergy Possibilities

- **web-scraper** (skill): Target retrieves data → web-scraper can send/notify
- **data-processor** (mcp): Target searches → data-processor can analyze results

---

## 💡 Recommendation

**❌ Do not install**

*Reason: High overlap with existing capability*

---

## 🚀 Installation Command (if applicable)
git clone https://github.com/user/example-skill ~/.config/opencode/skills/example-skill
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI API key for semantic matching
OPENAI_API_KEY=your_key_here

# Local embedding model (overrides OpenAI if set)
LOCAL_EMBEDDING=all-MiniLM-L6-v2

# Custom skills directory (overrides default scan paths)
SKILLS_DIR=/path/to/custom/skills
```

### Agent Paths Configuration

Edit `config/agent_paths.json` to add custom AI agent directories:

```json
{
  "my-agent": {
    "skills": "~/.my-agent/skills",
    "mcps": "~/.my-agent/mcp_servers"
  }
}
```

## Directory Structure

```
url-capability-analyzer/
├── .github/workflows/test.yml    # CI configuration
├── config/                       # Configuration files
│   └── agent_paths.json          # AI agent directory mappings
├── scripts/                      # Core Python modules
│   ├── analyze.py                # Main analysis script
│   ├── scanner.py                # Local capability scanner
│   ├── matcher.py                # Similarity and synergy analysis
│   ├── report.py                 # Report generation
│   └── utils.py                  # Webpage fetching utilities
├── server.py                     # MCP server entry point
├── package.json                  # npm package configuration
├── templates/                    # Report templates
│   └── report_template.md        # Markdown report template
├── tests/                        # Unit tests
│   ├── test_scanner.py           # Scanner tests
│   └── fixtures/                 # Test fixtures
├── SKILL.md                      # Skill definition
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
└── LICENSE                       # MIT License
```

## Development

### Run tests

```bash
pytest tests/
```

### Add a new agent path

Edit `config/agent_paths.json` and append:

```json
{
  "my-agent": {
    "skills": "~/.my-agent/skills",
    "mcps": "~/.my-agent/mcp_servers"
  }
}
```

## License

MIT

## Contributing

Issues and pull requests are welcome!