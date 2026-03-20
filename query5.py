import json
import re

from services.utils import (
    ChatGPT_API,
    extract_json,
    structure_to_list,
    get_page_tokens,
    get_text_of_pdf_pages
)

MODEL = "openai/gpt-oss-20b"
RELEVANCE_THRESHOLD = 6


def load_structure(structure_path):
    with open(structure_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------
# LLM relevance scoring
# ----------------------------------------------------

def score_summary(query, title, summary):

    if not summary or not summary.strip():
        return 5

    prompt = f"""
        You are evaluating document relevance.

        User question:
        {query}

        Section title:
        {title}

        Section summary:
        {summary}

        Score relevance from 0 to 10.

        0-2 → unrelated
        3-5 → weak relevance
        6-7 → possibly relevant
        8-10 → clearly relevant

        Return ONLY the number.
        """

    response = ChatGPT_API(MODEL, prompt)

    if not isinstance(response, str):
        return 5

    match = re.search(r"\d+", response)

    score = int(match.group()) if match else 5

    return max(0, min(10, score))


# ----------------------------------------------------
# Recursive traversal
# ----------------------------------------------------

def traverse(query, nodes, depth=0):

    collected = []

    for node in nodes:

        title = node.get("title", "")
        summary = node.get("summary", "")
        children = node.get("nodes", [])

        score = score_summary(query, title, summary)

        if score < RELEVANCE_THRESHOLD:
            continue

        if children:
            results = traverse(query, children, depth + 1)
            collected.extend(results)

        else:
            collected.append(node)

    return collected


# ----------------------------------------------------
# Context retrieval
# ----------------------------------------------------

def retrieve_context(pdf_pages, nodes):

    context = ""

    for node in nodes:

        page_offset = 1

        start = node["start_index"] - page_offset
        end = node["end_index"] - page_offset

        text = get_text_of_pdf_pages(pdf_pages, start, end)

        context += f"""
==============================
SECTION TITLE: {node['title']}
PAGE RANGE: {start}-{end}
==============================

{text}
"""

    return context


# ----------------------------------------------------
# Final answer generation
# ----------------------------------------------------

def generate_answer(question, context):

    prompt = f"""
You are answering questions using a technical document.

Question:
{question}

Document content:
{context}

Instructions:
- Identify the exact page where the answer appears.
- Even if the section spans multiple pages, return the specific page number where the fact is found.
- Do NOT return page ranges.
- Use the section title as the citation.
- Extract exact numeric values when present.

Return format:

Answer: <short answer>

Source:
Section: <section title>
Page: <exact page number>
"""

    return ChatGPT_API(MODEL, prompt)


# ----------------------------------------------------
# Main pipeline
# ----------------------------------------------------

def ask_document(question, pdf_path, structure_path):

    structure = load_structure(structure_path)

    pdf_pages = get_page_tokens(pdf_path)

    root_nodes = structure["structure"]

    relevant_nodes = traverse(question, root_nodes)

    context = retrieve_context(pdf_pages, relevant_nodes)

    answer = generate_answer(question, context)

    return answer