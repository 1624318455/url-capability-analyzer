from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class ReportGenerator:
    def __init__(self, template_path=None):
        if template_path is None:
            template_path = Path(__file__).parent.parent / "templates" / "report_template.md"
        self.template = template_path.read_text(encoding='utf-8') if template_path.exists() else self._default_template()

    def _default_template(self) -> str:
        return """# 🔍 Capability Analysis Report

**Generated:** {timestamp}

## 📦 Target: {target_name} ({target_type})

- **URL:** {target_url}
- **Description:** {target_desc}

---

## 🔄 Overlap with Local Capabilities

{overlap_table}

---

## 🤝 Synergy Possibilities

{synergy_list}

---

## 💡 Recommendation

**{recommendation}**

*Reason: {reason}*

---

## 🚀 Installation Command (if applicable)
{install_command}

text
"""

    def generate(self, target: Dict, overlap: List[Dict], synergy: List[Dict],
                 recommendation: str, reason: str) -> str:
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
        install_cmd = f"git clone {target.get('url', '#')} ~/.config/opencode/skills/{target.get('name', 'new-skill').replace(' ', '_')}"

        return self.template.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            target_name=target.get("name", "Unknown"),
            target_type=target.get("type", "unknown"),
            target_url=target.get("url", ""),
            target_desc=target.get("description", "")[:300],
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