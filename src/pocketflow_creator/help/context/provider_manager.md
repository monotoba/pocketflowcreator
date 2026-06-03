# Provider Manager

**Tools → Provider Manager** opens the dialog where you configure which LLM backend
PocketFlow Creator uses when you run or debug a flow.

---

## Choosing a Provider

Select the radio button for the provider you want to use.  Only the settings
panel for the selected provider is shown.  Click **OK** to save; **Cancel**
leaves the previous setting unchanged.

| Provider | Best for |
|---|---|
| **Mock** | Testing the run/debug UI without making real API calls |
| **Ollama** | Local models — no internet required, no API key |
| **OpenAI** | GPT-4o, GPT-4o-mini, and any OpenAI-compatible endpoint |
| **Anthropic (Claude)** | Claude Haiku, Sonnet, Opus |
| **Google Gemini** | Gemini 2.0 Flash, Gemini 1.5 Pro |
| **DeepSeek** | DeepSeek Chat, DeepSeek Reasoner |

---

## Mock

Returns a fixed string for every LLM call — no network traffic.

| Field | Description |
|---|---|
| **Fixed response** | The text returned for every prompt |

---

## Ollama (local)

Connects to a locally-running [Ollama](https://ollama.ai) server.

| Field | Description |
|---|---|
| **Base URL** | Ollama API root (default `http://localhost:11434`) |
| **Default model** | Model tag used when a node doesn't specify one. Click **Refresh** to fetch the list from your Ollama instance. |
| **Timeout** | Maximum seconds to wait per request |

**To use Ollama:**
1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model: `ollama pull qwen2.5-coder:14b`
3. Start the server: `ollama serve`
4. Set the Base URL and model name here; click **Test Connection**, then **OK**

---

## OpenAI

Uses the OpenAI Chat Completions API.  Works with Azure OpenAI and any
OpenAI-compatible third-party endpoint by changing the **Base URL**.

| Field | Description |
|---|---|
| **API Key** | Your OpenAI API key (`sk-…`). Stored locally in app settings. |
| **Base URL** | Completions endpoint root (default `https://api.openai.com/v1`) |
| **Default model** | e.g. `gpt-4o`, `gpt-4o-mini`, `o1-mini` |
| **Timeout** | Maximum seconds to wait per request |

Click **Test Connection** to send a minimal probe request and verify the key is valid.

---

## Anthropic (Claude)

Uses the [Anthropic Messages API](https://docs.anthropic.com/en/api/).

| Field | Description |
|---|---|
| **API Key** | Your Anthropic API key. Stored locally in app settings. |
| **Default model** | e.g. `claude-haiku-4-5`, `claude-sonnet-4-6`, `claude-opus-4-8` |
| **Timeout** | Maximum seconds to wait per request |

Click **Test Connection** to verify the key and model are accessible.

---

## Google Gemini

Uses the [Google Generative Language API](https://ai.google.dev/).

| Field | Description |
|---|---|
| **API Key** | Your Google AI Studio API key (`AIza…`). Stored locally in app settings. |
| **Default model** | e.g. `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash` |
| **Timeout** | Maximum seconds to wait per request |

Click **Test Connection** to verify the key and model are accessible.

---

## DeepSeek

Uses the DeepSeek API, which is OpenAI-compatible.

| Field | Description |
|---|---|
| **API Key** | Your DeepSeek API key. Stored locally in app settings. |
| **Base URL** | API root (default `https://api.deepseek.com/v1`) |
| **Default model** | e.g. `deepseek-chat`, `deepseek-reasoner` |
| **Timeout** | Maximum seconds to wait per request |

Click **Test Connection** to verify the key and model are accessible.

---

## Security note

API keys are stored in the operating system's application settings store
(registry on Windows, `~/.config` on Linux, `~/Library/Preferences` on macOS).
They are never stored in project files and are transmitted only to the
provider's own API endpoint when a flow is run.

[← Help Index](../index.md)
