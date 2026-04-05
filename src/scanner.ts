import { glob } from "glob";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

export interface LocalCapability {
  name: string;
  type: "skill" | "mcp";
  agent: string;
  path: string;
  description?: string;
}

// Common AI agent paths
const AGENT_PATHS: Record<string, { skills: string; mcps: string }> = {
  opencode: {
    skills: "~/.config/opencode/skills",
    mcps: "~/.config/opencode/mcp_servers",
  },
  "claude-code": {
    skills: "~/.claude/skills",
    mcps: "~/.claude/mcp_servers",
  },
  cursor: {
    skills: "~/.cursor/skills",
    mcps: "~/.cursor/mcp_servers",
  },
  openclaw: {
    skills: "~/.openclaw/skills",
    mcps: "~/.openclaw/mcp_servers",
  },
};

function expandTilde(filepath: string): string {
  if (filepath.startsWith("~/")) {
    return path.join(os.homedir(), filepath.slice(2));
  }
  return filepath;
}

async function scanSkillsDir(dirPath: string, agent: string): Promise<LocalCapability[]> {
  const results: LocalCapability[] = [];
  
  try {
    const expandedPath = expandTilde(dirPath);
    
    if (!fs.existsSync(expandedPath)) {
      return results;
    }

    const entries = fs.readdirSync(expandedPath, { withFileTypes: true });
    
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      
      const skillPath = path.join(expandedPath, entry.name);
      const skillMdPath = path.join(skillPath, "SKILL.md");
      
      let description = "";
      if (fs.existsSync(skillMdPath)) {
        try {
          const content = fs.readFileSync(skillMdPath, "utf-8");
          // Extract description from frontmatter
          const descMatch = content.match(/description:\s*(.+)/);
          if (descMatch) {
            description = descMatch[1].trim();
          }
        } catch {
          // Ignore errors
        }
      }

      results.push({
        name: entry.name,
        type: "skill",
        agent,
        path: skillPath,
        description,
      });
    }
  } catch (error) {
    console.error(`[url-capability-analyzer] Error scanning ${dirPath}:`, error);
  }

  return results;
}

async function scanMcpsDir(dirPath: string, agent: string): Promise<LocalCapability[]> {
  const results: LocalCapability[] = [];
  
  try {
    const expandedPath = expandTilde(dirPath);
    
    if (!fs.existsSync(expandedPath)) {
      return results;
    }

    const entries = fs.readdirSync(expandedPath, { withFileTypes: true });
    
    for (const entry of entries) {
      let mcpPath = "";
      let name = entry.name;
      
      if (entry.isDirectory()) {
        // Check for config.json in directory
        const configPath = path.join(expandedPath, entry.name, "config.json");
        if (fs.existsSync(configPath)) {
          mcpPath = configPath;
        }
      } else if (entry.isFile() && entry.name.endsWith(".json")) {
        mcpPath = path.join(expandedPath, entry.name);
      }

      if (mcpPath) {
        try {
          const content = fs.readFileSync(mcpPath, "utf-8");
          const config = JSON.parse(content);
          
          results.push({
            name: config.name || entry.name,
            type: "mcp",
            agent,
            path: mcpPath,
            description: config.description || "",
          });
        } catch {
          // Ignore errors
        }
      }
    }
  } catch (error) {
    console.error(`[url-capability-analyzer] Error scanning ${dirPath}:`, error);
  }

  return results;
}

export async function scanLocalCapabilities(): Promise<LocalCapability[]> {
  const results: LocalCapability[] = [];

  for (const [agent, paths] of Object.entries(AGENT_PATHS)) {
    const skills = await scanSkillsDir(paths.skills, agent);
    const mcps = await scanMcpsDir(paths.mcps, agent);
    
    results.push(...skills, ...mcps);
  }

  return results;
}