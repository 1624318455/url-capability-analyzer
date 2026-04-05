import * as cheerio from "cheerio";

export interface WebpageInfo {
  name: string;
  type: string;
  url: string;
  description?: string;
  full_text?: string;
  github_url?: string;
  tools: string[];
  install_methods: string[];
  author?: string;
  language?: string;
  tags: string[];
}

const FALSE_POSITIVES = new Set([
  "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
  "have", "has", "had", "do", "does", "did", "will", "would", "could",
  "should", "may", "might", "must", "can", "to", "of", "in", "for",
  "on", "with", "at", "by", "from", "as", "into", "through", "during",
  "before", "after", "above", "below", "between", "under", "again",
  "further", "then", "once", "here", "there", "when", "where", "why",
  "how", "all", "each", "few", "more", "most", "other", "some", "such",
  "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
  "just", "also", "now", "url", "https", "http", "html", "json", "xml",
  "api", "com", "org", "git", "src", "raw", "text", "content", "page",
  "none", "any", "all", "max", "min", "default", "type", "name", "id",
  "value", "data", "key", "link", "img", "div", "span", "p", "ul", "li",
  "h1", "h2", "h3", "h4", "h5", "h6", "button", "input", "form", "table",
  "row", "col", "cell", "header", "footer", "body", "head", "title", "meta",
  "style", "script", "class", "function", "return", "string", "number",
  "boolean", "null", "undefined", "object", "array", "true", "false",
  "world", "home", "mcp", "server", "servers", "fetching", "about",
  "login", "sign", "register", "menu", "nav", "navigation", "bot", "tree",
  "list", "item", "label", "tag", "tags", "icon", "image", "avatar",
  "main", "overview", "introduction", "installation", "configuration",
  "usage", "example", "examples", "available", "tools", "prompt", "prompts",
  "optionally", "alternatively", "recommended", "requirements", "license",
  "contributing", "security", "warning", "caution", "note", "tip",
  "introduction", "features", "quickstart", "getting", "started"
]);

export async function fetchWebpageInfo(
  url: string,
  useBrowser: boolean = false
): Promise<WebpageInfo> {
  const response = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 (compatible; URL-Capability-Analyzer/2.0)",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch URL: ${response.status} ${response.statusText}`);
  }

  const html = await response.text();
  return parseHtml(html, url);
}

function parseHtml(html: string, url: string): WebpageInfo {
  const $ = cheerio.load(html);

  // Remove script and style
  $("script, style, noscript").remove();

  // Get title
  let name = $("title").text() || "";
  if (!name) {
    $("h1, h2, h3").each((_, el) => {
      const text = $(el).text().trim();
      if (text && text.length > 3 && !name) {
        name = text;
        return false;
      }
    });
  }
  if (!name) {
    name = url.split("/").pop() || "Unknown";
  }

  // Detect type
  const text = $("body").text().toLowerCase();
  const urlLower = url.toLowerCase();
  let type = "skill";
  
  if (urlLower.includes("mcp") || text.includes("model context protocol") ||
      text.includes("mcp server") || text.includes("json-rpc")) {
    type = "mcp";
  }

  // Extract description
  let description = $('meta[name="description"]').attr("content") || 
                   $('meta[property="og:description"]').attr("content") || "";
  
  if (!description) {
    const paragraphs: string[] = [];
    $("p").each((_, el) => {
      const text = $(el).text().trim();
      if (text.length > 50) {
        paragraphs.push(text);
      }
    });
    description = paragraphs.slice(0, 3).join("\n\n");
  }

  // Extract GitHub URL
  let github_url: string | undefined;
  $("a[href]").each((_, el) => {
    const href = $(el).attr("href") || "";
    if (href.includes("github.com") && !href.endsWith(".git")) {
      github_url = href.startsWith("http") ? href : `https://github.com${href}`;
      return false;
    }
  });

  // Extract tools
  const tools: string[] = [];
  
  // From code blocks: `tool_name`
  const codeToolPattern = /`([a-z][a-z0-9_-]{2,30})`/g;
  let match;
  while ((match = codeToolPattern.exec(html)) !== null) {
    const tool = match[1].toLowerCase();
    if (!FALSE_POSITIVES.has(tool) && tool.length > 2) {
      tools.push(match[1]);
    }
  }

  // From bold patterns: **tool_name**
  const boldToolPattern = /\*\*([a-z][a-z0-9_-]{2,30})\*\*\s*[-–—]/g;
  while ((match = boldToolPattern.exec(text)) !== null) {
    const tool = match[1].toLowerCase();
    if (!FALSE_POSITIVES.has(tool) && tool.length > 2) {
      tools.push(match[1]);
    }
  }

  // Deduplicate
  const uniqueTools = [...new Set(tools)].slice(0, 10);

  // Extract install methods
  const install_methods: string[] = [];
  const htmlLower = html.toLowerCase();
  if (htmlLower.includes("uvx") || htmlLower.includes("uv run")) install_methods.push("uvx");
  if (htmlLower.includes("pip install")) install_methods.push("pip");
  if (htmlLower.includes("npm install") || htmlLower.includes("npx")) install_methods.push("npm");
  if (htmlLower.includes("docker")) install_methods.push("docker");

  // Extract author
  let author: string | undefined;
  const githubMatch = url.match(/github\.com\/([^\/]+)\//);
  if (githubMatch) {
    author = githubMatch[1];
  }

  // Extract language
  let language: string | undefined;
  const langMatch = text.match(/\b(JavaScript|TypeScript|Python|Rust|Go|Java|C\+\+|Ruby)\b/i);
  if (langMatch) {
    language = langMatch[1];
  }

  return {
    name,
    type,
    url,
    description: description.slice(0, 2000),
    full_text: text.slice(0, 5000),
    github_url,
    tools: uniqueTools,
    install_methods,
    author,
    language,
    tags: [],
  };
}