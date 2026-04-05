#!/usr/bin/env python3
"""
URL Capability Analyzer MCP Server

Usage:
    python server.py

This server implements the Model Context Protocol (MCP) stdio transport.
It analyzes MCP/Skill URLs and compares them with local installed capabilities.
"""

import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from scanner import LocalScanner
from matcher import Matcher
from report import ReportGenerator
from utils import fetch_webpage_info


class MCPServer:
    """MCP Server for URL Capability Analysis."""
    
    def __init__(self):
        self.scanner = LocalScanner()
        self.local_capabilities = None
        self._init_capabilities()
    
    def _init_capabilities(self):
        """Initialize local capabilities cache."""
        try:
            local_all = self.scanner.scan_all()
            self.local_capabilities = local_all["skills"] + local_all["mcps"]
        except Exception as e:
            print(f"Warning: Failed to scan local capabilities: {e}", file=sys.stderr)
            self.local_capabilities = []
    
    def handle_request(self, method: str, params: Dict = None) -> Dict[str, Any]:
        """Handle MCP request."""
        handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
        }
        
        handler = handlers.get(method)
        if handler:
            return handler(params or {})
        
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }
    
    def _handle_initialize(self, params: Dict) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "url-capability-analyzer",
                    "version": "2.0.0"
                },
                "capabilities": {
                    "tools": {},
                    "resources": {}
                }
            }
        }
    
    def _handle_tools_list(self, params: Dict) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "analyze_capability",
                        "description": "Analyze a URL pointing to an MCP or Skill, compare with locally installed capabilities, detect overlaps, and recommend whether to install.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL of the MCP or Skill webpage (GitHub repo, npm package, etc.)"
                                },
                                "use_browser": {
                                    "type": "boolean",
                                    "description": "Use headless browser for dynamic pages (requires Playwright)",
                                    "default": False
                                },
                                "include_embedding": {
                                    "type": "boolean",
                                    "description": "Use sentence-transformers for better matching (requires extra dependencies)",
                                    "default": False
                                }
                            },
                            "required": ["url"]
                        }
                    },
                    {
                        "name": "list_local_capabilities",
                        "description": "List all locally installed Skills and MCP servers",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "agent": {
                                    "type": "string",
                                    "description": "Filter by agent type (opencode, claude-code, cursor, etc.)",
                                    "enum": ["opencode", "claude-code", "cursor", "openclaw", "qcalw", "continue", "cline", "github-copilot", "aider"]
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Filter by type",
                                    "enum": ["skill", "mcp"]
                                }
                            }
                        }
                    },
                    {
                        "name": "compare_urls",
                        "description": "Compare multiple MCP/Skill URLs and find overlaps between them",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "urls": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Array of URLs to compare"
                                }
                            },
                            "required": ["urls"]
                        }
                    }
                ]
            }
        }
    
    def _handle_tools_call(self, params: Dict) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool_handlers = {
            "analyze_capability": self._tool_analyze_capability,
            "list_local_capabilities": self._tool_list_local_capabilities,
            "compare_urls": self._tool_compare_urls,
        }
        
        handler = tool_handlers.get(tool_name)
        if handler:
            try:
                result = handler(arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Tool execution error: {str(e)}"
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Tool not found: {tool_name}"
            }
        }
    
    def _tool_analyze_capability(self, args: Dict) -> Dict[str, Any]:
        """Analyze a URL and compare with local capabilities."""
        url = args.get("url", "")
        use_browser = args.get("use_browser", False)
        include_embedding = args.get("include_embedding", False)
        
        if not url:
            return {"error": "URL is required"}
        
        # Fetch target info
        try:
            target = fetch_webpage_info(url, use_headless_browser=use_browser)
        except Exception as e:
            return {"error": f"Failed to fetch URL: {str(e)}"}
        
        # Analyze with local capabilities
        try:
            matcher = Matcher(use_embedding=include_embedding)
            overlap = matcher.analyze_overlap(target, self.local_capabilities or [])
            synergy = matcher.analyze_synergy(target, self.local_capabilities or [])
            recommendation, reason = matcher.suggest_install(overlap, synergy)
        except Exception as e:
            return {"error": f"Analysis error: {str(e)}"}
        
        # Build result
        overlap_summary = []
        for item in overlap[:5]:
            if item["similarity"] > 0.6:
                overlap_summary.append({
                    "name": item["local_name"],
                    "type": item["local_type"],
                    "similarity": item["similarity"],
                    "level": item["level"]
                })
        
        synergy_summary = []
        for item in synergy[:3]:
            synergy_summary.append({
                "name": item["local_name"],
                "description": item["description"]
            })
        
        return {
            "target": {
                "name": target.get("name"),
                "type": target.get("type"),
                "url": target.get("url"),
                "description": target.get("description", "")[:500],
                "tools": target.get("tools", []),
                "author": target.get("author"),
                "language": target.get("language")
            },
            "local_capabilities_count": len(self.local_capabilities or []),
            "overlap": overlap_summary,
            "synergy": synergy_summary,
            "recommendation": recommendation,
            "reason": reason
        }
    
    def _tool_list_local_capabilities(self, args: Dict) -> Dict[str, Any]:
        """List local capabilities."""
        if not self.local_capabilities:
            self._init_capabilities()
        
        agent_filter = args.get("agent")
        type_filter = args.get("type")
        
        results = self.local_capabilities or []
        
        if agent_filter:
            results = [r for r in results if r.get("agent") == agent_filter]
        
        if type_filter:
            results = [r for r in results if r.get("type") == type_filter]
        
        return {
            "total": len(results),
            "capabilities": [
                {
                    "name": r.get("name"),
                    "type": r.get("type"),
                    "agent": r.get("agent"),
                    "description": r.get("description", "")[:200]
                }
                for r in results[:50]
            ]
        }
    
    def _tool_compare_urls(self, args: Dict) -> Dict[str, Any]:
        """Compare multiple URLs."""
        urls = args.get("urls", [])
        
        if not urls:
            return {"error": "urls array is required"}
        
        if len(urls) < 2:
            return {"error": "At least 2 URLs are required for comparison"}
        
        targets = []
        for url in urls:
            try:
                target = fetch_webpage_info(url, use_headless_browser=False)
                targets.append(target)
            except Exception as e:
                targets.append({"error": f"Failed to fetch {url}: {str(e)}"})
        
        # Compare each pair
        comparisons = []
        matcher = Matcher()
        
        for i in range(len(targets)):
            for j in range(i + 1, len(targets)):
                if "error" in targets[i] or "error" in targets[j]:
                    continue
                
                sim = matcher.compute_similarity(
                    f"{targets[i].get('name', '')} {targets[i].get('description', '')}",
                    f"{targets[j].get('name', '')} {targets[j].get('description', '')}"
                )
                
                comparisons.append({
                    "url1": urls[i],
                    "url2": urls[j],
                    "name1": targets[i].get("name"),
                    "name2": targets[j].get("name"),
                    "similarity": round(sim, 3)
                })
        
        return {
            "urls": urls,
            "targets": [
                {"name": t.get("name"), "type": t.get("type"), "url": t.get("url")}
                if "error" not in t else {"error": t.get("error")}
                for t in targets
            ],
            "comparisons": comparisons
        }
    
    def _handle_resources_list(self, params: Dict) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            "jsonrpc": "2.0",
            "result": {
                "resources": [
                    {
                        "uri": "capability://local/skills",
                        "name": "Local Skills List",
                        "mimeType": "application/json",
                        "description": "List of all locally installed Skills"
                    },
                    {
                        "uri": "capability://local/mcps",
                        "name": "Local MCP Servers List",
                        "mimeType": "application/json",
                        "description": "List of all locally installed MCP servers"
                    }
                ]
            }
        }
    
    def _handle_resources_read(self, params: Dict) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri", "")
        
        if not self.local_capabilities:
            self._init_capabilities()
        
        if uri == "capability://local/skills":
            skills = [r for r in (self.local_capabilities or []) if r.get("type") == "skill"]
            content = json.dumps(skills, ensure_ascii=False, indent=2)
        elif uri == "capability://local/mcps":
            mcps = [r for r in (self.local_capabilities or []) if r.get("type") == "mcp"]
            content = json.dumps(mcps, ensure_ascii=False, indent=2)
        else:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -404, "message": "Resource not found"}
            }
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": content
                    }
                ]
            }
        }


def main():
    """Main entry point - run as stdio MCP server."""
    server = MCPServer()
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            response = server.handle_request(method, params)
            
            if request_id:
                response["id"] = request_id
            
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()