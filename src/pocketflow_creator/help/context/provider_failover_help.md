# Provider Failover Node Help

## What is Provider Failover?

The Provider Failover Node enables resilient LLM calls across multiple providers with automatic fallback and error-specific retry logic.

**Key features:**
- Try multiple providers in priority order
- Different retry strategies for timeouts, network errors, rate limits, and session expiration
- Automatic cooldown for expired sessions with configurable offset
- Works identically in interactive and standalone script modes

## Configuration

### providers_config (JSON text)

Array of providers with priorities and retry policies:

```json
[
  {
    "priority": 1,
    "profile_id": "uuid-of-provider",
    "model": "",
    "timeout_retries": 3,
    "network_retries": 3,
    "ratelimit_retries": 2,
    "expired_retries": 1,
    "unknown_retries": 1,
    "retry_delay": 2.0,
    "session_offset_seconds": 60
  }
]
```

**Fields:**
- `priority` (required): Lower number = tried first (e.g., 1 before 2 before 3)
- `profile_id` (required): UUID reference to a Provider Manager profile
- `model`: Override the provider's default model (leave empty to use default)
- `timeout_retries`: Retries when provider is slow (0–10, default 3)
- `network_retries`: Retries for connection issues (0–10, default 3)
- `ratelimit_retries`: Retries for HTTP 429 / rate limits (0–10, default 2)
- `expired_retries`: Retries for token expiration (0–5, default 1)
- `unknown_retries`: Retries for unexpected errors (0–5, default 1)
- `retry_delay`: Sleep seconds between timeout/network retries (default 2.0)
- `session_offset_seconds`: Extra cooldown after expiration, 60–900 (default 60)

### Shared Store Keys

- `prompt_key` (default: `"prompt"`) — where to read the prompt
- `output_key` (default: `"failover_response"`) — where to write the response (on success)
- `error_key` (default: `"failover_error"`) — where to write the error message (on failure)

## Actions

- **success**: Provider returned a response. Response written to `output_key`.
- **all_failed**: All providers and retries exhausted. Error message written to `error_key`.

## Error Types

| Error | Detected As | Retry Count | Delay | Effect |
|-------|------------|------------|-------|--------|
| Timeout | Provider slow | `timeout_retries` | `retry_delay`s | Retry same provider |
| Network | Connection refused, DNS fail | `network_retries` | `retry_delay`s | Retry same provider |
| Rate Limit | HTTP 429 | `ratelimit_retries` | `Retry-After` header or `retry_delay`s | Retry same provider |
| Session Expired | HTTP 401/403 + expired/invalid/unauthorized | `expired_retries` | Mark unavailable | Skip to next provider |
| Unknown | Unexpected error | `unknown_retries` | `retry_delay`s | Retry same provider |

## Session Cooldown

When a provider reports session/token expiration:

1. Error detected (HTTP 401/403 with "expired"/"invalid"/"unauthorized")
2. Provider marked unavailable until: `now + session_offset_seconds`
3. Workflow proceeds to next provider (no retry of same provider)
4. After cooldown expires, provider automatically re-enabled

**Example:** If session expires at 2:00 PM with offset 300s, provider is re-enabled at 2:05 PM.

## Common Patterns

**Multi-cloud with local fallback:**
```
Priority 1: Local Ollama (always available, always try first)
Priority 2: Claude API (cloud, better results)
Priority 3: OpenAI (cloud, fallback)
```

**Development vs production:**
```
Development: Mock provider (no API calls)
Production: Claude API → OpenAI fallback
```

**High-availability with graceful degradation:**
```
Priority 1: Primary API (claude-api)
Priority 2: Secondary API (openai)
Priority 3: Tertiary local (ollama)
Priority 4: Fallback mock
```

## Best Practices

1. **Set realistic priorities** — Fast/cheap first, then reliable, then fallback
2. **Tune retry counts** — 3 for transient errors, 1 for terminal errors
3. **Use reasonable delays** — 2–5s between retries; don't hammer providers
4. **Monitor cooldowns** — Log when providers go offline
5. **Test failover** — Manually stop a provider to verify fallback works
6. **Document rationale** — Why is each provider in this position?

## Standalone Script Generation

Provider Failover fully supports standalone Python script export:

```bash
File > Export Standalone Archive
```

The generated script includes:
- All provider implementations (Ollama, OpenAI, Anthropic, Gemini, DeepSeek)
- Complete failover logic with retry and cooldown tracking
- Environment variable support for API keys
- Identical behavior to interactive mode

Set environment variables before running:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
python generated_flow.py
```

## See Also

- **Retry Node**: Simple exponential backoff for single provider
- **Human Review Node**: Escalate failures to human judgment
- **Cache Node**: Avoid repeated provider calls
- **Provider Manager**: Configure and test provider profiles

## Learn More

See the tutorial: **Resilience: Provider Failover** for detailed examples and patterns.
