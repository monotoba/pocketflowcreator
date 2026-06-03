# Provider Manager

**Tools → Provider Manager** opens the dialog where you create and manage named provider profiles.
Each profile stores the configuration for an LLM service (Ollama, OpenAI, Claude, etc.).

---

## Overview

The Provider Manager dialog is split into two panels:

**Left panel (Profiles list)**:
- Shows all your saved provider profiles
- ★ indicates the default profile (used by flows that don't specify a provider)
- Buttons: **+ Add** (new), **Delete**, **Set Default ★**

**Right panel (Profile editor)**:
- Name, API type, base URL, default model, timeout
- API Key field with options to enter directly or read from environment
- **Test Connection** button to verify the settings work

---

## Creating a New Profile

1. Click **+ Add**
2. Enter a profile name (e.g., "Local Ollama", "OpenAI Production")
3. Select an **API type** from the dropdown
4. The **Base URL** and **Default model** fields auto-populate with sensible defaults
5. Customize if needed (e.g., change port for Ollama running on a non-standard port)
6. If the provider requires an API key, enter it or select "Read from environment variable"
7. Click **Test Connection** to verify everything works
8. Click **OK** to save

---

## Provider Types

### Ollama (local)

Free, open-source LLM inference engine for local models.

| Field | Default | Notes |
|---|---|---|
| **Base URL** | `http://localhost:11434` | Change if Ollama runs on a different port/host |
| **Default model** | `qwen2.5-coder:14b` | Pull models with `ollama pull <model-name>` |
| **Timeout** | 120 s | Increase for large models or slow machines |

**Setup**: Install Ollama from [ollama.ai](https://ollama.ai), run `ollama serve`, and pull a model.

### LM Studio (local)

Desktop application for running local LLMs with a GUI.

| Field | Default | Notes |
|---|---|---|
| **Base URL** | `http://localhost:1234/v1` | Change if LM Studio runs on a different port |
| **Default model** | `meta-llama-3.1-8b` | Set to the model you've loaded in LM Studio |
| **Timeout** | 120 s | Increase for large models |

**Setup**: Install LM Studio from [lmstudio.ai](https://lmstudio.ai) and load a model.

### OpenAI-compatible

OpenAI's API format, used by OpenAI, Azure OpenAI, Deepseek, Groq, and others.

| Field | Notes |
|---|---|
| **Base URL** | e.g. `https://api.openai.com/v1` (OpenAI), `https://api.deepseek.com/v1` (Deepseek) |
| **Default model** | e.g. `gpt-4o`, `gpt-4o-mini`, `deepseek-chat` |
| **API Key** | Required; stored securely (see Security note below) |
| **Timeout** | 120 s (usually sufficient for cloud APIs) |

### Anthropic (Claude)

Claude models from Anthropic.

| Field | Default | Notes |
|---|---|---|
| **Default model** | `claude-haiku-4-5` | Other options: `claude-sonnet-4-6`, `claude-opus-4-8` |
| **API Key** | (required) | Get from [console.anthropic.com](https://console.anthropic.com) |
| **Timeout** | 120 s | Usually sufficient |

### Google Gemini

Google's generative AI models.

| Field | Default | Notes |
|---|---|---|
| **Default model** | `gemini-2.0-flash` | Also: `gemini-1.5-pro`, `gemini-1.5-flash` |
| **API Key** | (required) | Get from [aistudio.google.com](https://aistudio.google.com) |
| **Timeout** | 120 s | Usually sufficient |

---

## Testing Connections

The **Test Connection** button sends a simple test prompt to verify your provider is accessible.

After clicking **Test Connection**:
- The button shows "Testing…" while the test runs
- After 5-10 seconds, you'll see one of:
  - **✓ Connection successful** — provider is working
  - **✗ [error message]** — there's a problem (see Troubleshooting below)
  - **✗ Test timed out (30 s)** — provider didn't respond in time

---

## API Key Security

By default, API keys are **not** stored in project files. They're stored securely in your
operating system's application settings:
- **Windows**: Registry
- **macOS**: Keychain/Preferences
- **Linux**: `~/.config/`

### Storing API keys in the environment

For production use, set environment variables before starting PocketFlow Creator:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
./scripts/run_app.sh
```

Then in the Provider Manager, select "Read from environment variable" and enter the variable name
(e.g., `OPENAI_API_KEY`).

### Including API keys in project files

⚠️ **Warning**: Only do this for non-production projects or when keys are not sensitive.

Check **Include API keys in project file** to store keys in plain text in your project YAML.
This allows the project to be fully portable but exposes keys in the file.

---

## Using Providers in Workflows

### Set the default provider

Profiles with a ★ next to their name are the default. Click **Set Default ★** to change it.
Flows without an explicit provider setting will use the default.

### Use a specific provider in a node

1. Select an LLM node in your workflow
2. In the Object Inspector, find the **provider** dropdown
3. Select a profile or leave blank to use the default

---

## Troubleshooting

### "Connection refused" or "Cannot connect"

**For Ollama/LM Studio**:
- Verify the service is running
- Check the port number in the Base URL
- Test directly: `curl http://localhost:11434/api/tags` (Ollama) or visit `http://localhost:1234` (LM Studio)

**For cloud providers**:
- Verify your internet connection
- Check that your API key is correct and hasn't expired

### "Model not found"

**For Ollama**:
- Run `ollama pull qwen2.5-coder:14b` to pull the model
- Run `ollama list` to see available models
- Update the **Default model** field to a model you've pulled

**For other providers**:
- Verify the model name is correct and you have access to it
- Some models may not be available in your region or account tier

### "Invalid API key"

- Verify you've copied the entire key correctly
- Check the key hasn't expired
- Make sure you're using a key for the right provider

---

## More Information

For detailed setup instructions, custom port configuration, and advanced options, see:
- [docs/13_provider_setup.md](../../docs/13_provider_setup.md) — Comprehensive provider setup guide
- [README.md](../../README.md) — Quick start section

[← Help Index](../index.md)
