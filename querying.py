# import json
# import openai
# import os,requests
# from dotenv import load_dotenv
# # -----------------------------
# # Set OpenAI API Key
# # -----------------------------
# load_dotenv()
# API_KEY = os.getenv("CHATGPT_API_KEY")
# MODEL=os.getenv("OPENROUTER_MODEL")
# # print("Model:",MODEL,API_KEY)

# # -----------------------------
# # Load the PageIndex tree
# # -----------------------------
# with open("results/Tender Doc for Testing_structure.json", "r") as f:
#     data = json.load(f)

# tree=data["structure"]
# # -----------------------------
# # Flatten tree → node list
# # -----------------------------
# # def flatten_tree(tree):

# #     nodes = []

# #     def traverse(node):

# #         nodes.append({
# #             "node_id": node.get("node_id"),
# #             "title": node.get("title"),
# #             "text": node.get("summary", "")
# #         })

# #         for child in node.get("nodes", []):
# #             traverse(child)

# #     for root in tree:
# #         traverse(root)

# #     return nodes
# # nodes = flatten_tree(tree)

# # print("Total nodes:", len(nodes))

# def call_llm(prompt):

#     response = requests.post(
#         "https://openrouter.ai/api/v1/chat/completions",
#         headers={
#             "Authorization": f"Bearer {API_KEY}",
#             "Content-Type": "application/json"
#         },
#         json={
#             "model": MODEL,
#             "messages":[{"role":"user","content":prompt}],
#             "temperature": 0.1 
#         }
#     )
#     data = response.json()
#     # Debug print
#     print("\nLLM RAW RESPONSE:\n", data)

#     if "choices" not in data:
#         raise Exception(f"LLM API Error: {data}")

#     return data["choices"][0]["message"]["content"]

# def choose_best_node(query, current_level_nodes,breadcrumbs):
#     """
#     Shows the LLM ONLY the nodes at the current level.
#     """
#     # Create a simple list of options for the LLM
#     options = ""
#     for node in current_level_nodes:
#         options += f"ID: {node.get('node_id')} | Title: {node.get('title')}\nSummary: {node.get('summary', '')[:200]}\n---\n"

#     path = " > ".join(breadcrumbs) if breadcrumbs else "Root"
#     # prompt = f"""
#     #     You are a document navigation agent. 
#     #     USER QUERY: "{query}"

#     #     INSTRUCTIONS:
#     #     1. Review the available Headings below.
#     #     2. Select the ID of the section that is MOST likely to contain the SPECIFIC answer. 
#     #     3. Ignore generic introductory sections if a specific technical section is available.
#     #     4. If multiple look relevant, pick the one with the most detailed summary.

#     #     AVAILABLE SECTIONS:
#     #     {options}

#     #     Output ONLY the ID (e.g., 0001). Do not write sentences.
#     #     """
#     prompt = f"""
#         You are a document navigation assistant.
#         The user is looking for: "{query}"
#         Current Location in Document: {path}

#         TASK:
#         Look at the headings below. Which one is MOST likely to contain the specific data required to answer the query?
        
#         THINKING STEPS:
#         1. Does the query ask for a technical detail, a price, or a date?
#         2. Which heading matches that category?
#         3. If no heading matches, or you are at the correct place, output 'STOP'.

#         AVAILABLE SECTIONS:
#         {options}

#         OUTPUT FORMAT:
#         Reasoning: [1 sentence why this section fits]
#         Selection: [Just the 4-digit ID]
#         """
#     answer = call_llm(prompt).strip()
#     print(f"\n[NAVIGATOR]: {answer}") # See the LLM's logic
#     import re
#     match = re.search(r'Selection:\s*(\d+)', answer)
#     if match:
#         return match.group(1).upper()
#     return "NONE"


# def recursive_search(query, current_nodes,breadcrumbs=[]):
#     """
#     The core logic: Drills down into the tree level by level.
#     """
#     if not current_nodes:
#         return None

#     # Ask LLM which of these specific nodes to enter
#     selected_id = choose_best_node(query, current_nodes,breadcrumbs)
#     if selected_id in ["STOP", "NONE"]:
#         return None, breadcrumbs
#     # selected_id = "".join(filter(str.isdigit, selected_id_raw))
#     print(f"-> LLM chose: {selected_id}")

#     # if "NONE" in selected_id.upper() or "STOP" in selected_id.upper():
#     #     return None

#     # Find the actual node object that matches the ID
#     target_node = None
#     for node in current_nodes:
#         if str(node.get("node_id")).strip().zfill(4) == selected_id.zfill(4):
#             target_node = node
#             break

#     if target_node:
#         new_breadcrumbs = breadcrumbs + [target_node['title']]
#         children = target_node.get("nodes", [])
#         # print(f"Entering: {target_node['title']}")
        
#         # Check if this node has children
#         # children = target_node.get("nodes", [])
        
#         if children:
#             # Recursively go deeper
#             deeper_node,final_path = recursive_search(query, children,new_breadcrumbs)
#             if deeper_node:
#                 return deeper_node, final_path
#             else:
#                 return target_node, new_breadcrumbs
#             # If sub-search finds nothing, this node is the best match
#             # return {deeper_node,final_breadcrumbs} if deeper_node else {target_node,new_breadcrumbs}
#         else:
#             # No more children, this is the leaf node
#             return target_node,new_breadcrumbs
    
#     return None,breadcrumbs


# def generate_final_answer(query, node, breadcrumbs):
#     path = " > ".join(breadcrumbs)
#     context = f"Document Path: {path}\nHeading: {node['title']}\nText Content: {node.get('content', node.get('summary', ''))}"
#     # prompt = f"Using the following context, answer the question: {query}\n\nContext:\n{context}"
#     prompt = f"""
#         Answer the question accurately using ONLY the context provided below.
#         If the information is not in the context, say you don't know.

#         Context:
#         {context}

#         Question: {query}
#         """
#     return call_llm(prompt)


# user_query = input("Ask a question: ")

# # node = recursive_search(tree, query)
# best_node, final_path = recursive_search(user_query, tree)
# # if best_node:
# #     # print(f"\n[FOUND] Final Section: {best_node['title']}")
# #     # # print("\nRelevant Section:", node["title"])
# #     # # answer = generate_final_answer(query, node.get("text",""))
# #     # final_answer = generate_final_answer(user_query, best_node)
# #     # # print("\nAnswer:\n", answer)
# #     # print(f"\n[ANSWER]\n{final_answer}")
# #     page_num = (
# #         best_node.get("page_number") or 
# #         best_node.get("physical_index") or 
# #         best_node.get("start_page") or 
# #         "Unknown"
# #     )
# #     heading = best_node.get("title", "No Heading")
# #     answer = generate_final_answer(user_query, best_node)

# #     # FINAL CLEAN OUTPUT
# #     print("\n" + "="*50)
# #     print(f"PAGE NUMBER: {page_num}")
# #     print(f"HEADING:     {heading}")
# #     print(f"ANSWER:      {answer}")
# #     print("="*50 + "\n")
# # else:print("No relevant section found.")


# if best_node:
#     page_num = best_node.get("page_number") or best_node.get("physical_index") or "N/A"
#     heading = " > ".join(final_path)
#     answer = generate_final_answer(user_query, best_node, final_path)

#     print("\n" + "="*60)
#     print(f"PAGE:    {page_num}")
#     print(f"PATH:    {heading}")
#     print(f"ANSWER:  {answer}")
#     print("="*60 + "\n")
# else:
#     print("Could not find a relevant section.")



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

# def call_llm(prompt):
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

# # 1. FLATTEN THE ENTIRE TREE
# # We capture every leaf and every branch to ensure no "path" is hidden
# def flatten_entire_document(nodes, parent_path=""):
#     flat_list = []
#     for node in nodes:
#         current_path = f"{parent_path} > {node['title']}" if parent_path else node['title']
#         flat_list.append({
#             "id": str(node.get("node_id")).zfill(4),
#             "path": current_path,
#             "summary": node.get("summary", ""),
#             "content": node.get("content", node.get("summary", "")),
#             "page": node.get("page_index") or node.get("physical_index") or "N/A"
#         })
#         if node.get("nodes"):
#             flat_list.extend(flatten_entire_document(node["nodes"], current_path))
#     return flat_list

# all_sections = flatten_entire_document(tree)

# # 2. MULTI-PATH IDENTIFICATION
# def identify_all_relevant_ids(query, sections):
#     catalog = ""
#     for s in sections:
#         catalog += f"ID: {s['id']} | Path: {s['path']} | Summary: {s['summary'][:250]}\n---\n"

#     prompt = f"""
#     You are an expert auditor. The user needs to find ALL mentions of: "{query}"
    
#     Look at the document catalog below. List the IDs of EVERY section that might contain even a partial answer or relevant detail. 
#     Do not be restrictive. If a section is remotely related, include it.

#     CATALOG:
#     {catalog}

#     Output ONLY a comma-separated list of IDs.
#     Example: 0001, 0005, 0012
#     """
#     raw_response = call_llm(prompt)
#     print(f"\n[SCANNER] All potentially relevant sections: {raw_response}")
    
#     # Extract all 4-digit IDs found in the response
#     return re.findall(r'\b\d{4}\b', raw_response)

# # 3. COMPREHENSIVE ANSWER GENERATION
# def generate_comprehensive_answer(query, relevant_ids, sections):
#     combined_context = ""
#     sources_used = []

#     for s in sections:
#         if s['id'] in relevant_ids:
#             combined_context += f"SOURCE: {s['path']} (Page {s['page']})\nCONTENT: {s['content']}\n\n"
#             sources_used.append(s)

#     if not combined_context:
#         return "The information requested was not found in any section of the document.", []

#     prompt = f"""
#     Using the multiple context sources provided below, provide a COMPLETE and exhaustive answer to the question: "{query}"
    
#     INSTRUCTIONS:
#     1. Combine information from all sources.
#     2. If different sources provide different details, include all of them.
#     3. Group the answer logically (e.g., by category or requirement).
#     4. Cite the Page Numbers in your answer.

#     CONTEXT FROM DOCUMENT:
#     {combined_context}
#     """
#     final_answer = call_llm(prompt)
#     return final_answer, sources_used

# # --- EXECUTION ---
# user_query = input("Ask a question (to search all paths): ")

# # Step 1: Broad Scan
# relevant_ids = identify_all_relevant_ids(user_query, all_sections)

# # Step 2: Extract and Synthesize
# if relevant_ids:
#     final_response, sources = generate_comprehensive_answer(user_query, relevant_ids, all_sections)
    
#     print("\n" + "="*70)
#     print("COMPREHENSIVE MULTI-PATH ANSWER:")
#     print("="*70)
#     print(final_response)
#     print("\n" + "-"*70)
#     print("RELEVANT SECTIONS FOUND:")
#     for s in sources:
#         print(f"- Page {s['page']} | {s['path']}")
#     print("="*70 + "\n")
# else:
#     print("\nNo relevant sections were found across any document paths.")


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

# 1. FLATTEN THE ENTIRE TREE (Capturing start_index and end_index)
def flatten_entire_document(nodes, parent_path=""):
    flat_list = []
    for node in nodes:
        current_path = f"{parent_path} > {node['title']}" if parent_path else node['title']
        
        # Capture the page range
        start = node.get("start_index", "??")
        end = node.get("end_index", "??")
        
        # Format the page string
        if start == end:
            page_str = f"Page {start}"
        else:
            page_str = f"Pages {start}-{end}"

        flat_list.append({
            "id": str(node.get("node_id")).zfill(4),
            "path": current_path,
            "summary": node.get("summary", ""),
            "content": node.get("content", node.get("summary", "")),
            "pages": page_str
        })
        
        if node.get("nodes"):
            flat_list.extend(flatten_entire_document(node["nodes"], current_path))

    # print("FLat List:",flat_list)
    return flat_list

all_sections = flatten_entire_document(tree)

# 2. MULTI-PATH IDENTIFICATION
def identify_all_relevant_ids(query, sections):
    catalog = ""
    for s in sections:
        catalog += f"ID: {s['id']} | {s['pages']} | Path: {s['path']} | Summary: {s['summary'][:200]}\n---\n"

    prompt = f"""
    You are an expert document auditor. The user needs to find ALL mentions of: "{query}"
    
    Review the catalog below. Identify the IDs of EVERY section that might contain relevant details.
    Be thorough. If multiple sections across different chapters are relevant, list them all.

    CATALOG:
    {catalog}

    Output ONLY a comma-separated list of IDs (e.g., 0001, 0005).
    """
    raw_response = call_llm(prompt)
    print(f"\n[SCANNER] Relevant Section IDs: {raw_response}")
    return re.findall(r'\b\d{4}\b', raw_response)

# 3. COMPREHENSIVE ANSWER GENERATION
def generate_comprehensive_answer(query, relevant_ids, sections):
    combined_context = ""
    sources_used = []

    for s in sections:
        if s['id'] in relevant_ids:
            combined_context += f"SOURCE: {s['path']} ({s['pages']})\nCONTENT: {s['content']}\n\n"
            sources_used.append(s)

    if not combined_context:
        return "Information not found.", []

    prompt = f"""
    Answer the question: "{query}" using the provided context.
    
    INSTRUCTIONS:
    1. Consolidate info from all provided sources.
    2. If details appear on different pages, mention those specific pages.
    3. Be exhaustive. Do not summarize so much that you lose specific requirements.

    CONTEXT:
    {combined_context}
    """
    final_answer = call_llm(prompt)
    return final_answer, sources_used

# --- EXECUTION ---
user_query = input("Ask a question: ")

# Step 1: Broad Scan for IDs
relevant_ids = identify_all_relevant_ids(user_query, all_sections)

# Step 2: Extract and Generate Answer
if relevant_ids:
    final_response, sources = generate_comprehensive_answer(user_query, relevant_ids, all_sections)
    
    print("\n" + "="*75)
    print("COMPREHENSIVE RESPONSE:")
    print("="*75)
    print(final_response)
    print("\n" + "-"*75)
    print("MAPPED SOURCES:")
    for s in sources:
        print(f"- {s['pages'].ljust(12)} | {s['path']}")
    print("="*75 + "\n")
else:
    print("\nNo relevant sections identified.")