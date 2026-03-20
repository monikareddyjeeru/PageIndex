#Claude AI
import json
import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("CHATGPT_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL")

with open("results/Tender Doc for Testing_structure.json", "r") as f:
    data = json.load(f)
tree = data["structure"]


def call_llm(prompt):
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
            "reasoning":{
                "effort": "none"
            }
        }
    )
    res_json = response.json()
    return res_json["choices"][0]["message"]["content"] if "choices" in res_json else "ERROR"


# ── STEP 1: Smart tree traversal using summaries as gatekeepers ──────────────

def should_explore_node(query: str, node: dict, path: str) -> bool:
    """Ask the LLM: does this node's summary suggest it's relevant to the query?"""
    summary = node.get("summary", "").strip()
    if not summary:
        return True  # No summary? Explore to be safe

    prompt = f"""You are a document navigation assistant.

Query: "{query}"
Section: "{path}"
Summary: "{summary}"

Does this section likely contain information relevant to the query?
Reply with only YES or NO."""

    response = call_llm(prompt).strip().upper()
    return response.startswith("YES")


def traverse_and_collect(query: str, nodes: list, parent_path: str = "") -> list:
    """
    Recursively walk the tree. At each node:
    1. Check summary → if not relevant, prune entire subtree
    2. If relevant and has children → recurse into children
    3. If relevant and is a leaf → collect content
    """
    collected = []

    for node in nodes:
        title = node.get("title", "Untitled")
        current_path = f"{parent_path} > {title}" if parent_path else title

        # Gate: read summary, decide whether to go deeper
        if not should_explore_node(query, node, current_path):
            print(f"  [PRUNED]   {current_path}")
            continue

        children = node.get("nodes", [])

        if children:
            # Branch node: recurse into children
            print(f"  [EXPLORE]  {current_path}")
            collected.extend(traverse_and_collect(query, children, current_path))
        else:
            # Leaf node: collect actual content
            start = node.get("start_index", "??")
            end = node.get("end_index", "??")
            page_str = f"Page {start}" if start == end else f"Pages {start}-{end}"

            print(f"  [COLLECT]  {current_path} ({page_str})")
            collected.append({
                "id": str(node.get("node_id", "")).zfill(4),
                "path": current_path,
                "pages": page_str,
                "content": node.get("content", node.get("summary", ""))
            })

    return collected


# ── STEP 2: Answer generation from collected leaf nodes ──────────────────────

def generate_answer(query: str, relevant_sections: list) -> str:
    if not relevant_sections:
        return "No relevant information found in the document."

    combined_context = ""
    for s in relevant_sections:
        combined_context += (
            f"SOURCE: {s['path']} ({s['pages']})\n"
            f"CONTENT: {s['content']}\n\n"
        )

    prompt = f"""Answer the question: "{query}" using the provided context.

INSTRUCTIONS:
1. Consolidate information from all provided sources.
2. Reference specific page numbers where relevant.
3. Be thorough — do not omit specific requirements or details.

CONTEXT:
{combined_context}"""

    return call_llm(prompt)


# ── EXECUTION ────────────────────────────────────────────────────────────────

user_query = input("Ask a question: ")
print(f"\n[TRAVERSING TREE for: '{user_query}']\n")

relevant_sections = traverse_and_collect(user_query, tree)

print(f"\n[FOUND {len(relevant_sections)} relevant section(s)]\n")
print("=" * 75)
print("COMPREHENSIVE RESPONSE:")
print("=" * 75)

final_response = generate_answer(user_query, relevant_sections)
print(final_response)

print("\n" + "-" * 75)
print("MAPPED SOURCES:")
for s in relevant_sections:
    print(f"  - {s['pages'].ljust(14)} | {s['path']}")
print("=" * 75)