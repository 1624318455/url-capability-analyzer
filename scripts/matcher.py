import math
from typing import List, Dict, Any, Tuple, Optional
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class Matcher:
    def __init__(self, use_embedding: bool = False, embedding_model=None):
        self.use_embedding = use_embedding and (embedding_model is not None)
        self.embedding_model = embedding_model
        if not SKLEARN_AVAILABLE and not self.use_embedding:
            raise RuntimeError("scikit-learn is required for TF‑IDF matching. Install with: pip install scikit-learn")

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Return cosine similarity between two texts (0-1)."""
        if self.use_embedding:
            emb1 = self.embedding_model.encode([text1])[0]
            emb2 = self.embedding_model.encode([text2])[0]
            return float(cosine_similarity([emb1], [emb2])[0][0])
        else:
            vectorizer = TfidfVectorizer().fit([text1, text2])
            tfidf = vectorizer.transform([text1, text2])
            return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])

    def analyze_overlap(self, target: Dict[str, Any], local_list: List[Dict[str, Any]]) -> List[Dict]:
        """Return overlap info for each local capability."""
        target_text = f"{target.get('name','')} {target.get('description','')}"
        results = []
        for local in local_list:
            local_text = f"{local.get('name','')} {local.get('description','')}"
            sim = self.compute_similarity(target_text, local_text)
            if sim > 0.85:
                level = "high"
            elif sim > 0.6:
                level = "partial"
            else:
                level = "none"
            results.append({
                "local_name": local["name"],
                "local_type": local["type"],
                "agent": local.get("agent", "unknown"),
                "similarity": round(sim, 3),
                "level": level,
                "reason": self._explain_overlap(target, local, sim)
            })
        # sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results

    def _explain_overlap(self, target: Dict, local: Dict, sim: float) -> str:
        if sim > 0.85:
            return "Likely duplicate functionality"
        elif sim > 0.6:
            return "Partial functional overlap"
        else:
            return "No significant overlap"

    def analyze_synergy(self, target: Dict, local_list: List[Dict]) -> List[Dict]:
        """Heuristic synergy detection based on keyword flow."""
        synergies = []
        target_desc = target.get("description", "").lower()
        for local in local_list:
            local_desc = local.get("description", "").lower()
            # Simple pipeline: target fetches/reads -> local sends/writes
            if any(kw in target_desc for kw in ["fetch", "get", "read", "list", "query"]) and \
               any(kw in local_desc for kw in ["send", "post", "write", "create", "notify"]):
                synergies.append({
                    "local_name": local["name"],
                    "local_type": local["type"],
                    "description": f"Target retrieves data → {local['name']} can send/notify"
                })
            elif any(kw in target_desc for kw in ["search", "find"]) and \
                 any(kw in local_desc for kw in ["analyze", "summarize", "process"]):
                synergies.append({
                    "local_name": local["name"],
                    "local_type": local["type"],
                    "description": f"Target searches → {local['name']} can analyze results"
                })
        return synergies

    def suggest_install(self, overlap_results: List[Dict], synergy_results: List[Dict]) -> Tuple[str, str]:
        """Return (recommendation, reasoning)."""
        high_overlap = any(r["level"] == "high" for r in overlap_results)
        partial_overlap = any(r["level"] == "partial" for r in overlap_results)
        if high_overlap:
            return "❌ Do not install", "High overlap with existing capability"
        if synergy_results:
            return "✅ Recommended", "Can work synergistically with existing tools"
        if partial_overlap:
            return "⚠️ Consider carefully", "Partial overlap; may extend or conflict"
        return "✅ Recommended", "No conflict and no overlap"