# Part 19 — Resilience, Messaging, and Security Nodes

This final part covers six nodes that make flows production-ready: exponential-backoff
retries, per-minute rate limiting, email sending and reading, multi-platform
notifications, and secret management.

**Prerequisite:** Complete Part 1 (Start / Stop / Basic) before this part.

---

## Tutorial T-N78: Retry Node

### What it does

The **Retry Node** wraps a fallible operation in an exponential-backoff loop. On each
attempt it calls the configured sub-node logic; if the attempt raises an exception or
returns a failure signal, it waits `base_delay * 2^attempt` seconds (plus optional
random jitter) before retrying. After `max_attempts` failures it routes to `failed`.

### Use cases

- Retrying a flaky API call without coupling retry logic to the calling node
- Handling transient network errors in a web scraping or data-ingestion flow
- Implementing a self-healing LLM call that retries on rate-limit responses

### What you'll build

A flow where a simulated unstable API fails twice before succeeding, and the Retry
Node handles all three attempts automatically.

### Step-by-step

**Step 1: Create project `gtkn_part19`.**

**Step 2: Add a Retry Node** named `APIRetrier`.

**Step 3: Declare actions:** `success`, `failed`.

**Step 4: Set Inspector properties:**

| Property | Value |
|---|---|
| `max_attempts` | `3` |
| `base_delay` | `0.1` |
| `jitter` | `true` |
| `output_key` | `api_data` |

**Step 5: Wire:**

```
Start → APIRetrier →(success)→ Stop_OK
APIRetrier →(failed)→ Stop_Error
```

**Step 6: Paste the code:**

```python
import time
import random
from pocketflow import Node

class APIRetrier(Node):
    MAX_ATTEMPTS = 3
    BASE_DELAY = 0.1
    JITTER = True

    def prep(self, shared):
        shared.setdefault("attempt_count", 0)
        return shared["attempt_count"]

    def exec(self, prep_res):
        attempt = prep_res
        # Simulate a flaky API: fails on the first two attempts.
        if attempt < 2:
            raise ConnectionError(f"Simulated network error on attempt {attempt + 1}")
        return {"data": "API response after retry", "attempt": attempt + 1}

    def post(self, shared, prep_res, exec_res):
        shared["attempt_count"] = prep_res + 1
        shared["api_data"] = exec_res
        return "success"

    def exec_fallback(self, prep_res, exc):
        attempt = prep_res
        next_attempt = attempt + 1
        if next_attempt < self.MAX_ATTEMPTS:
            delay = self.BASE_DELAY * (2 ** attempt)
            if self.JITTER:
                delay += random.uniform(0, delay * 0.1)
            time.sleep(delay)
            return None   # signal: retry
        return None   # signal: exhausted

    # Note: in a real PocketFlow Retry Node the framework calls exec_fallback
    # automatically on exception. This code illustrates the pattern.
```

**Step 7: Run.** On the first two iterations `attempt_count` increments; on the
third the API "succeeds" and routes to `Stop_OK`.

### What you learned

- Retry Nodes isolate resilience logic — the wrapped node does not need to know about retries
- Exponential backoff (`base_delay * 2^attempt`) prevents thundering-herd behaviour
- Always wire a `failed` exit so the flow can report exhausted retries gracefully

---

## Tutorial T-N79: Rate Limiter Node

### What it does

The **Rate Limiter Node** enforces a maximum number of calls per minute to a named
endpoint or service. If the current call rate would exceed the limit, the node
sleeps until the window resets. A `label` property identifies the endpoint, allowing
multiple rate limiters with independent budgets in the same flow.

### Use cases

- Honouring a search API's free tier (e.g. 60 requests/minute)
- Preventing an LLM provider from returning 429 errors during batch processing
- Throttling outbound emails to comply with SMTP relay limits

### What you'll build

A flow that processes 5 items but allows only 2 API calls per minute.

### Step-by-step

**Step 1: Add a Rate Limiter Node** named `SearchLimiter` before an API Call Node.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `label` | `search_api` |
| `calls_per_minute` | `2` |
| `output_key` | `rate_limit_status` |

**Step 3: Wire Start → SearchLimiter → APINode → Stop.**

**Step 4: Paste the code:**

```python
import time
from pocketflow import Node

_WINDOWS: dict = {}

class SearchLimiter(Node):
    LABEL = "search_api"
    CALLS_PER_MINUTE = 2

    def prep(self, shared):
        return self.LABEL

    def exec(self, prep_res):
        label = prep_res
        now = time.monotonic()
        window = _WINDOWS.setdefault(label, {"calls": 0, "window_start": now})

        # Reset window every 60 seconds.
        if now - window["window_start"] >= 60:
            window["calls"] = 0
            window["window_start"] = now

        if window["calls"] >= self.CALLS_PER_MINUTE:
            sleep_time = 60 - (now - window["window_start"])
            # In production: time.sleep(sleep_time)
            # In simulation: just note the sleep
            return {"slept": True, "sleep_seconds": round(sleep_time, 1)}

        window["calls"] += 1
        return {"slept": False, "calls_this_window": window["calls"]}

    def post(self, shared, prep_res, exec_res):
        shared["rate_limit_status"] = exec_res
        return "default"
```

**Step 5: Run 3 times quickly.** The first two calls proceed; the third reports
`slept: true` with a sleep duration.

### What you learned

- Rate Limiter Nodes are inserted before any node that calls an external service
- `label` allows independent rate-limit buckets for different services in the same flow
- The window state lives in a module-level dict, persisting across calls in the same process

---

## Tutorial T-N80: Email Send Node

### What it does

The **Email Send Node** sends an email via SMTP, SendGrid, or Mailgun. Recipient
address, subject, body, and optional attachments are sourced from shared-store keys.
On success it writes the message ID back; on failure it stores the error.

### Use cases

- Sending automated reports or alerts when a flow completes
- Notifying a user that their request has been processed
- Forwarding LLM-generated content to a stakeholder inbox

### What you'll build

A flow that composes and sends a short summary email.

### Step-by-step

**Step 1: Add an Email Send Node** named `ReportSender`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `to_key` | `recipient_email` |
| `subject_key` | `email_subject` |
| `body_key` | `email_body` |
| `output_key` | `sent_message_id` |
| `provider` | `smtp` |

**Step 3: Wire Start → ReportSender → Stop.**

**Step 4: Paste the code:**

```python
import uuid
from pocketflow import Node

class ReportSender(Node):
    def prep(self, shared):
        shared.setdefault("recipient_email", "alice@example.com")
        shared.setdefault("email_subject", "Daily Flow Report")
        shared.setdefault(
            "email_body",
            "Hi Alice,\n\nYour daily PocketFlow run completed successfully.\n\nRegards,\nPocketFlow Creator",
        )
        return {
            "to": shared["recipient_email"],
            "subject": shared["email_subject"],
            "body": shared["email_body"],
        }

    def exec(self, prep_res):
        # Production: smtplib.SMTP(...).sendmail(...) or requests to SendGrid API.
        # Simulation: return a fake message ID.
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        return {"message_id": msg_id, "status": "sent"}

    def post(self, shared, prep_res, exec_res):
        shared["sent_message_id"] = exec_res["message_id"]
        return "default"
```

**Step 5: Run:**

```
sent_message_id: "msg_3a7f2c1e"
```

### What you learned

- Email Send Nodes decouple message construction from delivery — build the subject/body in a Template Render Node first
- `provider: smtp` uses local SMTP settings; `provider: sendgrid` and `provider: mailgun` use their respective APIs
- Store the message ID for follow-up tracking or to attach to an audit log

---

## Tutorial T-N81: Email Read Node

### What it does

The **Email Read Node** connects to an IMAP mailbox (Gmail, Outlook, or any IMAP
server) and fetches unseen messages matching optional filter criteria (subject
contains, sender, since date). Messages are returned as a list of dicts with `from`,
`subject`, `date`, and `body`.

### Use cases

- Triggering a flow when a specific email arrives (e.g. a customer enquiry)
- Processing form-submission emails and extracting structured data with an LLM
- Archiving or forwarding emails based on content classification

### What you'll build

A flow that checks for new support requests and stores the first unread message.

### Step-by-step

**Step 1: Add an Email Read Node** named `InboxPoller`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `host_key` | `imap_host` |
| `username_key` | `imap_user` |
| `password_key` | `imap_password` |
| `folder` | `INBOX` |
| `unseen_only` | `true` |
| `max_messages` | `5` |
| `output_key` | `new_emails` |

**Step 3: Wire Start → InboxPoller → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class InboxPoller(Node):
    def prep(self, shared):
        return {
            "host": shared.get("imap_host", "imap.example.com"),
            "user": shared.get("imap_user", "support@example.com"),
        }

    def exec(self, prep_res):
        # Production: imaplib.IMAP4_SSL(host); login, search UNSEEN, fetch.
        # Simulation: return two mock emails.
        return [
            {
                "from": "customer@example.com",
                "subject": "Login issue",
                "date": "2026-05-28T09:15:00",
                "body": "I cannot log in to my account since yesterday.",
            },
            {
                "from": "another@example.com",
                "subject": "Billing question",
                "date": "2026-05-28T10:00:00",
                "body": "Could you clarify the charge on my last invoice?",
            },
        ]

    def post(self, shared, prep_res, exec_res):
        shared["new_emails"] = exec_res
        return "default"
```

**Step 5: Run and inspect `new_emails`.** Chain a Classifier Node next to triage
by subject.

### What you learned

- Email Read Nodes return a list — use a Map Node to process each message independently
- `unseen_only: true` is essential for polling flows so already-processed messages are not reread
- Store credentials in a Secret Node (T-N83) rather than hard-coding them in the Inspector

---

## Tutorial T-N82: Notification Node

### What it does

The **Notification Node** sends a message to Slack, Discord, Microsoft Teams, or
Telegram via their respective incoming webhook or bot APIs. The message text, platform,
and webhook URL are configured in the Inspector. Use it to alert a team channel when
a flow completes, errors, or produces a notable result.

### Use cases

- Posting a daily summary to a Slack channel from a scheduled flow
- Alerting an on-call engineer when a monitored flow fails
- Sending a Telegram message when a sensor reading exceeds a threshold

### What you'll build

A flow that sends a Slack notification summarising a completed run.

### Step-by-step

**Step 1: Add a Notification Node** named `SlackAlerter`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `platform` | `slack` |
| `webhook_url_key` | `slack_webhook_url` |
| `message_key` | `notification_message` |
| `output_key` | `notification_status` |

**Step 3: Wire Start → SlackAlerter → Stop.**

**Step 4: Paste the code:**

```python
from pocketflow import Node

class SlackAlerter(Node):
    def prep(self, shared):
        shared.setdefault(
            "slack_webhook_url",
            "https://hooks.slack.com/services/T00/B00/XXXX",
        )
        shared.setdefault(
            "notification_message",
            "✅ Daily flow completed successfully. 142 records processed.",
        )
        return {
            "url": shared["slack_webhook_url"],
            "text": shared["notification_message"],
        }

    def exec(self, prep_res):
        # Production: requests.post(url, json={"text": text})
        # Simulation:
        return {"ok": True, "platform": "slack"}

    def post(self, shared, prep_res, exec_res):
        shared["notification_status"] = exec_res
        return "default"
```

**Step 5: Run:**

```
notification_status: {"ok": true, "platform": "slack"}
```

### What you learned

- Notification Nodes abstract the platform differences — switch from Slack to Discord by changing `platform` and `webhook_url`
- The `message_key` pattern lets an LLM node compose the notification text before this node sends it
- Wire Notification Nodes onto both `done` and `error` paths to ensure the team is always informed

---

## Tutorial T-N83: Secret Node

### What it does

The **Secret Node** retrieves a secret value from a configured source — an environment
variable, a `.env` file, AWS Secrets Manager, or HashiCorp Vault — and writes it to a
shared-store key. Use it to inject credentials at runtime without hard-coding sensitive
values in flow code or the Inspector.

### Use cases

- Loading API keys (OpenAI, SendGrid, Stripe) at flow start
- Injecting database passwords from Vault into a DB Schema or SQL Execute Node
- Rotating secrets without re-editing any flow configuration

### What you'll build

A flow that loads an API key from an environment variable and uses it in a downstream
API Call Node.

### Step-by-step

**Step 1: Add a Secret Node** named `APIKeyLoader`.

**Step 2: Set Inspector properties:**

| Property | Value |
|---|---|
| `source` | `env` |
| `secret_name` | `OPENAI_API_KEY` |
| `output_key` | `openai_api_key` |

**Step 3: Wire Start → APIKeyLoader → APICallNode → Stop.**

**Step 4: Paste the code:**

```python
import os
from pocketflow import Node

class APIKeyLoader(Node):
    SECRET_NAME = "OPENAI_API_KEY"

    def prep(self, shared):
        return self.SECRET_NAME

    def exec(self, prep_res):
        value = os.environ.get(prep_res)
        if value:
            return {"found": True, "value": value}
        # Simulation: return a placeholder when the env var is not set.
        return {"found": False, "value": "sk-PLACEHOLDER-NOT-A-REAL-KEY"}

    def post(self, shared, prep_res, exec_res):
        shared["openai_api_key"] = exec_res["value"]
        shared["secret_found"] = exec_res["found"]
        return "default"
```

**Step 5: Set the environment variable and run:**

```bash
export OPENAI_API_KEY="sk-my-real-key"
```

When the variable is set, `openai_api_key` contains the real key; when it is absent,
it falls back to the placeholder and `secret_found` is `false`.

**Step 6: Add a Condition Node** after `APIKeyLoader` that routes to `Stop_Error`
when `secret_found == false`.

### What you learned

- Secret Nodes ensure credentials are never stored in YAML or Python files
- `source: dotenv` reads from a local `.env` file; `source: aws` and `source: vault` call their respective SDKs
- The secret value lives in the shared store only for the duration of the run — it is not persisted

---

## Built-in Nodes Complete — Continue to Addon Nodes!

You have worked through all 19 parts covering PocketFlow Creator's 83 built-in node types. Here is a summary of the full pipeline families you can now build with built-in nodes alone:

| Pipeline | Key Nodes |
|---|---|
| RAG | Text Chunk → Embed → Vector Index → Vector Retrieve → LLM Prompt |
| NL-to-SQL | DB Schema → NL to SQL → SQL Execute |
| Voice assistant | Speech to Text → LLM Prompt → Text to Speech |
| Code assistant | Code Gen → Code Exec → Test Gen |
| Email triage | Email Read → Classifier → Notification |
| Debate | Debate Advocate (×2) → Debate Judge |
| Web research | Web Search → Web Scrape → LLM Prompt |
| IoT sensing | TTY Serial → Transform → Condition → Notification |
| Scheduled job | Calendar Read → LLM Prompt → Calendar Write |
| Resilient API | Secret → Rate Limiter → Retry → API Call |

Ready to go further? Parts 20–25 cover the 34 domain-specific **addon nodes** for geospatial data, hydrology, atmospheric modelling, aerospace CFD and propulsion, wind energy, and scientific computing.

---

[← Part 18](gtkn_part18.md)
[→ Part 20 — Geospatial Addon Nodes](gtkn_part20.md)
[↑ Series Index](gtkn_index.md)
