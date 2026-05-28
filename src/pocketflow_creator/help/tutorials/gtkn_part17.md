# Part 17 — Networking Nodes

This part covers three nodes for network communication: TCP/UDP sockets, WebSocket
connections, and inbound HTTP webhooks.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N68: Socket Node

### What it does

The **Socket Node** creates, connects, sends data over, or closes a TCP or UDP
socket. The open socket object is stored in the shared store under `socket_key` so
that multiple nodes in the same flow can share the connection. Supported operations
are `connect`, `send`, `receive`, `close`.

### Use cases

- Sending commands to a custom TCP server (industrial equipment, game servers)
- Receiving real-time UDP sensor packets from embedded devices
- Building a simple chat client or monitoring probe as a flow

### What you'll build

A flow that connects to a TCP echo server on `localhost:9000`, sends a message,
receives the echo, and closes the connection.

### Step-by-step

**Step 1: Create project `gtkn_part17`.**

**Step 2: Add three Socket Nodes:** `TCPConnect`, `TCPSendRecv`, `TCPClose`.

**Step 3: Configure `TCPConnect`:**

| Property | Value |
|---|---|
| `operation` | `connect` |
| `host` | `localhost` |
| `port` | `9000` |
| `protocol` | `tcp` |
| `socket_key` | `tcp_socket` |

**Step 4: Wire: Start → TCPConnect → TCPSendRecv → TCPClose → Stop.**

**Step 5: Paste the code:**

```python
# TCPConnect
import socket as _socket
from pocketflow import Node

class TCPConnect(Node):
    HOST = "localhost"
    PORT = 9000

    def prep(self, shared):
        return (self.HOST, self.PORT)

    def exec(self, prep_res):
        host, port = prep_res
        # Production: s = _socket.create_connection((host, port), timeout=5)
        # Simulation: return a mock socket
        class MockSocket:
            def sendall(self, data): pass
            def recv(self, n): return b"Echo: hello from flow\n"
            def close(self): pass
        return MockSocket()

    def post(self, shared, prep_res, exec_res):
        shared["tcp_socket"] = exec_res
        return "default"
```

```python
# TCPSendRecv
from pocketflow import Node

class TCPSendRecv(Node):
    MESSAGE = "hello from flow"

    def prep(self, shared):
        return shared.get("tcp_socket")

    def exec(self, prep_res):
        sock = prep_res
        if sock is None:
            return ""
        sock.sendall((self.MESSAGE + "\n").encode())
        response = sock.recv(1024).decode().strip()
        return response

    def post(self, shared, prep_res, exec_res):
        shared["socket_response"] = exec_res
        return "default"
```

```python
# TCPClose
from pocketflow import Node

class TCPClose(Node):
    def prep(self, shared):
        return shared.get("tcp_socket")

    def exec(self, prep_res):
        if prep_res is not None:
            prep_res.close()
        return "closed"

    def post(self, shared, prep_res, exec_res):
        shared.pop("tcp_socket", None)
        return "default"
```

**Step 6: Run and inspect:**

```
socket_response: "Echo: hello from flow"
```

### What you learned

- Socket Nodes follow the Open/Use/Close pattern — the socket object lives in the shared store
- `protocol: tcp` uses a stream socket; `protocol: udp` uses a datagram socket (no connect step)
- Always wire a Close Node — even on error paths — to avoid leaking file descriptors

---

## Tutorial T-N69: WebSocket Node

### What it does

The **WebSocket Node** opens a persistent `ws://` or `wss://` connection, sends a
JSON or text frame, and waits for the server's reply. The connection is stored in the
shared store and can be reused across multiple send/receive cycles within the same
flow run.

### Use cases

- Subscribing to live market data or sports scores feeds
- Sending real-time updates to a browser UI from a PocketFlow backend
- Communicating with an LLM API that uses a WebSocket streaming interface

### What you'll build

A flow that connects to a public WebSocket echo server, sends a JSON message, and
stores the echoed reply.

### Step-by-step

**Step 1: Add two WebSocket Nodes:** `WSConnect` and `WSSend`.

**Step 2: Configure `WSConnect`:**

| Property | Value |
|---|---|
| `operation` | `connect` |
| `url` | `wss://echo.websocket.org` |
| `connection_key` | `ws_conn` |

**Step 3: Wire: Start → WSConnect → WSSend → Stop.**

**Step 4: Paste the code:**

```python
# WSConnect
from pocketflow import Node

class WSConnect(Node):
    URL = "wss://echo.websocket.org"

    def prep(self, shared):
        return self.URL

    def exec(self, prep_res):
        # Production: import websockets; return websockets.connect(url) (async)
        # or websocket-client for sync usage.
        # Simulation:
        class MockWS:
            def send(self, msg): pass
            def recv(self): return '{"echo": "hello from flow"}'
            def close(self): pass
        return MockWS()

    def post(self, shared, prep_res, exec_res):
        shared["ws_conn"] = exec_res
        return "default"
```

```python
# WSSend
import json
from pocketflow import Node

class WSSend(Node):
    def prep(self, shared):
        return {
            "conn": shared.get("ws_conn"),
            "message": shared.get("ws_message", {"action": "ping", "data": "hello from flow"}),
        }

    def exec(self, prep_res):
        conn = prep_res["conn"]
        msg = prep_res["message"]
        if conn is None:
            return {}
        conn.send(json.dumps(msg))
        raw = conn.recv()
        return json.loads(raw)

    def post(self, shared, prep_res, exec_res):
        shared["ws_response"] = exec_res
        # Close the connection after a single exchange.
        conn = shared.pop("ws_conn", None)
        if conn:
            conn.close()
        return "default"
```

**Step 5: Run and inspect:**

```
ws_response: {"echo": "hello from flow"}
```

### What you learned

- WebSocket Nodes store the connection object in the shared store — keep it alive across multiple sends within one run
- `url: wss://` uses TLS; `ws://` is unencrypted — use the secure form in production
- Close the connection in `post()` or in a dedicated Close node to avoid leaks

---

## Tutorial T-N70: Webhook Trigger Node

### What it does

The **Webhook Trigger Node** starts an HTTP listener on a configured port and pauses
the flow until an inbound `POST` request arrives. When the request comes in the
payload (JSON body or form fields) is stored in the shared store and execution
resumes. It is the entry point for event-driven flows triggered by external systems.

### Use cases

- Starting a flow when a GitHub push event arrives
- Receiving a Stripe payment webhook and processing the order
- Responding to a Slack slash command by triggering a PocketFlow workflow

### What you'll build

A flow that waits for a webhook, extracts the payload, and stores the sender's
repository name from a simulated GitHub push event.

### Step-by-step

**Step 1: Add a Webhook Trigger Node** named `GitHubHook`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `port` | `8080` |
| `path` | `/webhook` |
| `output_key` | `webhook_payload` |
| `timeout` | `60` |
| `secret_key` | `webhook_secret` |

**Step 3: Wire: Start → GitHubHook → RepoHandler → Stop.**

**Step 4: Paste the code:**

```python
# GitHubHook — Webhook Trigger
from pocketflow import Node

class GitHubHook(Node):
    PORT = 8080
    PATH = "/webhook"

    def prep(self, shared):
        return {"port": self.PORT, "path": self.PATH}

    def exec(self, prep_res):
        # Production: start a Flask/FastAPI one-shot server and block until
        # a POST arrives at /webhook, then return request.json
        #
        # Simulation: return a canned GitHub push event payload.
        return {
            "ref": "refs/heads/main",
            "repository": {"full_name": "octocat/hello-world"},
            "pusher": {"name": "octocat"},
            "commits": [
                {"id": "abc1234", "message": "Fix typo in README"}
            ],
        }

    def post(self, shared, prep_res, exec_res):
        shared["webhook_payload"] = exec_res
        return "default"
```

```python
# RepoHandler — processes the webhook payload
from pocketflow import Node

class RepoHandler(Node):
    def prep(self, shared):
        return shared.get("webhook_payload", {})

    def exec(self, prep_res):
        payload = prep_res
        repo = payload.get("repository", {}).get("full_name", "unknown")
        pusher = payload.get("pusher", {}).get("name", "unknown")
        commits = payload.get("commits", [])
        return {
            "repo": repo,
            "pusher": pusher,
            "commit_count": len(commits),
            "last_message": commits[-1]["message"] if commits else "",
        }

    def post(self, shared, prep_res, exec_res):
        shared["push_summary"] = exec_res
        return "default"
```

**Step 5: Run and inspect:**

```
push_summary: {
  "repo": "octocat/hello-world",
  "pusher": "octocat",
  "commit_count": 1,
  "last_message": "Fix typo in README"
}
```

### What you learned

- Webhook Trigger Nodes convert push events into flow runs — the flow waits, receives, then continues
- `secret_key` enables HMAC signature verification for GitHub, Stripe, and similar services
- `timeout` prevents the flow from waiting indefinitely — route the timeout exit to an error Stop

---

[↑ Series Index](gtkn_index.md)
[← Part 16](gtkn_part16.md)
[→ Part 18: AI/LLM Utility and Text Processing Nodes](gtkn_part18.md)
