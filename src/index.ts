#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  InitializeRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { fetchWebpageInfo, type WebpageInfo } from "./webfetch.js";
import { scanLocalCapabilities, type LocalCapability } from "./scanner.js";
import { analyzeOverlap, suggestInstall, type AnalysisResult } from "./matcher.js";

const server = new Server(
  {
    name: "url-capability-analyzer",
    version: "2.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Store local capabilities in memory
let localCapabilities: LocalCapability[] = [];

// Initialize: scan local capabilities
async function initCapabilities() {
  try {
    localCapabilities = await scanLocalCapabilities();
    console.error(`[url-capability-analyzer] Loaded ${localCapabilities.length} local capabilities`);
  } catch (error) {
    console.error("[url-capability-analyzer] Failed to scan local capabilities:", error);
    localCapabilities = [];
  }
}

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  const args = request.params.arguments as Record<string, unknown> || {};

  try {
    if (name === "analyze_capability") {
      const url = args.url as string;
      const useBrowser = args.use_browser as boolean | undefined;
      
      if (!url) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: "URL is required" }, null, 2),
            },
          ],
        };
      }

      // Fetch target info
      let target: WebpageInfo;
      try {
        target = await fetchWebpageInfo(url, useBrowser);
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: `Failed to fetch URL: ${error}` },
                null,
                2
              ),
            },
          ],
        };
      }

      // Analyze
      const result: AnalysisResult = analyzeOverlap(target, localCapabilities);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                target: {
                  name: target.name,
                  type: target.type,
                  url: target.url,
                  description: target.description?.slice(0, 500),
                  tools: target.tools,
                  author: target.author,
                  language: target.language,
                },
                local_capabilities_count: localCapabilities.length,
                overlap: result.overlap.slice(0, 5),
                synergy: result.synergy.slice(0, 3),
                recommendation: result.recommendation,
                reason: result.reason,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "list_local_capabilities") {
      const agentFilter = args.agent as string | undefined;
      const typeFilter = args.type as string | undefined;

      let results = localCapabilities;
      if (agentFilter) {
        results = results.filter((r) => r.agent === agentFilter);
      }
      if (typeFilter) {
        results = results.filter((r) => r.type === typeFilter);
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                total: results.length,
                capabilities: results.slice(0, 50).map((r) => ({
                  name: r.name,
                  type: r.type,
                  agent: r.agent,
                  description: r.description?.slice(0, 200),
                })),
              },
              null,
              2
            ),
          },
        ],
      };
    }

    if (name === "compare_urls") {
      const urls = args.urls as string[];

      if (!urls || urls.length < 2) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                { error: "At least 2 URLs are required for comparison" },
                null,
                2
              ),
            },
          ],
        };
      }

      const targets: WebpageInfo[] = [];
      for (const url of urls) {
        try {
          const target = await fetchWebpageInfo(url, false);
          targets.push(target);
        } catch {
          targets.push({ 
            name: "Error", 
            url, 
            type: "unknown", 
            description: `Failed to fetch: ${url}`,
            tools: [],
            install_methods: [],
            tags: []
          });
        }
      }

      // Simple pairwise comparison using name + description similarity
      const comparisons: any[] = [];
      for (let i = 0; i < targets.length; i++) {
        for (let j = i + 1; j < targets.length; j++) {
          const text1 = `${targets[i].name} ${targets[i].description || ""}`;
          const text2 = `${targets[j].name} ${targets[j].description || ""}`;
          const sim = cosineSimilarity(text1, text2);
          comparisons.push({
            url1: urls[i],
            url2: urls[j],
            name1: targets[i].name,
            name2: targets[j].name,
            similarity: Math.round(sim * 1000) / 1000,
          });
        }
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                urls,
                targets: targets.map((t) => ({ name: t.name, type: t.type, url: t.url })),
                comparisons,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: `Unknown tool: ${name}` }, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            { error: `Tool execution error: ${error}` },
            null,
            2
          ),
        },
      ],
    };
  }
});

// Simple cosine similarity for text
function cosineSimilarity(text1: string, text2: string): number {
  const words1 = new Set(text1.toLowerCase().split(/\s+/).filter(Boolean));
  const words2 = new Set(text2.toLowerCase().split(/\s+/).filter(Boolean));
  const intersection = new Set([...words1].filter((x) => words2.has(x)));
  if (intersection.size === 0) return 0;
  const union = new Set([...words1, ...words2]);
  return intersection.size / union.size;
}

// Handle tool list
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "analyze_capability",
        description:
          "Analyze a URL pointing to an MCP or Skill, compare with locally installed capabilities, detect overlaps, and recommend whether to install.",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description:
                "URL of the MCP or Skill webpage (GitHub repo, npm package, etc.)",
            },
            use_browser: {
              type: "boolean",
              description: "Use headless browser for dynamic pages (requires Playwright)",
              default: false,
            },
          },
          required: ["url"],
        },
      },
      {
        name: "list_local_capabilities",
        description: "List all locally installed Skills and MCP servers",
        inputSchema: {
          type: "object",
          properties: {
            agent: {
              type: "string",
              description: "Filter by agent type (opencode, claude-code, cursor, etc.)",
              enum: [
                "opencode",
                "claude-code",
                "cursor",
                "openclaw",
                "qcalw",
                "continue",
                "cline",
                "github-copilot",
                "aider",
              ],
            },
            type: {
              type: "string",
              description: "Filter by type",
              enum: ["skill", "mcp"],
            },
          },
        },
      },
      {
        name: "compare_urls",
        description:
          "Compare multiple MCP/Skill URLs and find overlaps between them",
        inputSchema: {
          type: "object",
          properties: {
            urls: {
              type: "array",
              items: { type: "string" },
              description: "Array of URLs to compare",
            },
          },
          required: ["urls"],
        },
      },
    ],
  };
});

// Start server
async function main() {
  await initCapabilities();
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[url-capability-analyzer] MCP server started");
}

main().catch(console.error);