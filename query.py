import json
import asyncio
import openai

# --- Configuration ---
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
MODEL = "gpt-4.1"  # as used in the official cookbook


# --- Step 1: LLM helper ---
async def call_llm(prompt, model=MODEL):
    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()


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
    return json.loads(response)


# --- Step 4: Extract text from identified nodes ---
def extract_context(node_list, node_map):
    context = ""
    for node_id in node_list:
        if node_id in node_map and "text" in node_map[node_id]:
            context += node_map[node_id]["text"] + "\n\n"
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
    print("Relevant nodes:", search_result["node_list"])
    print("Reasoning:", search_result["thinking"])

    # Step 2: Extract context
    context = extract_context(search_result["node_list"], node_map)

    # Step 3: Answer
    answer = await answer_question(question, context)
    print("\nAnswer:", answer)
    return answer


# --- Run ---
if __name__ == "__main__":
    asyncio.run(query(
        question="What are the main conclusions?",
        tree_path="results/your_document_structure.json"
    ))