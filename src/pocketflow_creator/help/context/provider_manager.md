# Provider Manager

**Tools > Provider Manager** configures the LLM providers used when running flows.

## Ollama Provider

[Ollama](https://ollama.com) runs open-weight LLM models locally.

| Setting | Description | Default |
|---|---|---|
| **Base URL** | The Ollama server address | `http://localhost:11434` |
| **Default model** | Model name to use for LLM nodes | `qwen2.5-coder:14b` |

**To use Ollama:**
1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a model: `ollama pull qwen2.5-coder:14b`
3. Start the server: `ollama serve`
4. Set the Base URL and model name here; click OK

## Mock Provider

The Mock Provider returns a fixed string without making any LLM calls.
Use it for testing flows, testing validation, and running the test suite.

| Setting | Description | Default |
|---|---|---|
| **Fixed response** | The string returned for every LLM call | `mock response` |

The Mock Provider is always available and is the default when no other provider is configured.

## Which Provider Is Used?

The active provider is determined at run time. Currently, PocketFlow Creator uses
whichever provider is configured here. A future release will support per-node provider
selection via the Object Inspector.

## Security Note

Provider credentials (API keys, auth tokens) are never stored in project files.
They are stored in application settings local to your machine.

[← Help Index](../index.md)
