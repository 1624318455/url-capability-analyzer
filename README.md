# URL Capability Analyzer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**A smart skill for AI agents (OpenCode, Claude Code, Cursor, etc.) that automatically analyzes any MCP or Skill URL and compares it with your locally installed capabilities.**

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
git clone https://github.com/yourusername/url-capability-analyzer.git
cd url-capability-analyzer
2. Install Python dependencies
bash
pip install -r requirements.txt
3. Install as a skill for your AI Agent
OpenCode: Copy the whole folder to ~/.config/opencode/skills/url-capability-analyzer/

Claude Code: Copy to ~/.claude/skills/url-capability-analyzer/

Other agents: Refer to their skill installation docs.

4. (Optional) Enable advanced semantic matching
Set an environment variable:

bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# Or for a local embedding model (sentence-transformers)
export LOCAL_EMBEDDING="all-MiniLM-L6-v2"
Usage
Once installed, simply ask your agent:

text
Analyze this Skill: https://github.com/user/awesome-skill
The agent will run the skill and return a report.

Development
Run tests
bash
pytest tests/
Add a new agent path
Edit config/agent_paths.json and append:

json
{
  "my-agent": {
    "skills": "~/.my-agent/skills",
    "mcps": "~/.my-agent/mcp_servers"
  }
}
License
MIT

Contributing
Issues and pull requests are welcome!