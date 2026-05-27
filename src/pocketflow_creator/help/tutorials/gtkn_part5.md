# Part 5 — Batch and Async Nodes: Batch, Async, Async Batch, Async Parallel Batch

Parts 1–4 covered nodes that process a single piece of data at a time. Part 5 introduces the four nodes designed for **collections** and **concurrency**. When you need to apply the same operation to every item in a list, or when your exec logic involves waiting for I/O (network calls, file reads, database queries), the batch and async node family gives you the right tool.

These four nodes form a 2×2 matrix:

|            | **Single item** | **List of items** |
|------------|-----------------|-------------------|
| **Sync**   | Basic Node      | Batch Node        |
| **Async**  | Async Node      | Async Batch Node  |

And a fifth option: **Async Parallel Batch** — like Async Batch but all items run concurrently.

Complete Parts 1–4 before starting here.

---

## Tutorial T-N14: The Batch Node

### What it does

The **Batch Node** processes a list of items one at a time using sequential iteration. You write three lifecycle methods: `prep(shared)` returns the list of items; the PocketFlow framework calls `exec(item)` once per item, collecting each return value; and `post(shared, prep_res, exec_res_list)` receives *all* results as a list and stores them. The key difference from the Basic Node is that `exec()` receives a single item from the list on each call, and `post()` receives the complete list of all return values.

### Use cases

- Applying a text transformation to every line in a document
- Calling an API for each item in a product catalogue
- Running the same validation check across all records in a dataset
- Generating a summary for each document in a collection

### What you'll build

A four-node flow — **Start → ItemLoader → BatchProcessor → Aggregator → Stop** — where `ItemLoader` seeds a list of fruit names, `BatchProcessor` is a Batch Node that uppercases each name, and `Aggregator` joins the results into a single string.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part5_batch`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **Basic Node** — rename to `ItemLoader`
3. **Batch Node** — from the **Component Palette**, Batch category; rename to `BatchProcessor`
4. **Basic Node** — rename to `Aggregator`
5. **Stop Node**

Wire: Start →(default)→ ItemLoader →(default)→ BatchProcessor →(default)→ Aggregator →(default)→ Stop.

**Step 3: Write the ItemLoader code**

Select **ItemLoader** and open the **Python editor tab**:

```python
from pocketflow import Node

class ItemLoader(Node):
    """Seeds the shared store with a list of items to batch-process."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        # Place a list of fruit names in the shared store.
        # The BatchProcessor's prep() will read this list.
        shared["items"] = ["apple", "banana", "cherry", "date", "elderberry"]
        return "default"
```

**Step 4: Write the BatchProcessor code**

Select the **BatchProcessor** (Batch Node) and open the **Python editor tab**. Notice that the Batch Node's method signatures differ from the Basic Node:

```python
from pocketflow import BatchNode

class BatchProcessor(BatchNode):
    """Converts each fruit name to uppercase using batch processing."""

    def prep(self, shared):
        # prep() returns the LIST of items to process.
        # The framework will iterate over this list and call exec()
        # once for each item.
        return shared.get("items", [])

    def exec(self, item):
        # exec() receives ONE item from the list at a time.
        # Whatever you return here becomes one element of exec_res_list
        # that post() will receive.
        return item.upper()

    def post(self, shared, prep_res, exec_res_list):
        # post() receives ALL results as a list.
        # prep_res  = the original list returned by prep()
        # exec_res_list = [exec(item) for item in prep_res]
        shared["results"] = exec_res_list
        return "default"
```

> ⚠️ **Note:** The crucial difference from a Basic Node is that `exec()` in a Batch Node receives a **single item**, not the full `prep_res`. If you write `exec(self, prep_res)` expecting the whole list, you will process only the first element. The framework handles the iteration — your `exec()` just handles one item.

**Step 5: Write the Aggregator code**

Select **Aggregator** and open the **Python editor tab**:

```python
from pocketflow import Node

class Aggregator(Node):
    """Joins the batch results into a single comma-separated string."""

    def prep(self, shared):
        return shared.get("results", [])

    def exec(self, prep_res):
        # Join all uppercased fruit names into one string.
        return ", ".join(prep_res)

    def post(self, shared, prep_res, exec_res):
        shared["summary"] = exec_res
        print(f"Batch results: {exec_res}")
        return "default"
```

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Check the **Shared Store tab**:

```
items:   ["apple", "banana", "cherry", "date", "elderberry"]
results: ["APPLE", "BANANA", "CHERRY", "DATE", "ELDERBERRY"]
summary: "APPLE, BANANA, CHERRY, DATE, ELDERBERRY"
```

> 💡 **Tip:** The Batch Node is ideal for the **map** step of a map-reduce pipeline. Use `BatchProcessor` to transform each item (map), then use an `Aggregator` node to combine the results (reduce). This pattern handles any collection-processing task without you writing the iteration loop.

**Step 7: Understand the performance characteristics**

The Batch Node processes items **sequentially** — it waits for each `exec()` call to complete before starting the next. This is fine for CPU-bound operations (string manipulation, math) but slow for I/O-bound operations (API calls, file reads). For I/O-bound batch work, use the Async Batch or Async Parallel Batch nodes covered in T-N16 and T-N17.

### What you learned

- The Batch Node's `prep()` returns a list; `exec()` processes one item at a time; `post()` receives all results as a list
- `exec(self, item)` receives one item per call — not the full list
- Batch Node processes items sequentially — fast for CPU-bound, slow for I/O-bound tasks
- The map-reduce pattern: BatchProcessor for map, Aggregator Basic Node for reduce
- For I/O-bound batch work, prefer Async Batch or Async Parallel Batch

---

## Tutorial T-N15: The Async Node

### What it does

The **Async Node** is identical to the Basic Node in purpose and lifecycle (`prep/exec/post`), but its `exec()` method is an `async def` coroutine. This means the method can `await` asynchronous I/O operations — network requests, database queries, async file I/O — without blocking the event loop. PocketFlow detects that the flow contains async nodes and runs the entire flow inside an `asyncio` event loop automatically.

### Use cases

- Making HTTP requests with `aiohttp` without blocking other operations
- Calling an async database driver (e.g., `asyncpg`, `motor`)
- Performing async file I/O with `aiofiles`
- Integrating with any `async`/`await`-based third-party library

### What you'll build

A three-node flow — **Start → AsyncFetcher → Stop** — where `AsyncFetcher` simulates an async network request using `asyncio.sleep`, then stores a "fetched" result in the shared store.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part5_async`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **Async Node** — from the **Component Palette**, Async category; rename to `AsyncFetcher`
3. **Stop Node**

Wire: Start →(default)→ AsyncFetcher →(default)→ Stop.

**Step 3: Seed the Start Node**

Select **Start Node**, open **Python editor tab**:

```python
from pocketflow import Node

class StartNode(Node):

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        shared["url"] = "https://api.example.com/data"
        return "default"
```

**Step 4: Write the AsyncFetcher code**

Select **AsyncFetcher** and open the **Python editor tab**. The key difference is the `async def exec` signature:

```python
import asyncio
from pocketflow import AsyncNode

class AsyncFetcher(AsyncNode):
    """Simulates an async HTTP fetch using asyncio.sleep."""

    def prep(self, shared):
        # prep() is synchronous — it just reads from the shared store.
        return shared.get("url", "")

    async def exec(self, prep_res):
        # exec() is an async coroutine. The 'await' here suspends
        # this coroutine without blocking the event loop, allowing
        # other coroutines to run concurrently (important in parallel
        # batch scenarios — see T-N17).
        url = prep_res
        print(f"Fetching {url}...")
        await asyncio.sleep(0.1)  # Simulates network latency
        # In a real flow, replace this with:
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(url) as response:
        #         return await response.text()
        return f"Fetched content from {url}"

    def post(self, shared, prep_res, exec_res):
        # post() is synchronous again.
        shared["fetched_content"] = exec_res
        print(f"Result: {exec_res}")
        return "default"
```

> 💡 **Tip:** Notice that `prep()` and `post()` remain synchronous even in an Async Node — only `exec()` is a coroutine. This is intentional: reading from and writing to the shared store (a plain Python dict) is a fast, synchronous operation, so there is no benefit to making it async. Only the slow I/O operation in `exec()` needs to be awaited.

**Step 5: Identify Async Nodes on the canvas**

On the canvas, the **AsyncFetcher** node tile displays a small lightning bolt (⚡) icon in its header, distinguishing it from synchronous nodes at a glance. If you mix sync and async nodes in the same flow, the runner handles the transition automatically.

> ⚠️ **Note:** PocketFlow runs async flows inside `asyncio.run()`. You cannot mix `asyncio.run()` calls directly inside an async node's `exec()` — always use `await` instead. If you call a synchronous library function from inside an async `exec()`, consider wrapping it with `await asyncio.to_thread(sync_function, args)` to avoid blocking the event loop.

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The flow runs inside an asyncio event loop. Check the **Run Log tab** for the print output and the **Shared Store tab** for:

```
url:             "https://api.example.com/data"
fetched_content: "Fetched content from https://api.example.com/data"
```

### What you learned

- The Async Node's `exec()` is an `async def` coroutine that can use `await`
- `prep()` and `post()` remain synchronous even in an Async Node
- PocketFlow automatically runs async flows inside an asyncio event loop
- Async nodes display a lightning bolt icon on the canvas tile
- Use `await asyncio.to_thread()` to run blocking sync code inside an async exec without blocking the event loop

---

## Tutorial T-N16: The Async Batch Node

### What it does

The **Async Batch Node** combines the collection-iteration capability of the Batch Node with the async coroutine capability of the Async Node. It processes a list of items sequentially — one at a time — but each `exec()` call is an `async def` coroutine. This is the right choice when you need to make I/O calls for each item in a list but must process them in order (for example, when order matters or when an API enforces strict sequential access).

### Use cases

- Fetching a web page for each URL in a list, processing each before moving to the next
- Querying a rate-limited API for each item in sequence (one at a time to respect rate limits)
- Processing a list of database records where each update must complete before the next begins
- Async file operations on a list of files

### What you'll build

A four-node flow — **Start → URLLoader → AsyncBatchFetcher → Stop** — where `URLLoader` seeds a list of URLs and `AsyncBatchFetcher` fetches each one sequentially using async I/O.

### Step-by-step

**Step 1: Create a new project**

Go to **File > New Project** and name it `gtkn_part5_async_batch`.

**Step 2: Build the canvas**

Drag and wire:

1. **Start Node**
2. **Basic Node** — rename to `URLLoader`
3. **Async Batch Node** — from the **Component Palette**, Async category; rename to `AsyncBatchFetcher`
4. **Stop Node**

Wire: Start →(default)→ URLLoader →(default)→ AsyncBatchFetcher →(default)→ Stop.

**Step 3: Write the URLLoader code**

```python
from pocketflow import Node

class URLLoader(Node):
    """Seeds a list of URLs into the shared store."""

    def prep(self, shared):
        return None

    def exec(self, prep_res):
        return None

    def post(self, shared, prep_res, exec_res):
        shared["urls"] = [
            "https://api.example.com/item/1",
            "https://api.example.com/item/2",
            "https://api.example.com/item/3",
        ]
        return "default"
```

**Step 4: Write the AsyncBatchFetcher code**

Select the **AsyncBatchFetcher** node and open the **Python editor tab**:

```python
import asyncio
from pocketflow import AsyncBatchNode

class AsyncBatchFetcher(AsyncBatchNode):
    """Fetches each URL sequentially using async I/O."""

    def prep(self, shared):
        # Return the list of URLs to process.
        return shared.get("urls", [])

    async def exec(self, url):
        # Called once per URL, awaiting each before the next begins.
        # This ensures sequential ordering.
        print(f"Fetching {url}...")
        await asyncio.sleep(0.05)  # Simulate network latency per item
        return {"url": url, "status": 200, "content": f"Content of {url}"}

    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list contains one dict per URL, in order.
        shared["fetch_results"] = exec_res_list
        successful = sum(1 for r in exec_res_list if r["status"] == 200)
        print(f"Fetched {successful}/{len(exec_res_list)} URLs successfully.")
        return "default"
```

> 💡 **Tip:** Compare the `exec()` signature here (`async def exec(self, url)`) to the Batch Node from T-N14 (`def exec(self, item)`). The only difference is the `async def`. The Batch Node and Async Batch Node are otherwise identical in structure — learning one teaches you the other.

**Step 5: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. The **Run Log tab** will show each URL being fetched in order, with a 50ms pause between each. The **Shared Store tab** shows `fetch_results` as a list of three dicts.

> ⚠️ **Note:** Async Batch processes items *sequentially* despite being async. Each `await exec(item)` completes before the next item starts. If you need concurrent processing, use the Async Parallel Batch Node (T-N17) instead. The sequential guarantee of Async Batch is a feature, not a limitation — it protects you from API rate limits and ordering requirements.

### What you learned

- Async Batch Node combines Batch's list iteration with Async's coroutine exec
- Items are processed sequentially — each item completes before the next starts
- `exec()` is `async def`; `prep()` and `post()` remain synchronous
- Use Async Batch when ordering matters or when strict sequential API access is required
- For concurrent item processing, use Async Parallel Batch (T-N17)

---

## Tutorial T-N17: The Async Parallel Batch Node

### What it does

The **Async Parallel Batch Node** is the final and most powerful batch variant. Like the Async Batch Node, it processes a list of items with an `async def exec()` coroutine per item — but instead of awaiting each item in turn, it launches *all* `exec()` calls concurrently using `asyncio.gather`. All items are in flight simultaneously, and `post()` receives the complete results list once every item has finished. For I/O-bound workloads where items are independent, this dramatically reduces total wall-clock time.

### Use cases

- Fetching data from multiple independent API endpoints simultaneously
- Uploading multiple files concurrently to cloud storage
- Running the same LLM prompt in parallel for multiple inputs (batch embedding, batch classification)
- Scraping multiple web pages at the same time

### What you'll build

You will extend T-N16 by replacing `AsyncBatchFetcher` with an `AsyncParallelBatchFetcher` that fetches all URLs at the same time rather than one at a time.

### Step-by-step

**Step 1: Open the T-N16 project or create a new one**

Open `gtkn_part5_async_batch` or go to **File > New Project** and name it `gtkn_part5_async_parallel`. If opening the existing project, change the `AsyncBatchFetcher` node type to **Async Parallel Batch Node** (or delete it and drag a new one from the palette).

**Step 2: Build the canvas**

The canvas structure is identical to T-N16:

1. **Start Node**
2. **Basic Node** — rename to `URLLoader` (same as T-N16)
3. **Async Parallel Batch Node** — from the **Component Palette**, Async category; rename to `AsyncParallelFetcher`
4. **Stop Node**

Wire: Start →(default)→ URLLoader →(default)→ AsyncParallelFetcher →(default)→ Stop.

**Step 3: Write the AsyncParallelFetcher code**

```python
import asyncio
from pocketflow import AsyncParallelBatchNode

class AsyncParallelFetcher(AsyncParallelBatchNode):
    """Fetches all URLs concurrently using asyncio.gather."""

    def prep(self, shared):
        # Return the list of URLs — same as AsyncBatchNode.
        return shared.get("urls", [])

    async def exec(self, url):
        # This coroutine runs concurrently with all other exec() calls.
        # All three URLs are in flight at the same time.
        print(f"Starting fetch for {url}")
        await asyncio.sleep(0.05)  # Simulated latency — all items wait this together
        print(f"Completed fetch for {url}")
        return {"url": url, "status": 200, "content": f"Parallel content of {url}"}

    def post(self, shared, prep_res, exec_res_list):
        # Results arrive as a list in the same order as prep_res,
        # even though they ran concurrently.
        shared["parallel_results"] = exec_res_list
        print(f"All {len(exec_res_list)} fetches complete (ran in parallel).")
        return "default"
```

> 💡 **Tip:** Even though execution is concurrent, `post()` always receives results in the **same order as the input list**. `asyncio.gather` preserves ordering. You never need to match results back to inputs using IDs or indices — the position in `exec_res_list` corresponds to the position in the list returned by `prep()`.

**Step 4: Compare timing with T-N16**

Add a timing measurement to see the difference. In a real-world scenario with genuine network latency (say 200ms per request and 10 URLs):

- **Async Batch** (sequential): 10 × 200ms = 2,000ms total
- **Async Parallel Batch** (concurrent): ~200ms total (all 10 run simultaneously)

With simulated 50ms sleep and 3 URLs in this tutorial, the difference is small, but the principle scales dramatically with real I/O.

**Step 5: Decide between sequential and parallel**

Use **Async Batch** (sequential) when:
- Items are not independent (item N depends on the result of item N-1)
- The API you are calling has a rate limit that prohibits concurrent requests
- You need to process exactly one item at a time for correctness reasons
- Items must be processed in strict order

Use **Async Parallel Batch** (concurrent) when:
- Items are independent of each other
- The bottleneck is I/O latency, not CPU time
- You want to minimise total wall-clock time
- The target API supports concurrent connections

> ⚠️ **Note:** Be aware of API rate limits when using Async Parallel Batch. If you have 100 items and each triggers an API call, you will fire 100 requests simultaneously. Most APIs impose rate limits and will start returning HTTP 429 (Too Many Requests) errors. Consider adding a semaphore: `async with asyncio.Semaphore(10): ...` inside `exec()` to cap concurrency at, say, 10 simultaneous requests.

**Step 6: Validate and run**

Press **Ctrl+Shift+V**, then **F5**. Watch the **Run Log tab** — you will see "Starting fetch" messages for all three URLs before you see any "Completed fetch" messages, confirming that all three fetches are running simultaneously.

### What you learned

- Async Parallel Batch runs all `exec()` coroutines concurrently via `asyncio.gather`
- Results in `post()` are always ordered to match the input list, regardless of which item finished first
- Parallel batch dramatically reduces wall-clock time for I/O-bound independent tasks
- Use sequential (Async Batch) for dependent items or rate-limited APIs; use parallel for independent, latency-bound workloads
- Consider `asyncio.Semaphore` inside `exec()` to cap concurrency when API rate limits apply

---

[← Previous Part: LLM Nodes](gtkn_part4.md)  
[→ Next Part: Advanced Nodes](gtkn_part6.md)  
[↑ Series Index](gtkn_index.md)  
[↑ Tutorials Index](index.md)
