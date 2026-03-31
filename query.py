import json
import asyncio
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini") # as used in the official cookbook


# --- Step 1: LLM helper ---
async def call_llm(prompt, model=MODEL):
    client = openai.AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENAI_API_KEY
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    message = response.choices[0].message
    if message.content is None:
        print("\n--- ERROR: message.content is None ---")
        print(response.model_dump_json(indent=2))
        print("--------------------------------------\n")
        return "{}" # Return empty JSON to prevent immediate crash in json.loads
        
    return message.content.strip()


# --- Step 2: Build flat node map from tree JSON ---
def create_node_mapping(tree_structure):
    node_map = {}

    def traverse(nodes):
        for node in nodes:
            if "node_id" in node:
                node_map[node["node_id"]] = node
            if "nodes" in node:
                traverse(node["nodes"])

    traverse(tree_structure)
    return node_map


# --- Step 3: Tree search — ask LLM which nodes answer the query ---
async def tree_search(query, tree):
    tree_json = json.dumps(tree, indent=2)
    prompt = f"""You are given a question and a tree structure of a document.
Find all nodes that are likely to contain the answer.

Question: {query}
Document tree structure: {tree_json}

Reply ONLY in this JSON format:
{{
  "thinking": "<your reasoning>",
  "node_list": ["0001", "0002"]
}}"""
    response = await call_llm(prompt)
    try:
        return json.loads(response)
    except Exception as e:
        print(f"Warning: Failed to parse LLM response as JSON. Error: {e}")
        return {}


# --- Step 4: Extract text from identified nodes ---
def extract_context(node_list, node_map):
    context = ""
    for node_id in node_list:
        if node_id in node_map and "summary" in node_map[node_id]:
            context += f"[{node_map[node_id].get('title', 'Section')}]\n"
            context += node_map[node_id]["summary"] + "\n\n"
    return context.strip()


# --- Step 5: Generate final answer ---
async def answer_question(query, context):
    prompt = f"""Answer the question based on the context below.

Question: {query}
Context: {context}"""
    return await call_llm(prompt)


# --- Main query function ---
async def query(question, tree_path):
    # Load the pre-generated tree JSON
    with open(tree_path, "r") as f:
        tree_data = json.load(f)

    tree = tree_data["structure"]

    # Build flat lookup map
    node_map = create_node_mapping(tree)

    # Step 1: Tree search
    search_result = await tree_search(question, tree)
    
    node_list = search_result.get("node_list", [])
    thinking = search_result.get("thinking", "LLM did not provide reasoning.")
    
    print("Relevant nodes:", node_list)
    print("Reasoning:", thinking[:500] + "..." if len(thinking) > 500 else thinking)

    # Step 2: Extract context
    context = extract_context(node_list, node_map)

    # Step 3: Answer
    answer = await answer_question(question, context)
    print("\nAnswer:", answer)
    return answer


# --- Run ---
if __name__ == "__main__":
    asyncio.run(query(
        question="What documents are mandatory for bidders to submit?",
        tree_path="results/Tender Doc for Testing_structure.json"
    ))

# Questions
# What is the name of the organization issuing this tender?
# What is the main objective of this tender?
# What type of systems is the contractor required to handle?
# What are the key components included in the electrical infrastructure? (list any four)
# Where will the project be executed?
# What is the required Earnest Money Deposit (EMD) amount?
# What are the acceptable forms of submitting the EMD?
# What is the minimum annual turnover required for bidders?
# How many similar projects must the bidder have completed, and within what time period?
# What is the total duration of the project?