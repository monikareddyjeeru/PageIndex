# PageIndexAI — Hierarchical Summary-Gated Tree Traversal
import json
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CHATGPT_API_KEY")
MODEL   = os.getenv("OPENROUTER_MODEL")

# with open("results/Tender Doc for Testing_structure.json", "r") as f:
#     data = json.load(f)
with open("results/tocnopages_structure.json", "r") as f:
    data = json.load(f)
# if isinstance(data, list):
#     tree = data[0]["structure"]
# else:
#     tree = data["structure"]
# tree=data
tree = data["structure"]
# ── CONFIG ────────────────────────────────────────────────────────────────────
RELEVANCE_THRESHOLD = 6   # 0-10; prune anything below this at every level
LLM_CALL_COUNT      = 0


def call_llm(prompt: str) -> str:
    global LLM_CALL_COUNT
    LLM_CALL_COUNT += 1
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "reasoning": {
                "effort": "none"
            }

        }
    )
    res_json = response.json()
    return res_json["choices"][0]["message"]["content"] if "choices" in res_json else "ERROR"


# ── CORE: Score a node's summary against the query ────────────────────────────

def score_summary(query: str, title: str, summary: str) -> int:
    """
    Scores how well a node's summary relates to the query.
    Returns 0-10. No summary → returns 5 (pass-through, explore safely).
    """
    if not summary or not summary.strip():
        return 5  # No summary available — don't prune blindly, go deeper

    prompt = f"""You are a document navigation assistant helping find relevant sections.

USER QUERY: "{query}"

SECTION TITLE: "{title}"
SECTION SUMMARY: "{summary}"

How likely is it that this section (or its subsections) contains information relevant to the query?

Score strictly from 0 to 10:
  0-2  → Completely unrelated topic
  3-5  → Vaguely related, unlikely to help
  6-7  → Possibly relevant, worth checking deeper
  8-10 → Clearly relevant, likely contains the answer

Respond with ONLY a single integer. No explanation."""

    raw = call_llm(prompt).strip()
    match = re.search(r'\b(\d+)\b', raw)
    score = int(match.group(1)) if match else 5
    return min(10, max(0, score))


# ── TRAVERSAL: Summary gates every level before going deeper ──────────────────

def traverse(query: str, nodes: list, depth: int = 0) -> list:
    """
    For each node at this level:
      1. Read its summary → score it against the query
      2. If score < threshold → PRUNE (don't go deeper)
      3. If score >= threshold AND has children → recurse into children
      4. If score >= threshold AND is a leaf → collect it
    """
    collected = []
    pad = "  " * depth

    for node in nodes:
        title   = node.get("title", "Untitled")
        summary = node.get("summary", "")
        children = node.get("nodes", [])

        # ── Gate: score this node's summary ──────────────────────────────────
        score = score_summary(query, title, summary)

        if score < RELEVANCE_THRESHOLD:
            # Prune — don't explore this subtree at all
            print(f"{pad}✗ PRUNED  [{score}/10]  {title}")
            continue

        if children:
            # ── Branch node: summary passed → go one level deeper ─────────────
            print(f"{pad}↓ EXPLORE [{score}/10]  {title}")
            results = traverse(query, children, depth + 1)
            collected.extend(results)

            # Edge case: branch was relevant but ALL children were pruned
            # → fall back to using this branch's own summary as context
            if not results:
                start    = node.get("start_index", "??")
                end      = node.get("end_index", "??")
                page_str = f"Page {start}" if start == end else f"Pages {start}–{end}"
                print(f"{pad}  ↳ FALLBACK — no children matched, using branch summary")
                collected.append({
                    "node_id" : str(node.get("node_id", "")).zfill(4),
                    "title"   : title,
                    "pages"   : page_str,
                    "score"   : score,
                    "content" : summary   # best we have for this branch
                })
        else:
            # ── Leaf node: summary passed → collect its content ───────────────
            start    = node.get("start_index", "??")
            end      = node.get("end_index", "??")
            page_str = f"Page {start}" if start == end else f"Pages {start}–{end}"
            content  = node.get("content", summary)

            print(f"{pad}✓ COLLECT [{score}/10]  {title}  ({page_str})")
            collected.append({
                "node_id" : str(node.get("node_id", "")).zfill(4),
                "title"   : title,
                "pages"   : page_str,
                "score"   : score,
                "content" : content
            })

    return collected


# ── ANSWER: Synthesise collected nodes into a final response ──────────────────

def generate_answer(query: str, sections: list) -> str:
    if not sections:
        return "No relevant sections were found in the document for this query."

    # Sort by score so the LLM sees the most relevant context first
    sections = sorted(sections, key=lambda s: s["score"], reverse=True)

    context_block = ""
    for s in sections:
        context_block += (
            f"[{s['pages']}]  {s['title']}\n"
            f"{s['content']}\n\n"
        )

    prompt = f"""Answer the question below using ONLY the provided document excerpts.

QUESTION: "{query}"

INSTRUCTIONS:
- Synthesise all relevant excerpts into a single, clear answer.
- Mention page numbers where helpful.
- If the context is insufficient, say so explicitly.

DOCUMENT EXCERPTS:
{context_block}
ANSWER:"""

    return call_llm(prompt)


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    query = input("Ask a question: ")
    print(f"\n▶  Query : {query}")
    print(f"▶  Threshold : {RELEVANCE_THRESHOLD}/10\n")
    print("─" * 70)

    sections = traverse(query, tree)

    print("─" * 70)
    print(f"\n✔  {len(sections)} section(s) collected  |  {LLM_CALL_COUNT} LLM calls\n")
    print("═" * 70)
    print("ANSWER")
    print("═" * 70)
    print(generate_answer(query, sections))

    print("\n" + "─" * 70)
    print("SOURCES")
    print("─" * 70)
    for s in sorted(sections, key=lambda x: x["score"], reverse=True):
        bar = "█" * s["score"] + "░" * (10 - s["score"])
        print(f"  {bar}  {s['pages'].ljust(14)}  {s['title']}")
    print("═" * 70)
    print(f"Total LLM calls: {LLM_CALL_COUNT}")