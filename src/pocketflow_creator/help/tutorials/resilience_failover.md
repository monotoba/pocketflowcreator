# Provider Failover: Building Resilient LLM Workflows

## Overview

The **Provider Failover Node** enables resilient LLM calls across multiple providers with sophisticated error handling and automatic recovery. Use it when you need:

- **Multi-provider fallback** — Try local Ollama, fall back to cloud APIs, then mock provider
- **Error-specific retries** — Different retry strategies for timeouts vs rate limits vs token expiration
- **Session recovery** — Automatically re-enable expired providers when their sessions are restored
- **Production resilience** — Handle transient failures without stopping your workflow

## When to Use Provider Failover

| Scenario | Use Provider Failover | Use Retry Node | Use Single Provider |
|----------|----------------------|-----------------|-------------------|
| Need multiple providers as backup | ✅ Yes | No | No |
| Different retry strategies per error | ✅ Yes | No | No |
| Handle API token expiration | ✅ Yes | No | No |
| Simple exponential backoff | No | ✅ Better fit | No |
| Test with mock, deploy with cloud | ✅ Yes | No | No |
| Single reliable provider | No | Maybe | ✅ Yes |

## Example: Multi-Provider LLM Pipeline

**Use case:** You have a question-answering system. During development, use a local Ollama model. In production, use Claude API with OpenAI fallback. Mock provider for tests.

### Step 1: Set Up Providers

In **Tools → Provider Manager**, create three profiles:
1. **"Local Ollama"** — Type: Ollama, Model: `qwen2.5-coder:14b`, URL: `http://localhost:11434`
2. **"Claude API"** — Type: Anthropic, Model: `claude-haiku-4-5` (set `ANTHROPIC_API_KEY` env var)
3. **"OpenAI Fallback"** — Type: OpenAI Compatible, Model: `gpt-4o-mini` (set `OPENAI_API_KEY` env var)

### Step 2: Create the Flow

1. Start node
2. **Provider Failover node** configured as:
   ```json
   [
     {
       "priority": 1,
       "profile_id": "local-ollama-uuid",
       "timeout_retries": 3,
       "network_retries": 3,
       "retry_delay": 2.0
     },
     {
       "priority": 2,
       "profile_id": "claude-api-uuid",
       "timeout_retries": 2,
       "ratelimit_retries": 5,
       "expired_retries": 1,
       "session_offset_seconds": 300
     },
     {
       "priority": 3,
       "profile_id": "openai-fallback-uuid",
       "timeout_retries": 2,
       "ratelimit_retries": 3
     }
   ]
   ```

   **Property values:**
   - `prompt_key`: `"user_question"` (read from shared store)
   - `output_key`: `"answer"` (write response here)
   - `error_key`: `"provider_error"` (write error message on failure)

3. Connect **success** action → next node (process answer)
4. Connect **all_failed** action → error handler (log or user message)

### Step 3: Understand the Behavior

**At runtime:**

1. **Local Ollama (priority 1)** is tried first
   - If it responds: return answer immediately ✓
   - If timeout: sleep 2s, retry up to 3 times
   - If network error (connection refused): sleep 2s, retry up to 3 times
   - After 3 timeouts or 3 network errors exhausted: try next provider

2. **Claude API (priority 2)** is tried next
   - If token expired (HTTP 401 with "expired" in message):
     - Mark this provider unavailable for 300 seconds (5 minutes)
     - Try next provider immediately
   - If rate limited (HTTP 429):
     - Sleep per `Retry-After` header or 2s default
     - Retry up to 5 times
   - If timeout: retry up to 2 times
   - Success: return answer

3. **OpenAI Fallback (priority 3)** is last resort
   - Same retry logic
   - If this fails: action routes to `all_failed`

**Cooldown Example:**

If Claude's token expires at 2:00 PM with `session_offset_seconds: 300`:
- Provider marked unavailable until 2:05 PM
- Future calls to this flow between 2:00–2:05 skip Claude, try OpenAI
- At 2:05 PM+, Claude is re-enabled and tried again

## Error Types and Retry Behavior

| Error Type | Trigger | Default Retries | Delay | Cooldown |
|----------|---------|-----------------|-------|----------|
| **Timeout** | Provider slow to respond | 3 | 2s | None |
| **Network** | Connection refused, DNS fail | 3 | 2s | None |
| **Rate Limit** | HTTP 429 | 2 | Via `Retry-After` header | None |
| **Session Expired** | HTTP 401/403 + "expired" in message | 1 | 2s | Yes (configurable) |
| **Unknown** | Unexpected error | 1 | 2s | None |

## Configuration Reference

Each provider entry in the JSON config:

```json
{
  "priority": 1,              // Lower runs first (required)
  "profile_id": "uuid-...",   // Reference to Provider Manager profile (required)
  "model": "claude-...",      // Override provider's default model (optional)
  "timeout_retries": 3,       // Retries for slow responses (default: 3)
  "network_retries": 3,       // Retries for connection issues (default: 3)
  "ratelimit_retries": 2,     // Retries for HTTP 429 (default: 2)
  "expired_retries": 1,       // Retries for token expiration (default: 1)
  "unknown_retries": 1,       // Retries for other errors (default: 1)
  "retry_delay": 2.0,         // Delay in seconds between timeout/network retries (default: 2.0)
  "session_offset_seconds": 60 // Extra cooldown after session expires (default: 60, max: 900)
}
```

## Shared Store Keys

By default, Provider Failover uses:

- **Input:** `prompt` — reads the prompt from here
- **Output (success):** `failover_response` — stores response here
- **Output (error):** `failover_error` — stores error message here

You can change these in the node's properties:
- `prompt_key`: where to read the prompt
- `output_key`: where to write the response
- `error_key`: where to write error messages

## Session Expiration Handling

When a provider's session/token expires:

1. Error detected: HTTP 401/403 with "expired", "invalid", or "unauthorized"
2. Provider marked unavailable
3. Cooldown set: `reinstatement_time + session_offset_seconds`
4. Workflow continues with next provider (no retry of same provider)
5. After cooldown expires: provider re-enabled automatically

**Why this matters:** API tokens often have refresh windows. By setting `session_offset_seconds`, you give the upstream service time to propagate token refreshes across regions, improving reliability.

## Interactive vs Standalone Execution

**Interactive (GUI):** Provider Failover works immediately—just configure and run.

**Standalone Script Generation:** 
- Export flows with Provider Failover as self-contained `.py` scripts
- Embedded provider implementations (Ollama, OpenAI, Anthropic, Gemini, DeepSeek)
- Cooldown state persisted in script execution's shared store
- All error handling and retry logic fully functional
- Set environment variables for API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Advanced: Combining with Other Nodes

### Provider Failover + Human Review

```
Provider Failover
├─ success → Human Review (quality check the answer)
└─ all_failed → Log (alert on provider failure)
```

When all providers fail, escalate to human review for manual intervention.

### Provider Failover + Cache

```
Cache (check if cached)
├─ hit → return cached result
└─ miss → Provider Failover → Cache (store result)
```

Cache previously computed results to reduce provider load.

### Provider Failover + Router

```
Router (select provider strategy by input)
├─ "local" → Ollama direct
├─ "cloud" → Provider Failover (Claude → OpenAI)
└─ "test" → Mock Provider
```

Route different input types to different provider strategies.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Always falling through to last provider | Local Ollama not running | Start Ollama: `ollama serve` |
| Rate limit retries not working | `ratelimit_retries` too low | Increase to 5+; check `Retry-After` headers |
| Provider never re-enabled after expiration | `session_offset_seconds` too long | Reduce to 60–300 seconds |
| Wrong provider tried first | Priority order wrong | Check JSON config; lower priority = earlier |
| Timeout retries too aggressive | Delaying workflow unnecessarily | Reduce `timeout_retries` or `retry_delay` |

## Best Practices

1. **Test locally first** — Use Ollama locally, add cloud providers as fallback
2. **Set realistic retry counts** — 3 for timeout/network, 2 for rate limit, 1 for session-expired
3. **Use sensible retry delays** — 2–5 seconds for transient issues; don't overwhelm the API
4. **Monitor session expiration** — Log when providers enter cooldown; rotate tokens proactively
5. **Keep priorities clear** — Document why each provider is in the fallback order
6. **Test failover** — Manually stop a provider to verify fallback works
7. **Use env vars for secrets** — Never embed API keys in the flow config

## Summary

The Provider Failover Node transforms your LLM workflows from brittle (single provider, single failure mode) to resilient (multiple providers, error-specific recovery). It's the backbone of production-grade LLM applications.

**Next:** Explore the Retry Node for simpler retry patterns, or combine failover with the Human Review node for escalation workflows.
