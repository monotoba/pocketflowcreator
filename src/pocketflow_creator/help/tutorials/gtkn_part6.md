# Part 6 — Advanced Nodes: RAG, Agent, Subflow

Part 6 covers the three most powerful and architecturally significant node types in PocketFlow Creator. The **RAG Node** combines vector search with LLM generation to produce answers grounded in a document collection. The **Agent Node** implements an autonomous decision loop where an LLM chooses which tools to call, calls them, observes the results, and repeats until it has an answer. The **Subflow Node** lets you embed one complete graph inside another as a single node, enabling modular, reusable pipeline construction.

These nodes build on everything from Parts 1–5. Complete all previous parts before starting here.

---

## Tutorial T-N18: The RAG Node

### What it does

The **RAG Node** (Retrieval-Augmented Generation) implements the full RAG pipeline in a single node. When it executes, it performs four sub-steps in order: (1) **Embed** — converts the query into a vector using an embedding model; (2) **Search** — queries a vector store for the most similar document chunks; (3) **Build Context** — assembles the retrieved chunks into a context string; (4) **Generate** — sends the context plus the original query to an LLM and returns the answer. The result is an answer that is grounded in your document collection rather than in the LLM's parametric memory alone.

### Use cases

- Question answering over a private document corpus (internal wikis, policy documents, codebases)
- Customer support bots that answer from a product knowledge base
- Research assistants that cite sources from an uploaded paper collection
- Any scenario where LLM hallucination must be reduced by grounding answers in real documents

### What you'll build

A five-node flow — **Start → HumanInput(question) → RAGSearch → LLMAnswer → Stop** — where the user asks a question, the RAG Node retrieves relevant document chunks, and an LLM generates a grounded answer.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part6_rag`. This tutorial uses MockProvider for the LLM and a mock vector store, so no real external services are required.

**Step 2: Build the canvas**

Drag and wire the following nodes:

1. **Start Node**
2. **Human Input Node** — configure: `prompt` = "What would you like to know?", `output_key` = `question`
3. **RAG Node** — from the **Component Palette**, AI category; rename to `RAGSearch`
4. **Basic Node** — rename to `LLMAnswer`
5. **Stop Node**

Wire: Start →(default)→ HumanInput →(default)→ RAGSearch →(default)→ LLMAnswer →(default)→ Stop.

**Step 3: Configure the RAG Node**

Click the **RAGSearch** node and set these properties in the **Object Inspector**:

- **collection_name**: `my_documents` — the name of the vector store collection to search. In MockProvider mode, this is a named identifier; with a real vector database (Chroma, Qdrant, Weaviate, etc.) this maps to a collection or index.
- **embedding_model**: `text-embedding-ada-002` (or leave blank for the project default) — the model used to embed the query into a vector.
- **top_k**: `3` — how many document chunks to retrieve. More chunks provide more context but increase the LLM prompt size and cost.
- **input_key**: `question` — the shared store key containing the user's query (placed there by the Human Input Node).
- **output_key**: `context` — the retrieved document chunks are assembled into a context string and stored here.

> ⚠️ **Note:** In MockProvider mode, the RAG Node skips the real embedding and vector search and instead returns placeholder context text. This is sufficient for testing your flow's structure. To use real retrieval, configure a vector database provider in **Tools > Provider Manager** and ensure your collection is populated with embedded documents before running the flow.

**Step 4: Understand the four RAG sub-steps**

Before writing code, it helps to understand what the RAG Node does internally during each run:

1. **Embed**: Reads `shared["question"]`, calls the embedding model, receives a numerical vector (e.g. 1536 floats for `text-embedding-ada-002`).
2. **Search**: Submits the query vector to the configured vector store collection. The store returns the `top_k` most semantically similar document chunks with their similarity scores.
3. **Build Context**: Formats the retrieved chunks into a readable context string: `"[Source 1]\n...\n[Source 2]\n..."`. This string is stored in `shared["context"]`.
4. **Generate**: You are responsible for passing `shared["context"]` to a downstream LLM node — the RAG Node itself only does retrieval, not generation. This separation lets you choose how to use the context: you might pass it to an LLM Prompt Node, a JSON LLM Node, or even back to a Human Review Node first.

**Step 5: Write the LLMAnswer code**

Since the RAG Node only retrieves context (it does not call the LLM), a downstream node must combine the context with the question and generate the answer. Select **LLMAnswer** and open the **Python editor tab**:

```python
from pocketflow import Node

class LLMAnswer(Node):
    """Combines the RAG context with the question and generates an answer.
    
    In a real flow, replace this Basic Node with an LLM Prompt Node
    configured with:
        prompt: "Answer the question using ONLY the provided context.
                 Context: {{context}}
                 Question: {{question}}
                 Answer:"
    For this tutorial, we simulate the LLM call.
    """

    def prep(self, shared):
        # Gather both the context (from RAG) and the question (from HumanInput).
        return {
            "context": shared.get("context", "(no context retrieved)"),
            "question": shared.get("question", "(no question)"),
        }

    def exec(self, prep_res):
        context  = prep_res["context"]
        question = prep_res["question"]
        # In a real flow this would be an LLM call. Here we simulate it.
        print(f"\nQuestion: {question}")
        print(f"\nRetrieved Context:\n{context}")
        simulated_answer = (
            f"Based on the retrieved documents, the answer to '{question}' is: "
            "[MockProvider: insert LLM-generated answer grounded in context here]"
        )
        return simulated_answer

    def post(self, shared, prep_res, exec_res):
        shared["answer"] = exec_res
        print(f"\nAnswer: {exec_res}")
        return "default"
```

> 💡 **Tip:** In production, replace the `LLMAnswer` Basic Node with an **LLM Prompt Node** configured with `prompt_type: string` and a prompt like `"Answer the question using ONLY the provided context. Context: {{context}}\nQuestion: {{question}}\nAnswer:"`. Using a dedicated LLM Prompt Node gives you access to the full model configuration (temperature, max_tokens, system prompt) without writing any code.

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Type a question when the Human Input dialog appears. The **Run Log tab** will show the retrieved context (placeholder in MockProvider mode) and the simulated answer. The **Shared Store tab** shows:

```
question: "What is PocketFlow?"
context:  "[MockProvider] Retrieved 3 chunks from my_documents..."
answer:   "Based on the retrieved documents..."
```

**Step 7: Populate a real collection**

When you are ready to use real retrieval, you will need to: (1) choose a vector database (Chroma is easiest for local development), (2) embed your documents using the same embedding model you configured in the RAG Node, (3) store the embedded chunks in a collection named `my_documents`, and (4) change the provider in **Tools > Provider Manager** from MockProvider to your real embedding and LLM providers.

### What you learned

- The RAG Node performs embed → search → build context in sequence; generation is left to a downstream node
- `collection_name`, `embedding_model`, and `top_k` are the three key configuration properties
- MockProvider simulates retrieval for flow topology testing without a real vector database
- The retrieved context is stored in `shared[output_key]` as a formatted string for the LLM to use
- Combining a RAG Node with an LLM Prompt Node downstream is the production-ready RAG pattern

---

## Tutorial T-N19: The Agent Node

### What it does

The **Agent Node** implements an autonomous tool-using agent loop. When it executes, it enters a reasoning loop: it sends the current state (question, conversation history, tool results so far) to an LLM; the LLM decides which registered tool to call next (or that no more tools are needed and the answer is ready); the agent calls the chosen tool, observes the result, appends it to the conversation, and loops again. This continues until the LLM signals that it has enough information to answer the original question, or until `max_iterations` is reached.

### Use cases

- Research tasks that require searching multiple sources and combining the results
- Math or logic problems that benefit from a calculator tool
- Code generation where the agent can test its own output and fix errors
- Any task where the correct sequence of tool calls cannot be determined in advance

### What you'll build

A three-node flow — **Start → AgentOrchestrator → Stop** — where the Agent Node uses registered `web_search` and `calculator` tools to answer a compound question.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part6_agent`.

**Step 2: Create the tools**

In the **Project Explorer**, create `tools.py` in the project root and define two tool functions:

```python
from pocketflow import tool

@tool
def web_search(query: str) -> str:
    """Search the web for information on a topic.
    
    Args:
        query: The search query string.
        
    Returns:
        A string of simulated search results.
    """
    # In production, replace this with a real search API call
    # (e.g., Serper, Tavily, Bing Search API).
    return (
        f"[MockSearch results for '{query}']: "
        "PocketFlow is an open-source Python framework for building LLM workflows. "
        "It was created by The Pocket team and released in 2024. "
        "It supports async, batch, and agent patterns."
    )


@tool
def calculator(expression: str) -> float:
    """Evaluate a mathematical expression and return the result.
    
    Args:
        expression: A Python-compatible math expression, e.g. '2 + 2' or '3.14 * 5 ** 2'.
        
    Returns:
        The numeric result of evaluating the expression.
    """
    # WARNING: In production, use a safe math parser (e.g., simpleeval)
    # rather than eval() to prevent code injection.
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return float(result)
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"
```

Save with **Ctrl+S**.

> ⚠️ **Note:** The `eval()` call above is acceptable for local development tutorials but is a security risk in any public-facing application. In production, replace it with a safe expression evaluator library such as `simpleeval` or implement a dedicated math parser.

**Step 3: Build the canvas**

Drag and wire:

1. **Start Node**
2. **Agent Node** — from the **Component Palette**, AI category; rename to `AgentOrchestrator`
3. **Stop Node**

Wire: Start →(default)→ AgentOrchestrator →(default)→ Stop.

**Step 4: Configure the Agent Node**

Click the **AgentOrchestrator** node and set these properties in the **Object Inspector**:

- **Title**: `AgentOrchestrator`
- **tools**: `web_search, calculator` (comma-separated list of tool names registered with `@tool`)
- **max_iterations**: `5` — the agent will make at most 5 tool calls before returning whatever answer it has
- **prompt**: `Answer the user's question using the available tools. Question: {{question}}`
- **input_key**: `question`
- **output_key**: `answer`

> 💡 **Tip:** The `max_iterations` property is your safety valve. An agent that cannot find an answer will keep calling tools indefinitely without it. Set it conservatively — `5` is generous for most question-answering tasks. Complex multi-step research might warrant `10–15`, but anything above `20` is usually a sign that the agent's tools or prompt need improvement.

**Step 5: Seed the Start Node**

Select the **Start Node** and open the **Python editor tab**:

```python
from pocketflow import Node

class StartNode(Node):

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Provide a question the agent will research and answer.
        shared["question"] = (
            "What is PocketFlow and approximately how many nodes does it support? "
            "Also, what is 42 times 13?"
        )
        return "default"
```

**Step 6: Understand the agent loop**

The Agent Node's internal loop looks like this:

```
1. Send: (question + tool list + conversation history) → LLM
2. LLM responds with: chosen tool name + arguments  OR  final answer
3. If final answer: store in shared[output_key], return "default"
4. If tool call: call tool(args), append result to conversation
5. Increment iteration counter; if >= max_iterations, return "default"
6. Go to step 1
```

The LLM decides the sequence of tool calls. The agent framework handles the loop mechanics. You just provide the tools and the initial question.

**Step 7: How tool discovery works**

When the Agent Node runs, it inspects the `tools` property and looks up each tool name in the Tool Registry (populated by importing all `@tool`-decorated functions from `tools.py` files). For each tool, it reads the function's docstring and type annotations to generate a tool description that the LLM can understand. This is why well-written docstrings are important for `@tool` functions — the LLM reads them to decide when to use each tool.

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. With MockProvider the agent will simulate tool calls and return a mock answer. With a real LLM (Ollama with a capable model like `llama3.1`), the agent will actually call `web_search` and `calculator` and synthesise a real answer.

Check the **Run Log tab** to see the agent's tool calls and the **Shared Store tab** for:

```
question: "What is PocketFlow and approximately how many nodes..."
answer:   "[Agent answer combining search results and calculation]"
```

### What you learned

- The Agent Node runs a think → choose tool → call tool → observe → repeat loop driven by an LLM
- `tools` lists `@tool` function names; the agent discovers capabilities from docstrings and type annotations
- `max_iterations` is a mandatory safety valve to prevent infinite loops
- The agent decides the sequence of tool calls — you cannot predict or hard-code it in advance
- Well-written `@tool` docstrings are critical because the LLM reads them to decide when to use each tool

---

## Tutorial T-N20: The Subflow Node

### What it does

The **Subflow Node** embeds a complete, separate PocketFlow graph as a single node within the current graph. When the runner reaches a Subflow Node, it pauses the parent flow, loads and executes the referenced graph from start to finish, and then resumes the parent flow. The shared store is automatically available to the subflow — it reads the same dict the parent flow has been building — and any keys the subflow writes to the shared store are visible to subsequent nodes in the parent flow when it resumes.

### Use cases

- Creating reusable building blocks (a "standardise text" subflow, a "validate and log" subflow) that many parent flows can share
- Breaking a large, complex flow into manageable, independently testable sub-graphs
- Implementing a library of standard pipeline stages that can be versioned and shared across projects
- Reducing canvas clutter by collapsing a multi-node sequence into a single named Subflow Node

### What you'll build

Two flows: (a) a **GreetingSubflow** graph that captures a user's name and writes a greeting; and (b) a **MainFlow** graph with a Subflow Node that calls the GreetingSubflow, followed by a Logger node that logs the greeting from the shared store.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part6_subflow`. The project opens with one graph (`main.pfcgraph.yaml`) on the canvas.

**Step 2: Create the GreetingSubflow graph**

You will create a second graph file for the subflow. In the **Project Explorer**, right-click the `graphs/` folder (or the project root if no `graphs/` folder exists) and choose **New Graph**. Name it `greeting_subflow`. A new tab opens on the canvas showing an empty `greeting_subflow.pfcgraph.yaml`.

> 💡 **Tip:** Organise your subflow graphs in a `graphs/` subdirectory to keep the project root clean. The Subflow Node's `subflow_ref` property uses paths relative to the project root, so `graphs/greeting_subflow.pfcgraph.yaml` is a valid reference even if the calling graph is in the root.

**Step 3: Build the GreetingSubflow graph**

On the `greeting_subflow` canvas tab, drag and wire:

1. **Start Node**
2. **Human Input Node** — configure: `prompt` = "What is your name?", `output_key` = `name`
3. **Basic Node** — rename to `GreetingBuilder`
4. **Stop Node**

Wire: Start →(default)→ HumanInput →(default)→ GreetingBuilder →(default)→ Stop.

Write the GreetingBuilder code:

```python
from pocketflow import Node

class GreetingBuilder(Node):
    """Builds a personalised greeting from shared['name']."""

    def prep(self, shared):
        return shared.get("name", "Friend")

    def exec(self, prep_res):
        return f"Hello, {prep_res}! This greeting was generated by a subflow."

    def post(self, shared, prep_res, exec_res):
        # Write the greeting to the shared store.
        # Because this is a subflow, the parent flow will see
        # shared["greeting"] after the Subflow Node completes.
        shared["greeting"] = exec_res
        return "default"
```

Save with **Ctrl+S**. Validate the subflow graph: **Ctrl+Shift+V**. It should pass.

**Step 4: Build the MainFlow graph**

Switch to the `main.pfcgraph.yaml` tab (click it in the **Project Explorer** or use the canvas tab). Build:

1. **Start Node**
2. **Subflow Node** — from the **Component Palette**, Flow Control category; rename to `GreetingSubflowNode`
3. **Basic Node** — rename to `Logger`
4. **Stop Node**

Wire: Start →(default)→ GreetingSubflowNode →(default)→ Logger →(default)→ Stop.

**Step 5: Configure the Subflow Node**

Click the **GreetingSubflowNode** to select it. In the **Object Inspector**:

- **subflow_ref**: `graphs/greeting_subflow.pfcgraph.yaml` — the path to the subflow graph file, relative to the project root.
- **Title**: `GreetingSubflowNode`

This is the only configuration required. At runtime, the runner will load and execute the referenced graph when it reaches this node.

> ⚠️ **Note:** The `subflow_ref` path must be relative to the project root, not to the calling graph's location. If the subflow file is at `<project_root>/graphs/greeting_subflow.pfcgraph.yaml`, the `subflow_ref` property should be `graphs/greeting_subflow.pfcgraph.yaml`. Using an absolute path will break portability when the project is moved or shared.

**Step 6: Write the Logger code**

Select **Logger** and open the **Python editor tab**:

```python
from pocketflow import Node

class Logger(Node):
    """Reads the greeting produced by the subflow and logs it."""

    def prep(self, shared):
        # The subflow wrote shared["greeting"] — we read it here
        # in the parent flow, demonstrating shared store continuity.
        return shared.get("greeting", "(no greeting — did the subflow run?)")

    def exec(self, prep_res):
        print(f"Logger received from subflow: {prep_res}")
        return prep_res

    def post(self, shared, prep_res, exec_res):
        shared["logged_greeting"] = exec_res
        return "default"
```

**Step 7: Understand shared store continuity**

The shared store is a single Python dict that travels through the entire execution, including into and out of subflows. When the Subflow Node begins execution, it passes the *same* shared store dict to the subflow's Start Node. Any key the subflow writes (such as `shared["greeting"]`) is immediately visible in the parent flow after the Subflow Node completes. There is no copy, no merge, and no namespace isolation — the subflow and parent flow share the same dict object.

This design has two implications:

- **Benefit**: Data flows naturally between parent and subflow without any special "output port" configuration.
- **Risk**: If the subflow writes a key that the parent flow also uses (name collision), the subflow's write overwrites the parent's value. Choose descriptive key names to avoid collisions.

**Step 8: Validate both graphs and run**

Validate the main flow: switch to `main.pfcgraph.yaml` and press **Ctrl+Shift+V**. Then press **F5**. The runner executes the main flow, reaches the Subflow Node, switches to `greeting_subflow.pfcgraph.yaml`, prompts for your name via the Human Input dialog, builds the greeting, writes it to `shared["greeting"]`, returns to the main flow, and passes `shared["greeting"]` to the Logger.

Check the **Shared Store tab** after the run:

```
name:             "Alice"
greeting:         "Hello, Alice! This greeting was generated by a subflow."
logged_greeting:  "Hello, Alice! This greeting was generated by a subflow."
```

All three keys are visible in the same flat shared store, confirming that the subflow and parent flow share the same dict.

> 💡 **Tip:** Subflows can call other subflows — nesting is supported. However, be careful with deep nesting (more than 2–3 levels) as it becomes hard to debug when something goes wrong. Prefer flat composition (one level of subflows in the main flow) over deep nesting.

**Step 9: Understand the broader use of Subflow Nodes**

Consider a production document-processing pipeline that needs to: (1) validate an incoming document, (2) extract entities, (3) classify the document type, and (4) route to different handlers. Each of these four stages could be a multi-node subflow graph tested independently. The main flow then becomes four Subflow Nodes, each with a clear label, making the overall pipeline architecture immediately obvious to anyone reading the canvas. This is the primary architectural benefit of the Subflow Node: it lets you build large pipelines from tested, reusable components rather than putting everything in one enormous graph.

### What you learned

- The Subflow Node runs a separate graph file and resumes the parent flow when it finishes
- `subflow_ref` is a project-root-relative path to the subflow graph file (`.pfcgraph.yaml`)
- The shared store is the same dict in parent and subflow — writes in the subflow are visible in the parent
- Key name collisions between parent and subflow can cause unexpected overwrites — use descriptive names
- Subflow Nodes enable modular, reusable pipeline construction and keep large graphs readable

---

## Congratulations — Series Complete!

You have now built 20 mini-flows covering every node type in PocketFlow Creator's **Component Palette**. Here is a quick summary of what you have learned:

| Part | Nodes | Key Concept |
|------|-------|-------------|
| 1 | Start, Stop, Basic | prep/exec/post lifecycle; shared store basics |
| 2 | File Reader, File Writer, Python Tool | Disk I/O; `@tool` functions and the Tool Registry |
| 3 | Router, Human Review, Human Input | Branching; human-in-the-loop checkpoints |
| 4 | LLM Prompt, JSON LLM, Classifier, Judge | LLM integration; structured output; quality gates |
| 5 | Batch, Async, Async Batch, Async Parallel Batch | Collection processing; concurrency patterns |
| 6 | RAG, Agent, Subflow | Advanced patterns: retrieval, autonomy, composition |

**Recommended next steps:**

- Work through the [PocketFlow Patterns tutorials](part2_patterns.md) to see these node types combined in realistic application flows.
- Try the [Exercises](part4_exercises.md) to build complete applications from scratch.
- Read the [Node Type Wizard help page](../context/node_type_wizard.md) to learn how to create your own custom node types that appear in the palette alongside the built-ins.

---

[← Previous Part: Batch and Async Nodes](gtkn_part5.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
