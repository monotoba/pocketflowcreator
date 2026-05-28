# Part 8 — Web and Search Nodes

This part covers three nodes that bring external data into a flow: fetching web search
results, scraping page content, and calling any REST or GraphQL API.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N26: Web Search Node

### What it does

The **Web Search Node** submits a query to a search engine (DuckDuckGo by default, or
a configured SerpAPI / Brave Search key) and writes a list of result dicts —
`title`, `url`, `snippet` — to the shared store. Downstream nodes can inspect,
filter, or scrape individual results.

### Use cases

- Research pipelines that need fresh web information not in the model's training data
- Fact-checking flows that retrieve primary sources before answering
- Competitive-monitoring workflows that scan for new mentions of a keyword

### What you'll build

A two-node flow — **Start → WebSearcher → Stop** — that searches for
"PocketFlow framework" and stores the top-3 results.

### Step-by-step

**Step 1: Create project `gtkn_part8` and open a blank canvas.**

**Step 2: Drag a Web Search Node** onto the canvas and name it `WebSearcher`.

**Step 3: Set Inspector properties:**

| Property | Value |
|---|---|
| `query_key` | `search_query` |
| `results_key` | `search_results` |
| `num_results` | `3` |
| `engine` | `duckduckgo` |

**Step 4: Wire Start → WebSearcher → Stop.**

**Step 5: Open the Python editor** and paste:

```python
from pocketflow import Node

class WebSearcher(Node):
    def prep(self, shared):
        return shared.get("search_query", "PocketFlow framework")

    def exec(self, prep_res):
        # Simulate search results (production calls a real search API).
        query = prep_res
        return [
            {
                "title": "PocketFlow — Minimalist LLM Framework",
                "url": "https://github.com/The-Pocket/PocketFlow",
                "snippet": "A 100-line LLM framework for agents and workflows.",
            },
            {
                "title": "PocketFlow Tutorial: Build Your First Agent",
                "url": "https://example.com/pocketflow-tutorial",
                "snippet": "Step-by-step guide to building an agent with PocketFlow.",
            },
            {
                "title": "PocketFlow vs LangChain Comparison",
                "url": "https://example.com/comparison",
                "snippet": "Side-by-side comparison of minimalist LLM frameworks.",
            },
        ]

    def post(self, shared, prep_res, exec_res):
        shared["search_results"] = exec_res
        return "default"
```

**Step 6: Validate and run (F5).** Switch to the Shared Store tab:

```
search_results: [
  {"title": "PocketFlow — Minimalist LLM Framework", "url": "...", "snippet": "..."},
  ...
]
```

### What you learned

- Web Search Nodes decouple the query string (shared store) from the node logic
- `results_key` stores a list of dicts with `title`, `url`, and `snippet`
- `num_results` limits how many results are fetched; downstream nodes iterate the list

---

## Tutorial T-N27: Web Scrape Node

### What it does

The **Web Scrape Node** fetches a URL and returns cleaned text content. It strips
navigation, ads, and boilerplate, leaving the main body text for downstream LLM
processing. An optional CSS selector narrows the extraction to a specific page region.

### Use cases

- Extracting article text before summarising with an LLM
- Collecting product descriptions for price-comparison flows
- Archiving page content at a point in time

### What you'll build

Extend the flow from T-N26: add a Web Scrape Node that fetches the first search
result URL and stores its text in `page_text`.

### Step-by-step

**Step 1: Add a Web Scrape Node** named `PageScraper` after `WebSearcher`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `url_key` | `target_url` |
| `output_key` | `page_text` |
| `selector` | _(leave empty — full page)_ |
| `timeout` | `10` |

**Step 3: Re-wire: Start → WebSearcher → PageScraper → Stop.**

**Step 4: Update `WebSearcher.post()`** to also write the first URL:

```python
def post(self, shared, prep_res, exec_res):
    shared["search_results"] = exec_res
    if exec_res:
        shared["target_url"] = exec_res[0]["url"]
    return "default"
```

**Step 5: Paste the Scraper code:**

```python
from pocketflow import Node

class PageScraper(Node):
    def prep(self, shared):
        return shared.get("target_url", "")

    def exec(self, prep_res):
        url = prep_res
        if not url:
            return ""
        # Production: use requests + BeautifulSoup or a headless browser.
        # Simulated response:
        return (
            "PocketFlow is a minimalist LLM framework written in ~100 lines of Python. "
            "It supports nodes, flows, shared state, and async execution. "
            "Design patterns: Map-Reduce, RAG, Agent loops, and multi-agent debate."
        )

    def post(self, shared, prep_res, exec_res):
        shared["page_text"] = exec_res
        return "default"
```

**Step 6: Run and check the Shared Store:**

```
target_url: "https://github.com/The-Pocket/PocketFlow"
page_text: "PocketFlow is a minimalist LLM framework..."
```

### What you learned

- Web Scrape Nodes read their URL from the shared store — easily chained after a Web Search Node
- The `selector` property lets you target a CSS element when only part of the page is relevant
- `page_text` is plain text ready for an LLM node to summarise or analyse

---

## Tutorial T-N28: API Call Node

### What it does

The **API Call Node** makes a configurable HTTP request (GET, POST, PUT, PATCH, DELETE)
to any REST or GraphQL endpoint. Headers, query parameters, and request body are all
sourced from the shared store. The raw response (status code + body) is written back.

### Use cases

- Fetching weather, exchange rates, or any JSON API
- POSTing LLM-generated content to a webhook or CRM
- Calling an internal microservice from within a flow

### What you'll build

A flow that calls the Open-Notify ISS position API (no key required) and extracts the
latitude and longitude of the International Space Station.

### Step-by-step

**Step 1: Add an API Call Node** named `ISSTracker` to a new flow.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `url` | `http://api.open-notify.org/iss-now.json` |
| `method` | `GET` |
| `output_key` | `api_response` |

**Step 3: Wire Start → ISSTracker → Stop.**

**Step 4: Paste the node code:**

```python
import json
from pocketflow import Node

class ISSTracker(Node):
    URL = "http://api.open-notify.org/iss-now.json"

    def prep(self, shared):
        return self.URL

    def exec(self, prep_res):
        # Production: use requests.get(prep_res).json()
        # Simulated response:
        return {
            "status_code": 200,
            "body": {
                "iss_position": {"latitude": "51.5", "longitude": "-0.1"},
                "timestamp": 1716900000,
                "message": "success",
            },
        }

    def post(self, shared, prep_res, exec_res):
        shared["api_response"] = exec_res
        if exec_res.get("status_code") == 200:
            pos = exec_res["body"]["iss_position"]
            shared["iss_lat"] = pos["latitude"]
            shared["iss_lon"] = pos["longitude"]
        return "default"
```

**Step 5: Run and inspect:**

```
api_response: {"status_code": 200, "body": {...}}
iss_lat: "51.5"
iss_lon: "-0.1"
```

### What you learned

- API Call Nodes centralise HTTP configuration in the Inspector (URL, method, headers)
- The raw response (status code + body) is stored for inspection or error handling
- `post()` can unpack specific fields into named shared-store keys for downstream nodes

---

[↑ Series Index](gtkn_index.md)
[← Part 7](gtkn_part7.md)
[→ Part 9: Data and Vector Nodes](gtkn_part9.md)
