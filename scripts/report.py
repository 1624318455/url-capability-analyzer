from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

class ReportGenerator:
    def __init__(self, template_path=None, use_emoji: bool = None):
        """
        Initialize report generator.
        
        Args:
            template_path: Path to custom template file
            use_emoji: Whether to use emoji in report. 
                       None = auto-detect based on terminal encoding.
                       True = always use emoji.
                       False = never use emoji.
        """
        self._use_emoji = use_emoji
        self._template_path = template_path
        
        # Always use default template based on emoji setting
        # This ensures the use_emoji parameter is respected
        self.template = self._get_default_template()
    
    def _should_use_emoji(self) -> bool:
        """Determine if emoji should be used based on environment."""
        if self._use_emoji is not None:
            return self._use_emoji
        
        # Check if output is to a file
        if not sys.stdout.isatty():
            return True  # Assume file output supports UTF-8
        
        # Check Windows console encoding
        try:
            if sys.platform == 'win32':
                # Get console encoding
                import subprocess
                result = subprocess.run(['chcp'], capture_output=True, text=True)
                if '65001' in result.stdout:  # UTF-8 code page
                    return True
                return False  # GBK or other code page
        except:
            pass
        
        # Check environment variable
        env_emoji = os.environ.get('REPORT_USE_EMOJI', '').lower()
        if env_emoji in ('1', 'true', 'yes'):
            return True
        elif env_emoji in ('0', 'false', 'no'):
            return False
        
        # Default to emoji for file output, no emoji for console
        return True
    
    def _get_default_template(self) -> str:
        """Get default template based on emoji setting."""
        if self._should_use_emoji():
            return """# [SEARCH] Capability Analysis Report

**Generated:** {timestamp}

## [TARGET] Target: {target_name} ({target_type})

- **URL:** {target_url}
- **Description:** {target_desc}
- **GitHub:** {github_url}

---

## [OVERLAP] Overlap with Local Capabilities

{overlap_table}

---

## [SYNERGY] Synergy Possibilities

{synergy_list}

---

## [RECOMMEND] Recommendation

**{recommendation}**

*Reason: {reason}*

---

## [INSTALL] Installation Command (if applicable)
{install_command}

---
"""
        else:
            return """# Capability Analysis Report

**Generated:** {timestamp}

## Target: {target_name} ({target_type})

- **URL:** {target_url}
- **Description:** {target_desc}
- **GitHub:** {github_url}

---

## Overlap with Local Capabilities

{overlap_table}

---

## Synergy Possibilities

{synergy_list}

---

## Recommendation

**{recommendation}**

*Reason: {reason}*

---

## Installation Command (if applicable)
{install_command}

---
"""

    def generate(self, target: Dict, overlap: List[Dict], synergy: List[Dict],
                 recommendation: str, reason: str) -> str:
        # Replace emoji in recommendation text if not using emoji
        if not self._should_use_emoji():
            emoji_map = {
                "✅": "[OK]", "❌": "[NO]", "⚠️": "[WARN]",
                "🔍": "[SEARCH]", "📦": "[TARGET]", "🔄": "[OVERLAP]",
                "🤝": "[SYNERGY]", "💡": "[IDEA]", "🚀": "[ROCKET]",
                "→": "->"
            }
            for emoji, replacement in emoji_map.items():
                recommendation = recommendation.replace(emoji, replacement)
                reason = reason.replace(emoji, replacement)
        
        # Prepare overlap table
        if overlap:
            headers = ["Local Capability", "Type", "Agent", "Similarity", "Level", "Reason"]
            rows = [[
                o["local_name"],
                o["local_type"],
                o.get("agent", "?"),
                f"{o['similarity']:.2f}",
                o["level"],
                o["reason"]
            ] for o in overlap[:10]]  # show top 10
            overlap_table = self._markdown_table(headers, rows)
        else:
            overlap_table = "No local capabilities found."

        # Synergy list
        if synergy:
            synergy_list = "\n".join([f"- **{s['local_name']}** ({s['local_type']}): {s['description']}" for s in synergy])
        else:
            synergy_list = "No obvious synergy detected."

        # Install command example
        github_url = target.get('github_url')
        if github_url:
            install_cmd = f"git clone {github_url}\n# Or use MCP directly if available"
        else:
            install_cmd = f"# No git repository found. Visit: {target.get('url', '#')}"

        # Get GitHub URL for display
        github_url_display = github_url if github_url else "Not found in page"

        return self.template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_name=target.get("name", "Unknown"),
            target_type=target.get("type", "unknown"),
            target_url=target.get("url", ""),
            target_desc=target.get("description", "")[:500],
            github_url=github_url_display,
            overlap_table=overlap_table,
            synergy_list=synergy_list,
            recommendation=recommendation,
            reason=reason,
            install_command=install_cmd
        )

    def _markdown_table(self, headers: List[str], rows: List[List]) -> str:
        if not rows:
            return "No data"
        col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        sep_line = "|-" + "-|-".join("-" * col_widths[i] for i in range(len(headers))) + "-|"
        body_lines = ["| " + " | ".join(str(r[i]).ljust(col_widths[i]) for i in range(len(headers))) + " |" for r in rows]
        return "\n".join([header_line, sep_line] + body_lines)
