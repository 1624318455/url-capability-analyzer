import type { WebpageInfo } from "./webfetch.js";
import type { LocalCapability } from "./scanner.js";

export interface OverlapItem {
  name: string;
  type: string;
  agent: string;
  similarity: number;
  level: string;
  reason: string;
}

export interface SynergyItem {
  name: string;
  type: string;
  description: string;
}

export interface AnalysisResult {
  overlap: OverlapItem[];
  synergy: SynergyItem[];
  recommendation: string;
  reason: string;
}

// Simple TF-IDF like implementation
function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length > 2);
}

function termFrequency(term: string, tokens: string[]): number {
  const count = tokens.filter((t) => t === term).length;
  return count / tokens.length;
}

function inverseDocumentFrequency(term: string, documents: string[][]): number {
  const docsWithTerm = documents.filter((doc) => doc.includes(term)).length;
  if (docsWithTerm === 0) return 0;
  return Math.log(documents.length / docsWithTerm);
}

function computeTfidfSimilarity(text1: string, text2: string): number {
  const tokens1 = tokenize(text1);
  const tokens2 = tokenize(text2);
  
  if (tokens1.length === 0 || tokens2.length === 0) {
    return 0;
  }

  const allTokens = [tokens1, tokens2];
  const uniqueTerms = [...new Set([...tokens1, ...tokens2])];

  // Compute TF-IDF vectors
  const tfidf1: number[] = [];
  const tfidf2: number[] = [];

  for (const term of uniqueTerms) {
    const tf1 = termFrequency(term, tokens1);
    const tf2 = termFrequency(term, tokens2);
    const idf = inverseDocumentFrequency(term, allTokens);
    
    tfidf1.push(tf1 * idf);
    tfidf2.push(tf2 * idf);
  }

  // Cosine similarity
  const dotProduct = tfidf1.reduce((sum, val, i) => sum + val * tfidf2[i], 0);
  const magnitude1 = Math.sqrt(tfidf1.reduce((sum, val) => sum + val * val, 0));
  const magnitude2 = Math.sqrt(tfidf2.reduce((sum, val) => sum + val * val, 0));

  if (magnitude1 === 0 || magnitude2 === 0) {
    return 0;
  }

  return dotProduct / (magnitude1 * magnitude2);
}

function explainOverlap(target: WebpageInfo, local: LocalCapability, sim: number): string {
  if (sim > 0.85) {
    return "Likely duplicate functionality";
  } else if (sim > 0.6) {
    return "Partial functional overlap";
  }
  return "No significant overlap";
}

export function analyzeOverlap(
  target: WebpageInfo,
  localCapabilities: LocalCapability[]
): AnalysisResult {
  const targetText = `${target.name} ${target.description || ""}`;
  
  const overlap: OverlapItem[] = [];
  
  for (const local of localCapabilities) {
    const localText = `${local.name} ${local.description || ""}`;
    const sim = computeTfidfSimilarity(targetText, localText);
    
    let level: string;
    if (sim > 0.85) {
      level = "high";
    } else if (sim > 0.6) {
      level = "partial";
    } else {
      level = "none";
    }

    if (sim > 0.3) {
      overlap.push({
        name: local.name,
        type: local.type,
        agent: local.agent,
        similarity: Math.round(sim * 1000) / 1000,
        level,
        reason: explainOverlap(target, local, sim),
      });
    }
  }

  // Sort by similarity
  overlap.sort((a, b) => b.similarity - a.similarity);

  // Synergy detection (simple keyword-based)
  const synergy: SynergyItem[] = [];
  const targetDesc = (target.description || "").toLowerCase();
  
  for (const local of localCapabilities) {
    const localDesc = (local.description || "").toLowerCase();
    
    // Pipeline: fetch → send/notify
    if (
      (targetDesc.includes("fetch") || targetDesc.includes("get") || targetDesc.includes("read") ||
       targetDesc.includes("list") || targetDesc.includes("query")) &&
      (localDesc.includes("send") || localDesc.includes("post") || localDesc.includes("write") ||
       localDesc.includes("create") || localDesc.includes("notify"))
    ) {
      synergy.push({
        name: local.name,
        type: local.type,
        description: `Target retrieves data → ${local.name} can send/notify`,
      });
    }
    // Search → analyze
    else if (
      (targetDesc.includes("search") || targetDesc.includes("find")) &&
      (localDesc.includes("analyze") || localDesc.includes("summarize") || localDesc.includes("process"))
    ) {
      synergy.push({
        name: local.name,
        type: local.type,
        description: `Target searches → ${local.name} can analyze results`,
      });
    }
  }

  // Generate recommendation
  const highOverlap = overlap.some((o) => o.level === "high");
  const partialOverlap = overlap.some((o) => o.level === "partial");

  let recommendation: string;
  let reason: string;

  if (highOverlap) {
    recommendation = "Do not install";
    reason = "High overlap with existing capability";
  } else if (synergy.length > 0) {
    recommendation = "Recommended";
    reason = "Can work synergistically with existing tools";
  } else if (partialOverlap) {
    recommendation = "Consider carefully";
    reason = "Partial overlap; may extend or conflict";
  } else {
    recommendation = "Recommended";
    reason = "No conflict and no overlap";
  }

  return {
    overlap,
    synergy,
    recommendation,
    reason,
  };
}

export function suggestInstall(
  overlap: OverlapItem[],
  synergy: SynergyItem[]
): [string, string] {
  const result = analyzeOverlap(
    { name: "", type: "", url: "", tools: [], install_methods: [], tags: [] },
    []
  );
  return [result.recommendation, result.reason];
}