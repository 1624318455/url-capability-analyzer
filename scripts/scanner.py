import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

class LocalScanner:
    """Scans all known AI Agent directories for installed Skills and MCPs."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "agent_paths.json"
        self.agents = self._load_agent_paths(config_path)

    def _load_agent_paths(self, config_path: Path) -> Dict[str, Dict[str, str]]:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Expand '~' to user home
        expanded = {}
        for agent, paths in data.items():
            expanded[agent] = {
                "skills": str(Path(paths["skills"]).expanduser()),
                "mcps": str(Path(paths["mcps"]).expanduser())
            }
        return expanded

    def scan_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return {'skills': [...], 'mcps': [...]}"""
        skills = []
        mcps = []
        for agent, paths in self.agents.items():
            skills += self._scan_skills(agent, Path(paths["skills"]))
            mcps += self._scan_mcps(agent, Path(paths["mcps"]))
        return {"skills": skills, "mcps": mcps}

    def _scan_skills(self, agent: str, skills_dir: Path) -> List[Dict[str, Any]]:
        if not skills_dir.exists():
            return []
        result = []
        for item in skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skill_md = item / "SKILL.md"
                content = skill_md.read_text(encoding='utf-8', errors='ignore')
                name = item.name
                description = self._extract_description(content)
                result.append({
                    "name": name,
                    "type": "skill",
                    "agent": agent,
                    "path": str(item),
                    "description": description,
                    "raw_content": content
                })
        return result

    def _scan_mcps(self, agent: str, mcps_dir: Path) -> List[Dict[str, Any]]:
        if not mcps_dir.exists():
            return []
        result = []
        # Look for .json files or subfolders with config.json
        for item in mcps_dir.iterdir():
            if item.is_file() and item.suffix == ".json":
                data = self._safe_load_json(item)
                if data:
                    result.append(self._mcp_from_json(agent, item, data))
            elif item.is_dir() and (item / "config.json").exists():
                data = self._safe_load_json(item / "config.json")
                if data:
                    result.append(self._mcp_from_json(agent, item, data))
        return result

    def _safe_load_json(self, path: Path) -> Optional[Dict]:
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except:
            return None

    def _mcp_from_json(self, agent: str, path: Path, data: Dict) -> Dict[str, Any]:
        return {
            "name": data.get("name", path.stem),
            "type": "mcp",
            "agent": agent,
            "path": str(path),
            "description": data.get("description", ""),
            "tools": data.get("tools", []),  # list of tool names
            "raw_content": json.dumps(data)
        }

    def _extract_description(self, content: str) -> str:
        lines = content.splitlines()
        in_frontmatter = False
        for i, line in enumerate(lines):
            if i == 0 and line.strip() == "---":
                in_frontmatter = True
                continue
            if in_frontmatter and line.strip() == "---":
                break
            if in_frontmatter and line.strip().startswith("description:"):
                return line.split("description:", 1)[1].strip()
        # fallback: first 200 chars
        return content[:200].replace("\n", " ")