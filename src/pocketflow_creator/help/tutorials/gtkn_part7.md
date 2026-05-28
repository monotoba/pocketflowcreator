# Part 7 — AI / Reasoning Nodes

This part covers five nodes that implement structured reasoning patterns on top of a
standard LLM call. Where a plain **LLM Prompt Node** fires a single prompt and stores
the reply, these nodes add layers of repetition, voting, oversight, and adversarial
debate to make LLM outputs more reliable and trustworthy.

**Prerequisite:** Complete Part 4 (LLM Nodes) before this part.

---

## Tutorial T-N21: Chain of Thought Node

### What it does

The **Chain of Thought Node** prompts an LLM to reason through a problem step-by-step
before producing a final answer. On each call the model appends one "thought" to a
growing list in the shared store; the node loops internally until the model signals it
has reached a conclusion or `steps` is exhausted. The accumulated thoughts are stored
alongside the final answer so you can inspect the model's reasoning in the Run Log.

### Use cases

- Multi-step maths or logic problems where a single-shot answer is unreliable
- Debugging LLM reasoning by examining intermediate steps
- Generating structured plans before executing them

### What you'll build

A four-node flow — **Start → ChainThinker → Stop** — where `ChainThinker` uses 3
reasoning steps to answer "What is 17 × 24?" without a calculator. You will watch the
intermediate thoughts appear in the **Shared Store tab**.

### Step-by-step

**Step 1: Create project `gtkn_part7` and open a blank canvas.**

**Step 2: Drag a Chain of Thought Node** from the palette onto the canvas. Rename it
`ChainThinker` in the Inspector.

**Step 3: Configure the Inspector properties:**

| Property | Value |
|---|---|
| `model` | _(leave empty — uses mock provider)_ |
| `steps` | `3` |
| `output_key` | `cot_result` |

**Step 4: Wire Start → ChainThinker → Stop** (both edges labelled `default`).

**Step 5: Open the Python editor** for `ChainThinker` and paste:

```python
from pocketflow import Node

class ChainThinker(Node):
    def prep(self, shared):
        return shared.get("problem", "What is 17 × 24?")

    def exec(self, prep_res):
        # In a real flow this calls an LLM; here we simulate.
        problem = prep_res
        thoughts = [
            "I need to multiply 17 by 24.",
            "17 × 20 = 340, and 17 × 4 = 68.",
            "340 + 68 = 408. The answer is 408.",
        ]
        return {"thoughts": thoughts, "answer": thoughts[-1].split(". ")[-1]}

    def post(self, shared, prep_res, exec_res):
        shared["thoughts"] = exec_res["thoughts"]
        shared["cot_result"] = exec_res["answer"]
        return "default"
```

**Step 6: Validate (Ctrl+Shift+V) and run (F5).**

**Step 7: Switch to the Shared Store tab.** You will see:

```
thoughts: ["I need to multiply...", "17 × 20 = 340...", "340 + 68 = 408..."]
cot_result: "The answer is 408."
```

### What you learned

- Chain of Thought nodes accumulate intermediate reasoning steps in the shared store
- The `steps` property caps the maximum number of reasoning iterations
- Storing thoughts allows downstream nodes (e.g. a Judge Node) to evaluate the reasoning quality, not just the final answer

---

## Tutorial T-N22: Majority Vote Node

### What it does

The **Majority Vote Node** generates `samples` independent answers to the same prompt
and returns whichever answer appears most often. Self-consistency via majority vote
reliably improves accuracy on tasks where the model sometimes makes mistakes, at the
cost of `samples` LLM calls per invocation.

### Use cases

- Multiple-choice or short-answer questions where the model is sometimes wrong
- Code generation where you want the most popular correct solution
- Any task with a definitive right answer and a small output space

### What you'll build

A flow that asks three independent instances of the model "Is the number 97 prime?"
and returns the majority answer.

### Step-by-step

**Step 1: Add a Majority Vote Node** to the canvas from the previous flow (or a new
one). Name it `PrimeVoter`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `samples` | `3` |
| `output_key` | `voted_result` |

**Step 3: Wire Start → PrimeVoter → Stop.**

**Step 4: Paste the node code:**

```python
from pocketflow import Node
import random

class PrimeVoter(Node):
    def prep(self, shared):
        return shared.get("question", "Is 97 a prime number? Answer yes or no.")

    def exec(self, prep_res):
        # Simulate 3 independent LLM calls.
        # In production each call would go to the configured LLM provider.
        answers = ["yes", "yes", "no"]          # 2-to-1 majority: yes
        return answers

    def post(self, shared, prep_res, exec_res):
        from collections import Counter
        winner = Counter(exec_res).most_common(1)[0][0]
        shared["all_answers"] = exec_res
        shared["voted_result"] = winner
        return "default"
```

**Step 5: Run and check the Shared Store tab:**

```
all_answers: ["yes", "yes", "no"]
voted_result: "yes"
```

### What you learned

- Majority Vote trades LLM cost (N calls) for reliability
- The `samples` property controls how many independent answers are generated
- Even if one or two calls give wrong answers, the majority wins
- The full answer list is stored for auditability

---

## Tutorial T-N23: Supervisor Node

### What it does

The **Supervisor Node** orchestrates a sub-agent loop: it evaluates the output of a
previous step against configurable criteria, decides whether the result is
acceptable (`done`), needs more work (`continue`), or has hit an unrecoverable problem
(`error`), and routes accordingly. Wire `continue` back to the sub-agent and `done`
to the exit to create a supervised retry loop.

### Use cases

- Ensuring generated code compiles before moving on
- Requiring a summary to contain all mandatory keywords
- Capping the number of agent iterations while still allowing multiple attempts

### What you'll build

A loop where a Basic Node generates a random number, and the Supervisor checks
whether it is greater than 50. The flow loops until the condition is met or
`max_iterations` is reached.

### Step-by-step

**Step 1: Create a two-node pair:** a Basic Node named `NumberGen` and a Supervisor
Node named `NumberSupervisor`.

**Step 2: Configure `NumberSupervisor`:**

| Property | Value |
|---|---|
| `max_iterations` | `5` |
| `output_key` | `supervisor_result` |

**Step 3: Declare actions on `NumberSupervisor`:** `continue`, `done`, `error`.

**Step 4: Wire the flow:**

```
Start → NumberGen →(default)→ NumberSupervisor
NumberSupervisor →(continue)→ NumberGen        (loop back)
NumberSupervisor →(done)→ Stop_OK
NumberSupervisor →(error)→ Stop_Error
```

**Step 5: Paste the code for each node:**

```python
# NumberGen
import random
from pocketflow import Node

class NumberGen(Node):
    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return random.randint(1, 100)

    def post(self, shared, prep_res, exec_res):
        shared["number"] = exec_res
        return "default"
```

```python
# NumberSupervisor
from pocketflow import Node

class NumberSupervisor(Node):
    MAX_ITER = 5

    def prep(self, shared):
        return {
            "number": shared.get("number", 0),
            "iteration": shared.get("iter", 0),
        }

    def exec(self, prep_res):
        return prep_res

    def post(self, shared, prep_res, exec_res):
        n = exec_res["number"]
        iteration = exec_res["iteration"] + 1
        shared["iter"] = iteration
        if n > 50:
            shared["supervisor_result"] = f"Accepted {n} after {iteration} tries"
            return "done"
        if iteration >= self.MAX_ITER:
            shared["supervisor_result"] = f"Gave up after {iteration} tries, last={n}"
            return "error"
        return "continue"
```

**Step 6: Run several times** and observe that the loop sometimes exits after one
iteration (lucky roll > 50) and sometimes runs all 5.

### What you learned

- The Supervisor Node pattern wraps any sub-agent in a controlled retry loop
- Three actions — `continue`, `done`, `error` — cover the three outcomes a supervisor needs
- `max_iterations` prevents infinite loops
- The iteration counter lives in the shared store and persists across loop iterations

---

## Tutorial T-N24: Debate Advocate Node

### What it does

The **Debate Advocate Node** generates the strongest possible one-sided argument for a
given `position` (`pro` or `con`). Use two instances — one per side — to build an
adversarial evaluation pipeline where pros and cons are surfaced before a decision.

### Use cases

- Evaluating business decisions by generating best-case and worst-case arguments
- Improving persuasive writing by seeing both sides before drafting
- Red-teaming AI outputs by automatically generating counter-arguments

### What you'll build

A flow with two Debate Advocate Nodes (one `pro`, one `con`) that run in sequence, both
writing their arguments to different shared store keys.

### Step-by-step

**Step 1: Add two Debate Advocate Nodes:** `ProAdvocate` and `ConAdvocate`.

**Step 2: Set `position = pro` on `ProAdvocate` and `position = con` on `ConAdvocate`.**

Set `output_key = pro_argument` and `output_key = con_argument` respectively.

**Step 3: Wire: Start → ProAdvocate → ConAdvocate → Stop.**

**Step 4: Paste the code (same pattern for both, differing in `position`):**

```python
# ProAdvocate
from pocketflow import Node

class ProAdvocate(Node):
    POSITION = "pro"

    def prep(self, shared):
        return shared.get("topic", "Remote work increases productivity")

    def exec(self, prep_res):
        topic = prep_res
        if self.POSITION == "pro":
            return (f"FOR '{topic}': Employees report higher focus without "
                    "office distractions; commute time is reclaimed; "
                    "global talent pools open up.")
        return (f"AGAINST '{topic}': Collaboration suffers; junior staff lose "
                "mentorship; home environments are not always suitable for work.")

    def post(self, shared, prep_res, exec_res):
        shared["pro_argument"] = exec_res
        return "default"
```

```python
# ConAdvocate — identical except POSITION = "con" and output key
from pocketflow import Node

class ConAdvocate(Node):
    POSITION = "con"

    def prep(self, shared):
        return shared.get("topic", "Remote work increases productivity")

    def exec(self, prep_res):
        return (f"AGAINST '{prep_res}': Collaboration suffers; junior staff lose "
                "mentorship; home environments are not always suitable for work.")

    def post(self, shared, prep_res, exec_res):
        shared["con_argument"] = exec_res
        return "default"
```

**Step 5: Run and inspect both keys in the Shared Store tab.**

### What you learned

- Advocate Nodes are paired: one `pro`, one `con`
- Both write to different shared store keys so a downstream Judge Node can compare them
- The topic is passed via the shared store, making it easy to parameterise

---

## Tutorial T-N25: Debate Judge Node

### What it does

The **Debate Judge Node** reads arguments from both sides of a debate (stored by two
Debate Advocate Nodes) and decides the winner, returning `pro_wins`, `con_wins`, or
`tie`. It is the final step in a debate pipeline and can trigger different downstream
actions based on the verdict.

### Use cases

- Final arbitration in a multi-agent debate pipeline
- Choosing between two LLM-generated plans
- Any binary-or-tie decision that benefits from explicit argument comparison

### What you'll build

Extend the flow from T-N24 by appending a Debate Judge Node that reads `pro_argument`
and `con_argument` and routes to one of three Stop Nodes based on the verdict.

### Step-by-step

**Step 1: Add a Debate Judge Node** named `Arbiter` after `ConAdvocate`.

**Step 2: Declare actions:** `pro_wins`, `con_wins`, `tie`.

**Step 3: Add three Stop Nodes:** `Stop_Pro`, `Stop_Con`, `Stop_Tie`.

**Step 4: Wire:**

```
ConAdvocate →(default)→ Arbiter
Arbiter →(pro_wins)→ Stop_Pro
Arbiter →(con_wins)→ Stop_Con
Arbiter →(tie)→ Stop_Tie
```

**Step 5: Paste the Judge code:**

```python
from pocketflow import Node

class Arbiter(Node):
    def prep(self, shared):
        return {
            "pro": shared.get("pro_argument", ""),
            "con": shared.get("con_argument", ""),
        }

    def exec(self, prep_res):
        # In production: LLM compares the two arguments and scores them.
        # Here we simulate with a simple length heuristic.
        if len(prep_res["pro"]) > len(prep_res["con"]):
            return "pro_wins"
        if len(prep_res["con"]) > len(prep_res["pro"]):
            return "con_wins"
        return "tie"

    def post(self, shared, prep_res, exec_res):
        shared["debate_verdict"] = exec_res
        return exec_res         # routes to pro_wins, con_wins, or tie
```

**Step 6: Validate (all three actions must be wired) and run.**

### What you learned

- The Debate Judge Node is the router that closes a three-action debate pipeline
- `post()` returns the verdict string directly, which the runner uses to select the outgoing edge
- The complete pipeline is: ProAdvocate → ConAdvocate → Arbiter → (three exits)

---

[↑ Series Index](gtkn_index.md)
[← Part 6](gtkn_part6.md)
[→ Part 8: Web and Search Nodes](gtkn_part8.md)
