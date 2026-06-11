# Tutorial 5: Creating a Custom Node Type

**What you'll learn:** Use the Node Wizard to define a reusable node type with custom properties.

**Prerequisites:** Tutorial 2.

### Steps

1. Node > New Custom Node Type…
2. Fill in the wizard:
   - **Node Type ID:** `sentiment_node`
   - **Display Name:** Sentiment Analyser
   - **Category:** Analysis
   - **Base Class:** `Node`
   - **Actions:** `positive`, `negative`, `neutral`
3. Add a property:
   - Click **Add Property**
   - Name: `threshold`, Type: `number`, Default: `0.5`
4. Click **Create**

The wizard writes two files:
- `node_types/sentiment_node.yaml` — the type definition
- `custom/sentiment_node.py` — a Python skeleton

5. Open `custom/sentiment_node.py` from Project Explorer and implement the logic:

```python
class SentimentNode(Node):
    def prep(self, shared):
        return shared.get("text", "")

    def exec(self, prep_res):
        # Replace with a real sentiment model
        text = prep_res.lower()
        if any(w in text for w in ["great", "love", "excellent"]):
            return "positive"
        elif any(w in text for w in ["bad", "hate", "terrible"]):
            return "negative"
        return "neutral"

    def post(self, shared, prep_res, exec_res):
        shared["sentiment"] = exec_res
        return exec_res  # routes to "positive", "negative", or "neutral" edge
```

6. The **Sentiment Analyser** now appears in the Component Palette under "Analysis"
7. Drag it onto a canvas and wire three outgoing edges labelled `positive`, `negative`, `neutral`

---
