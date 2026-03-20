# import json
# import os
# import requests
# import re
# from dotenv import load_dotenv

# load_dotenv()
# API_KEY = os.getenv("CHATGPT_API_KEY")
# MODEL = os.getenv("OPENROUTER_MODEL")

# with open("results/Tender Doc for Testing_structure.json", "r") as f:
#     data = json.load(f)
# tree = data["structure"]

# # --- TESTING UTILS ---
# class SearchTracker:
#     def __init__(self):
#         self.steps = []
#         self.total_calls = 0

#     def log_step(self, level, selected_titles):
#         self.steps.append(f"Level {level}: Selected {selected_titles}")
#         self.total_calls += 1

# tracker = SearchTracker()

# def call_llm(prompt, task_name="Task"):
#     print(f"  [LLM CALL] {task_name}...")
#     response = requests.post(
#         "https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {API_KEY}",
#             "Content-Type": "application/json"
#         },
#         json={
#             "model": MODEL,
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature": 0
#         }
#     )
#     res_json = response.json()
#     return res_json["choices"][0]["message"]["content"] if "choices" in res_json else "ERROR"

# # --- CORE HIERARCHICAL SEARCH ---

# def drill_down_search(query, current_nodes, depth=1, path="Root"):
#     """
#     Recursive function that asks the LLM to pick the right 'folders' (nodes).
#     """
#     # 1. Prepare the 'Catalog' for the current level
#     catalog = ""
#     node_map = {}
#     for node in current_nodes:
#         n_id = str(node.get("node_id")).zfill(4)
#         node_map[n_id] = node
        
#         type_label = "[FOLDER]" if node.get("nodes") else "[LEAF/TEXT]"
#         summary = node.get("summary", "No summary")[:150]
#         catalog += f"ID: {n_id} | {type_label} | Title: {node['title']}\nSummary: {summary}\n---\n"

#     # 2. Ask LLM to decide
#     prompt = f"""
#     ROLE: Document Auditor
#     GOAL: Find information for the query: "{query}"
#     LOCATION IN DOC: {path}

#     INSTRUCTIONS:
#     Review the IDs below. Identify which sections likely contain the answer.
#     - If a section is a [FOLDER], select it to look inside.
#     - If a section is [LEAF/TEXT], select it to extract its content.
#     - You may select multiple IDs if the info is spread out.
#     - If nothing is relevant, reply 'NONE'.

#     CATALOG:
#     {catalog}

#     OUTPUT: Only a comma-separated list of IDs (e.g. 0001, 0004).
#     """
    
#     raw_response = call_llm(prompt, f"Navigating Level {depth}")
#     selected_ids = re.findall(r'\b\d{4}\b', raw_response)
    
#     found_nodes = []
    
#     if not selected_ids:
#         return []

#     selected_titles = []
#     for sid in selected_ids:
#         if sid in node_map:
#             target_node = node_map[sid]
#             selected_titles.append(target_node['title'])
            
#             # If it's a folder, we recurse (Drill Down)
#             if target_node.get("nodes"):
#                 print(f"    ↳ DRILLING INTO: {target_node['title']}...")
#                 found_nodes.extend(drill_down_search(query, target_node["nodes"], depth + 1, f"{path} > {target_node['title']}"))
#             else:
#                 # It's a leaf node, keep it
#                 found_nodes.append(target_node)
    
#     tracker.log_step(depth, selected_titles)
#     return found_nodes

# def generate_final_answer(query, nodes):
#     """Consolidates the specific nodes found into a final answer."""
#     context = ""
#     sources = []
    
#     # Use a dict to deduplicate nodes by ID
#     unique_nodes = {str(n['node_id']): n for n in nodes}.values()
    
#     for n in unique_nodes:
#         p_start = n.get('start_index', '?')
#         p_end = n.get('end_index', '?')
#         page_ref = f"Page {p_start}" if p_start == p_end else f"Pages {p_start}-{p_end}"
        
#         context += f"SOURCE: {n['title']} ({page_ref})\nCONTENT: {n.get('content', n.get('summary'))}\n\n"
#         sources.append(f"{page_ref} | {n['title']}")

#     prompt = f"""
#     Answer the query: "{query}"
#     Use ONLY the provided context. If the info is missing, say so.
#     Be specific and mention page numbers for every requirement found.

#     CONTEXT:
#     {context}
#     """
#     answer = call_llm(prompt, "Generating Final Answer")
#     return answer, sources

# # --- TEST EXECUTION ---

# if __name__ == "__main__":
#     print("\n" + "="*50)
#     print("TENDER DRILL-DOWN TESTER")
#     print("="*50)
    
#     test_query = input("Enter your test query: ")
    
#     # Phase 1: Search
#     print(f"\n[1/2] STARTING HIERARCHICAL SEARCH...")
#     relevant_nodes = drill_down_search(test_query, tree)
    
#     # Phase 2: Answer
#     if relevant_nodes:
#         print(f"\n[2/2] EXTRACTING CONTENT FROM {len(relevant_nodes)} SECTIONS...")
#         final_answer, source_list = generate_final_answer(test_query, relevant_nodes)
        
#         print("\n" + "#"*60)
#         print("FINAL RESULT")
#         print("#"*60)
#         print(final_answer)
#         print("\nSOURCES:")
#         for s in source_list:
#             print(f"  - {s}")
#     else:
#         print("\n[RESULT] No relevant information found in any branch.")

#     # Phase 3: Analytics
#     print("\n" + "="*50)
#     print("PERFORMANCE METRICS")
#     print("="*50)
#     print(f"Total LLM Calls: {tracker.total_calls + 1}")
#     print("Path Taken:")
#     for step in tracker.steps:
#         print(f"  {step}")
#     print("="*50 + "\n")


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

def call_llm(prompt, task_name="Task"):
    print(f"  [LLM CALL] {task_name}...")
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

# --- NEW: QUERY DECOMPOSITION ---
def decompose_query(original_query):
    """Breaks a compound question into a list of simple questions."""
    prompt = f"""
    Break the following user query into a list of simple, independent search questions.
    Example: "Who is the owner and what is the price?" 
    Output:
    1. Who is the owner?
    2. What is the price?

    Query: "{original_query}"
    Output as a simple list.
    """
    raw = call_llm(prompt, "Decomposing Query")
    # Extract lines that look like questions
    questions = re.findall(r'\d+\.\s*(.*)', raw)
    if not questions: # Fallback if regex fails
        questions = [original_query]
    return questions

# --- DRILL DOWN (SAME AS BEFORE) ---
def drill_down_search(query, current_nodes, path="Root"):
    catalog = ""
    node_map = {}
    for node in current_nodes:
        n_id = str(node.get("node_id")).zfill(4)
        node_map[n_id] = node
        type_label = "[FOLDER]" if node.get("nodes") else "[LEAF]"
        catalog += f"ID: {n_id} | {type_label} | Title: {node['title']}\nSummary: {node.get('summary', '')[:150]}\n---\n"

    prompt = f"""
    Query: "{query}"
    Location: {path}
    Identify IDs that contain info for THIS specific query. 
    If a section is a [FOLDER], select it to look inside.
    If it's a [LEAF], select it to extract content.
    Output ONLY a comma-separated list of IDs or 'NONE'.

    CATALOG:
    {catalog}
    """
    
    raw_response = call_llm(prompt, f"Searching for: {query[:30]}...")
    selected_ids = re.findall(r'\b\d{4}\b', raw_response)
    
    found_nodes = []
    for sid in selected_ids:
        if sid in node_map:
            target = node_map[sid]
            if target.get("nodes"):
                found_nodes.extend(drill_down_search(query, target["nodes"], f"{path} > {target['title']}"))
            else:
                found_nodes.append(target)
    return found_nodes

# --- FINAL GENERATION ---
def generate_final_answer(original_query, all_nodes):
    # Deduplicate nodes
    unique_nodes = {str(n['node_id']): n for n in all_nodes}.values()
    
    context = ""
    for n in unique_nodes:
        p = f"Page {n.get('start_index')}"
        context += f"SOURCE: {n['title']} ({p})\nCONTENT: {n.get('content', n.get('summary'))}\n\n"

    prompt = f"""
    Answer the user's full query: "{original_query}"
    
    Use the context below which was gathered from multiple parts of the document.
    Ensure you answer EVERY part of the user's question.
    Cite page numbers.

    CONTEXT:
    {context}
    """
    return call_llm(prompt, "Synthesizing Final Answer")

# --- EXECUTION ---
if __name__ == "__main__":
    user_query = input("Ask your complex question: ")
    
    # Step 1: Break it down
    sub_questions = decompose_query(user_query)
    print(f"[SYSTEM] Broken down into {len(sub_questions)} parts: {sub_questions}")
    
    # Step 2: Search for each part independently
    all_relevant_nodes = []
    for q in sub_questions:
        print(f"\n[SEARCHING] Part: {q}")
        nodes = drill_down_search(q, tree)
        all_relevant_nodes.extend(nodes)
    
    # Step 3: Combine and Answer
    if all_relevant_nodes:
        final_answer = generate_final_answer(user_query, all_relevant_nodes)
        print("\n" + "="*80)
        print("FINAL COMPREHENSIVE ANSWER")
        print("="*80)
        print(final_answer)
    else:
        print("No information found.")
