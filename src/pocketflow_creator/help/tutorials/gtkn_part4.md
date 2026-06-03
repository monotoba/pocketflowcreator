# Part 4 — LLM Nodes: LLM Prompt, JSON LLM, Classifier, Judge

Part 3 showed you how to branch flows and capture human input. Part 4 introduces the nodes that integrate Large Language Models (LLMs) into your pipelines. These four nodes — **LLM Prompt**, **JSON LLM**, **Classifier**, and **Judge** — cover the most common LLM usage patterns: free-form text generation, structured data extraction, multi-class routing, and quality evaluation.

All LLM nodes support the **MockProvider** out of the box, which means you can build and test your full flow topology without needing a real LLM service configured. Once your graph is wired and validated, you swap the provider to Ollama or another backend and run against a real model.

Complete Parts 1–3 before starting here.

---

## Tutorial T-N10: The LLM Prompt Node

### What it does

The **LLM Prompt Node** sends a text prompt to a configured LLM and stores the plain-text response in the shared store. It is the simplest and most direct LLM integration: you provide a prompt template, the node interpolates any `{{key}}` placeholders from the shared store, calls the LLM, and stores the result. This is the node to reach for whenever you need free-form text generation — summaries, rewrites, explanations, creative text, or any other open-ended language task.

### Use cases

- Summarising a document loaded by a File Reader Node
- Generating a draft blog post from bullet points in the shared store
- Translating text from one language to another
- Asking follow-up questions about data already in the pipeline

### What you'll build

A three-node flow — **Start → LLMPrompt → Stop** — where the Start Node seeds `shared["topic"]` and the LLM Prompt Node generates a fun fact about that topic, storing the response in `shared["fact"]`.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part4_llm_prompt`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **LLM Prompt Node** — from the **Component Palette**, AI category
3. **Stop Node**

Wire: Start →(default)→ LLMPrompt →(default)→ Stop.

**Step 3: Seed the shared store from the Start Node**

Select the **Start Node** and open the **Python editor tab**. Add code to seed the topic:

```python
from pocketflow import Node

class StartNode(Node):

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Seed the topic that the LLM Prompt Node will use.
        # The LLM node's prompt uses {{topic}} interpolation,
        # so this key must be present before the LLM node runs.
        shared["topic"] = "penguins"
        return "default"
```

**Step 4: Configure the LLM Prompt Node**

Click the **LLM Prompt Node** to select it. In the **Object Inspector**, set these properties:

- **Title**: `FactGenerator`
- **prompt_type**: `string` — this means you will type the prompt directly in the inspector, as opposed to loading it from a `.md` file.
- **prompt_file** (shown as "Prompt" or "prompt_file" depending on version): `Tell me a fun fact about {{topic}}.` — the `{{topic}}` placeholder will be replaced at runtime with the value of `shared["topic"]` before the prompt is sent to the LLM.
- **output_key**: `fact` — the LLM's text response will be stored in `shared["fact"]`.
- **model**: Leave blank to use the project default (MockProvider during testing).

> 💡 **Tip:** The `{{key}}` interpolation syntax allows any key from the shared store to be embedded into the prompt. You can use multiple placeholders in a single prompt: `"Compare {{item_a}} and {{item_b}} in terms of {{criteria}}."` All three keys must be present in the shared store before the LLM node runs, or the interpolation will raise a `KeyError`.

**Step 5: Understand prompt_type: string vs path**

The `prompt_type` property has two values:

- **`string`**: The prompt text is written directly in the `prompt_file` inspector field. Good for short, self-contained prompts.
- **`path`**: The `prompt_file` field is treated as a relative path to a Markdown file (e.g., `prompts/fact_prompt.md`). The file is read at runtime and its contents are used as the prompt. Good for long, carefully formatted prompts that benefit from version control and standalone editing.

For this tutorial, `string` is fine. In production flows, `path` is recommended for prompts longer than a few sentences.

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Because no real LLM is configured, the MockProvider returns a placeholder response. Switch to the **Shared Store tab**:

```
topic: "penguins"
fact: "[MockProvider response to: Tell me a fun fact about penguins.]"
```

> ⚠️ **Note:** The MockProvider is for testing flow *topology* — it validates that nodes are wired correctly and data flows to the right places. To see a real LLM response, configure a provider via **Tools > Provider Manager** (see [Provider Setup Guide](../../docs/13_provider_setup.md) for detailed instructions). Then change the **model** property to a real model name (e.g., `qwen2.5-coder:14b` for Ollama, `gpt-4o-mini` for OpenAI). Re-run the flow; this time `shared["fact"]` will contain a genuine AI-generated response.

**Step 7: Try a path-based prompt**

Create a file called `prompts/fact_prompt.md` in the **Project Explorer** (right-click, New File, enter the path). Write:

```markdown
Tell me a fun fact about {{topic}}.

Focus on something surprising that most people do not know.
Keep your response to two or three sentences.
```

Then change the LLM Prompt Node's `prompt_type` to `path` and `prompt_file` to `prompts/fact_prompt.md`. Re-run. The node reads the file, interpolates `{{topic}}`, and sends the full text to the LLM.

### What you learned

- The LLM Prompt Node sends a prompt to an LLM and stores the text response in `shared[output_key]`
- `{{key}}` placeholders in the prompt are replaced with `shared[key]` values at runtime
- `prompt_type: string` embeds the prompt in the inspector; `prompt_type: path` loads it from a file
- The MockProvider lets you test flow structure without a real LLM configured
- Switch to a real provider via **Tools > Provider Manager** when ready for live testing

---

## Tutorial T-N11: The JSON LLM Node

### What it does

The **JSON LLM Node** is like the LLM Prompt Node, but it instructs the LLM to respond with structured JSON rather than free-form text, and it automatically parses that JSON into a Python dict. You provide a JSON Schema describing the expected output shape; the node includes this schema in the system prompt and validates the LLM's response against it. The result stored in `shared[output_key]` is a Python dict, not a string — ready for immediate programmatic use by downstream nodes.

### Use cases

- Extracting structured data from unstructured text (names, dates, prices from an email)
- Having the LLM fill in a data record from a natural-language description
- Building ETL pipelines where an LLM transforms messy input into clean structured records
- Generating typed configuration objects from human-readable descriptions

### What you'll build

A three-node flow — **Start → JSONExtractor → Stop** — where the Start Node seeds `shared["text"]` with a text snippet and the JSON LLM Node extracts a name and age into a structured dict stored in `shared["person"]`.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part4_json_llm`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **JSON LLM Node** — from the **Component Palette**, AI category
3. **Stop Node**

Wire: Start →(default)→ JSONExtractor →(default)→ Stop.

**Step 3: Seed the shared store**

Select the Start Node and open the **Python editor tab**:

```python
from pocketflow import Node

class StartNode(Node):

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Provide some unstructured text for the LLM to parse.
        shared["text"] = (
            "My name is Sarah Chen and I am 34 years old. "
            "I work as a software engineer in San Francisco."
        )
        return "default"
```

**Step 4: Configure the JSON LLM Node**

Click the **JSON LLM Node** and set these properties in the **Object Inspector**:

- **Title**: `JSONExtractor`
- **prompt_type**: `string`
- **prompt_file** / **prompt**: `Extract the person's name and age from the following text: {{text}}`
- **output_key**: `person`
- **schema**: Paste the following JSON Schema:

```json
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "age":  { "type": "integer" }
  },
  "required": ["name", "age"]
}
```

The schema tells the node (and the LLM) exactly what shape of JSON to expect. The node will validate the LLM's response against this schema and raise an error if it does not conform.

> 💡 **Tip:** Keep JSON schemas simple. LLMs produce more reliable structured output with flat schemas containing 3–5 fields than with deeply nested schemas with 20+ fields. If you need complex structures, consider chaining two JSON LLM Nodes — the first extracts top-level fields, the second extracts nested details.

**Step 5: Understand why structured output matters**

When a downstream node needs to act on an extracted name (e.g., look it up in a database) it needs `shared["person"]["name"]` to be a proper Python string, not a substring extracted from a plain-text LLM response. The JSON LLM Node gives you that guarantee. Without it, you would need a Basic Node to parse the LLM's response with fragile regex or string splitting, which breaks whenever the LLM phrases its answer differently.

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Check the **Shared Store tab**:

```
text: "My name is Sarah Chen and I am 34 years old..."
person: {"name": "Sarah Chen", "age": 34}
```

In MockProvider mode the node returns a dummy dict. With a real LLM, `person` will be properly populated.

> ⚠️ **Note:** LLMs occasionally produce malformed JSON even when instructed not to. The JSON LLM Node retries the call up to a configurable number of times (default: 3) and raises an error if it still cannot parse a valid JSON response. If you encounter persistent parsing failures, simplify the schema or add explicit instructions in the prompt such as "Respond with ONLY the JSON object, no markdown code fences, no explanatory text."

**Step 7: Access the parsed dict downstream**

To see how a downstream Basic Node would use the parsed dict, add a **Printer** node after JSONExtractor:

```python
def prep(self, shared):
    return shared.get("person", {})

def exec(self, prep_res):
    name = prep_res.get("name", "Unknown")
    age  = prep_res.get("age", 0)
    print(f"Extracted: {name}, age {age}")
    return None

def post(self, shared, prep_res, exec_res):
    return "default"
```

### What you learned

- The JSON LLM Node instructs the LLM to return JSON and parses the response into a Python dict
- The `schema` property defines the expected output shape using JSON Schema syntax
- Structured output eliminates fragile post-processing of plain-text LLM responses
- Downstream nodes access the parsed dict like any other Python dict: `shared["person"]["name"]`
- Keep schemas simple; chain multiple JSON LLM Nodes for complex structures

---

## Tutorial T-N12: The Classifier Node

### What it does

The **Classifier Node** is an LLM-powered multi-class router. You write a prompt that describes a classification task, declare the possible output classes as the node's **Actions**, and the LLM returns exactly one of those class labels. Each class label becomes both an output port on the node tile and a valid return value from `post()`. This is the node to use when you need the LLM to make a categorical decision and route the flow accordingly.

### Use cases

- Sentiment classification (positive / negative / neutral)
- Intent detection (question / complaint / praise / refund-request)
- Topic routing (technology / sports / finance / health)
- Priority assignment (urgent / normal / low) for incoming requests

### What you'll build

A six-node flow — **Start → HumanInput → SentimentClassifier → (positive: PositiveReply, negative: NegativeReply, neutral: NeutralReply)** — where the user types a sentence and the LLM classifies its sentiment.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part4_classifier`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **Human Input Node** — configure: `prompt` = "Type a sentence to classify:", `output_key` = `user_input`
3. **Classifier Node** — from the **Component Palette**, AI category
4. **Stop Node** — rename to `PositiveReply`
5. **Stop Node** — rename to `NegativeReply`
6. **Stop Node** — rename to `NeutralReply`

**Step 3: Configure the Classifier Node**

Click the **Classifier Node** and set these properties in the **Object Inspector**:

- **Title**: `SentimentClassifier`
- **prompt_type**: `string`
- **prompt_file** / **prompt**: `Classify the sentiment of the following text. Respond with ONLY one word — positive, negative, or neutral — and nothing else: {{user_input}}`
- **Actions**: `positive`, `negative`, `neutral` (add all three; each becomes an output port)
- **output_key**: `sentiment` (the LLM's chosen class label is also stored in the store for auditing)

The key insight here is that the **Actions** field serves double duty: it defines the output ports on the canvas *and* it tells the LLM which words are acceptable responses. The Classifier Node includes the action labels in its system prompt instruction, constraining the LLM's output to one of those exact strings.

> 💡 **Tip:** The fewer the classes, the more reliable the classification. Binary classifiers (two classes) are nearly always accurate. As you add more classes, reliability drops — especially for classes with subtle distinctions. If you need more than five classes, consider a two-stage approach: a coarse Classifier followed by a fine-grained Classifier for ambiguous cases.

**Step 4: Wire the classifier output ports**

Connect:

1. Start →(default)→ HumanInput
2. HumanInput →(default)→ SentimentClassifier
3. SentimentClassifier →(positive)→ PositiveReply
4. SentimentClassifier →(negative)→ NegativeReply
5. SentimentClassifier →(neutral)→ NeutralReply

**Step 5: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Type "I absolutely love this product!" when the Human Input dialog appears. With a real LLM, the Classifier should route to `PositiveReply`. With MockProvider, it will route to one of the actions deterministically.

> ⚠️ **Note:** Unlike the Router Node — where *you* write the branching logic in Python — the Classifier Node delegates the decision to the LLM. This makes it more flexible (no code to maintain) but less deterministic. Always test your Classifier with edge cases (very short inputs, mixed signals, sarcasm) before deploying to production.

**Step 6: Understand the difference between Classifier and Router**

- **Router Node**: You write deterministic Python logic (`if score > 0: return "positive"`). Reliable, fast, no LLM cost.
- **Classifier Node**: The LLM makes the decision based on semantics. Handles nuanced natural language without you writing rules.

Use a Router when the branching condition can be expressed as simple code. Use a Classifier when the decision requires language understanding.

### What you learned

- The Classifier Node uses an LLM to choose one of its declared actions based on input text
- The **Actions** field defines both the output ports and the LLM's allowed response values
- The LLM is prompted to return exactly one action label, which routes the flow
- Use Classifier for natural language decisions; use Router for deterministic code-based decisions
- Fewer classes produce more reliable classification

---

## Tutorial T-N13: The Judge Node

### What it does

The **Judge Node** uses an LLM to evaluate something — the quality, correctness, safety, or any other measurable property of content in the shared store — and returns either `"pass"` or `"fail"`. It is a specialised Classifier with exactly two classes. Its primary use case is as a quality gate in an automated pipeline: generate content with an LLM Prompt Node, evaluate it with a Judge Node, and loop back to regenerate if the verdict is `"fail"`.

### Use cases

- Quality checking LLM-generated text before publishing
- Verifying that extracted data meets validation criteria
- Safety screening content for harmful or inappropriate material
- Confirming that a summarisation captures all required key points

### What you'll build

A looping flow — **Start → LLMWriter → JudgeQuality → (pass: Stop, fail: Reviser → loop back to LLMWriter)** — where the LLM writes a short text, the Judge evaluates its quality, and the flow loops until the Judge is satisfied.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part4_judge`.

**Step 2: Build the canvas**

Drag and position:

1. **Start Node** — left
2. **LLM Prompt Node** — rename to `LLMWriter`
3. **Judge Node** — from the **Component Palette**, AI category; rename to `JudgeQuality`
4. **Stop Node** — upper right (the "pass" exit)
5. **Basic Node** — rename to `Reviser` — lower right (increments attempts, loops back)

**Step 3: Configure LLMWriter**

- **prompt**: `Write a compelling two-sentence description of a product for: {{topic}}`
- **output_key**: `draft`

**Step 4: Configure JudgeQuality**

Click the **Judge Node** and set:

- **Title**: `JudgeQuality`
- **prompt**: `Is the following product description high quality, compelling, and free of grammatical errors? Respond with ONLY 'pass' or 'fail': {{draft}}`
- **Actions**: Confirm `pass` and `fail` are both listed (these are the Judge Node's defaults)
- **input_key**: `draft`

> 💡 **Tip:** The Judge's prompt should be specific about what "quality" means. A vague prompt like "Is this good?" produces unreliable verdicts. A specific prompt like "Does this text contain at least two concrete facts and no spelling errors?" gives the LLM clear criteria to evaluate against.

**Step 5: Wire the flow**

Connect:

1. Start →(default)→ LLMWriter
2. LLMWriter →(default)→ JudgeQuality
3. JudgeQuality →(pass)→ Stop
4. JudgeQuality →(fail)→ Reviser
5. Reviser →(default)→ LLMWriter  ← the loop

**Step 6: Seed the Start Node and write Reviser code**

Start Node:

```python
def post(self, shared, prep_res, exec_res):
    shared["topic"] = "noise-cancelling wireless headphones"
    shared["attempt"] = 0
    return "default"
```

Reviser:

```python
from pocketflow import Node

class Reviser(Node):
    """Tracks revision attempts and adds context for the next LLM write."""

    def prep(self, shared):
        return shared.get("attempt", 0)

    def exec(self, prep_res):
        return prep_res + 1

    def post(self, shared, prep_res, exec_res):
        shared["attempt"] = exec_res
        if exec_res >= 3:
            # Safety valve: after 3 failed attempts, accept what we have.
            print(f"Max attempts ({exec_res}) reached. Accepting draft.")
            shared["draft"] = shared.get("draft", "") + " [Auto-accepted after max retries]"
        print(f"Judge rejected draft. Attempt {exec_res}.")
        return "default"
```

> ⚠️ **Note:** Always include a maximum-iterations safeguard in retry loops. Without one, a Judge that is impossible to satisfy (or a misconfigured prompt) will cause the flow to loop indefinitely. The `attempt` counter in the Reviser above is a simple but effective safeguard — once three attempts have been made, the flow can proceed regardless of the Judge's verdict by adjusting the Reviser to return a special action that bypasses the Judge.

**Step 7: Understand Judge vs Classifier**

- **Classifier Node**: N-way branching, where N ≥ 2. Used when you need to route to more than two different downstream paths.
- **Judge Node**: Binary pass/fail gate. Semantically clearer when the decision is always a quality verdict. Both nodes are technically specialised Classifiers under the hood; the Judge Node simply defaults to two classes and is labelled to communicate intent.

**Step 8: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. With MockProvider the judge will produce a deterministic response. With a real LLM, the first draft may be accepted immediately or may require one or two revision passes. Check the **Run Log tab** to see how many iterations occurred.

### What you learned

- The Judge Node evaluates content and returns `"pass"` or `"fail"` using an LLM
- Judge is a specialised Classifier with exactly two classes: pass and fail
- The classic use case is a generate → evaluate → revise loop
- Always include a maximum-iterations safeguard to prevent infinite loops
- Use Judge for binary quality gates; use Classifier for multi-class routing decisions

---

[← Previous Part: Flow Control and Human Interaction](gtkn_part3.md)  
[→ Next Part: Batch and Async Nodes](gtkn_part5.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
