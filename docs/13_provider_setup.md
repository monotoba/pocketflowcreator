# Provider Setup Guide

## Overview

PocketFlow Creator supports multiple LLM providers through the **Provider Manager** dialog. You can configure named provider profiles, test connections, and use different providers for different workflows.

Supported providers:
- **Ollama** (local, free, open-source)
- **LM Studio** (local, desktop application)
- **OpenAI** (cloud-based, requires API key)
- **OpenAI-compatible** (Deepseek, Azure, Groq, etc.)
- **Anthropic** (Claude, requires API key)
- **Google Gemini** (requires API key)

## Opening Provider Manager

1. Click **Tools** → **Provider Manager**
2. The Provider Manager dialog opens with a list of profiles on the left and a profile editor on the right

## Creating a New Provider Profile

1. Click the **+ Add** button to create a new profile
2. Enter a name (e.g., "My Ollama", "OpenAI Production")
3. Select the **API type** from the dropdown
4. The **Base URL** and **Default model** fields automatically populate with sensible defaults
5. Customize the settings if needed:
   - **Base URL**: The endpoint your provider runs on
   - **Default model**: The model name to use when no model is specified
   - **Timeout**: Request timeout in seconds (default 120)
6. If required, enter an **API Key**:
   - Choose "Enter key directly" for immediate use, or
   - Choose "Read from environment variable" to load from a shell variable
7. Click **Test Connection** to verify the settings work
8. Click **OK** to save

## Provider Types

### Ollama (Local)

**What it is**: Free, open-source LLM inference engine. Runs models locally on your machine.

**Default settings**:
- **Base URL**: `http://localhost:11434`
- **Default model**: `qwen2.5-coder:14b`

**Setup**:
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Run Ollama: `ollama serve`
3. In another terminal, pull a model: `ollama pull qwen2.5-coder:14b`
4. Create a provider profile with type "Ollama (local)"
5. Verify the base URL is `http://localhost:11434`
6. Click **Test Connection** to verify

**Custom ports**:
If Ollama is running on a different port, edit the **Base URL** field:
- Default: `http://localhost:11434`
- Custom example: `http://localhost:9999` or `http://192.168.1.100:11434`

**Available models**:
List installed models with: `ollama list`
Pull additional models with: `ollama pull model-name`

### LM Studio (Local)

**What it is**: Desktop application for running LLMs locally with a graphical interface.

**Default settings**:
- **Base URL**: `http://localhost:1234/v1`
- **Default model**: `meta-llama-3.1-8b`

**Setup**:
1. Install LM Studio from [lmstudio.ai](https://lmstudio.ai)
2. Open LM Studio and load a model
3. Start the local server (usually accessible at `http://localhost:1234`)
4. Create a provider profile with type "LM Studio (local)"
5. Verify the base URL is `http://localhost:1234/v1`
6. Click **Test Connection** to verify

**Custom ports**:
If LM Studio is running on a different port, edit the **Base URL** field:
- Default: `http://localhost:1234/v1`
- Custom example: `http://localhost:8000/v1`

### OpenAI

**What it is**: Cloud-based LLM service from OpenAI. Requires an API key.

**Default settings**:
- **Base URL**: `https://api.openai.com/v1`
- **Default model**: `gpt-4o-mini`

**Setup**:
1. Create an account on [platform.openai.com](https://platform.openai.com)
2. Generate an API key from Settings → API Keys
3. Create a provider profile with type "OpenAI-compatible (OpenAI, DeepSeek, Azure, Groq, …)"
4. Enter your API key in the "API Key" field
5. Click **Test Connection** to verify

**Available models**:
- `gpt-4o` (latest, most capable)
- `gpt-4o-mini` (faster, cheaper)
- `gpt-3.5-turbo` (legacy)

### OpenAI-Compatible Services

Compatible with OpenAI's API format. Examples: Deepseek, Azure OpenAI, Groq

**Setup**:
1. Create an account and generate an API key
2. Create a provider profile with type "OpenAI-compatible"
3. Update the **Base URL** to your provider's endpoint:
   - Deepseek: `https://api.deepseek.com/v1`
   - Groq: `https://api.groq.com/openai/v1`
   - Azure OpenAI: `https://{resource-name}.openai.azure.com/v1`
4. Enter your API key
5. Update the **Default model** to match your provider's model name
6. Click **Test Connection** to verify

### Anthropic (Claude)

**What it is**: Cloud-based LLM service from Anthropic. Requires an API key.

**Default settings**:
- **Default model**: `claude-haiku-4-5`

**Setup**:
1. Create an account on [console.anthropic.com](https://console.anthropic.com)
2. Generate an API key from Settings → API Keys
3. Create a provider profile with type "Anthropic (Claude)"
4. Enter your API key in the "API Key" field
5. Click **Test Connection** to verify

**Available models**:
- `claude-opus-4-8` (most capable)
- `claude-sonnet-4-6` (balanced)
- `claude-haiku-4-5` (fast, cheap)

### Google Gemini

**What it is**: Google's LLM service. Requires an API key.

**Default settings**:
- **Default model**: `gemini-2.0-flash`

**Setup**:
1. Create an API key at [aistudio.google.com](https://aistudio.google.com)
2. Create a provider profile with type "Google Gemini"
3. Enter your API key in the "API Key" field
4. Click **Test Connection** to verify

## Testing Connections

The **Test Connection** button sends a simple test prompt to verify your provider is accessible and working.

**To test a provider**:
1. Configure the provider profile
2. Click **Test Connection**
3. The button shows "Testing…" while the test runs
4. After ~5 seconds, you'll see one of:
   - **✓ Connection successful** — provider is working
   - **✗ [error message]** — there's a problem (see troubleshooting below)
   - **✗ Test timed out (30 s)** — provider took too long to respond

## Troubleshooting

### "Connection refused" or "Cannot connect"

**For Ollama/LM Studio**:
- Verify the service is running
- Check the port number in the Base URL matches what the service uses
- Try `curl http://localhost:11434/api/tags` to test Ollama directly
- For Ollama, check logs: `ollama serve`

**For cloud providers**:
- Verify your internet connection
- Check that your API key is correct and hasn't expired
- Verify the Base URL is correct for your provider

### "Model not found"

**For Ollama**:
- Pull the model: `ollama pull qwen2.5-coder:14b`
- List available models: `ollama list`
- Update the **Default model** field to a model you've pulled

**For LM Studio**:
- Load a model in the LM Studio application
- Verify the model name matches what's in the **Default model** field

**For cloud providers**:
- Verify you have access to the model
- Check the model name is spelled correctly
- Some models may not be available in your region or account tier

### "Invalid API key"

- Verify you've copied the entire API key correctly
- Check the key hasn't expired
- Make sure you're using a key for the right provider (OpenAI key won't work for Anthropic, etc.)

### "Base URL is wrong"

The Base URL field now shows for all provider types, allowing you to:
- Change the port (e.g., Ollama on port 9999 instead of 11434)
- Change the hostname (e.g., `192.168.1.100` instead of `localhost`)
- Override completely for custom setups

Common issues:
- **Typo in URL**: Check spelling and make sure protocol is `http://` or `https://`
- **Port mismatch**: Verify the port number matches where the service runs
- **Hostname**: Use `localhost`, `127.0.0.1`, or your machine's IP address
- **Missing `/v1` suffix**: Some providers require `/v1` at the end

## Using Providers in Workflows

### Set Default Provider

1. Open Provider Manager
2. Select a profile
3. Click **Set Default ★** to make it the default

### Use Provider in LLM Node

1. Select an LLM node in your workflow
2. In the Object Inspector, find the **provider** field
3. Choose a profile from the dropdown, or leave blank to use the default

### Runtime Selection

When running a flow:
- If an LLM node has a specific provider set, it uses that
- Otherwise, it uses the default provider
- If no provider is configured, it uses MockProvider (fake responses for testing)

## API Key Security

### Direct Storage
By default, API keys are **not** stored in your project file. They're stored separately in your system's settings:
- **Linux/macOS**: `~/.config/[APP]/[APP].conf`
- **Windows**: Registry

### Include in Project
To include API keys in the project file (for sharing/backup):
1. Open Provider Manager
2. Check **Include API keys in project file**
3. ⚠️ **Warning**: This stores keys in plain text. Only use for non-production projects or when keys are not sensitive.

### Environment Variables
For production setups:
1. In Provider Manager, select "Read from environment variable"
2. Enter the variable name (e.g., `OPENAI_API_KEY`)
3. Set the variable in your shell before running PocketFlow Creator

Example:
```bash
export OPENAI_API_KEY="sk-..."
./scripts/run_app.sh
```

## Best Practices

1. **Test before using**: Always click "Test Connection" after creating a profile
2. **Use meaningful names**: Name profiles clearly (e.g., "Ollama Local Dev", "OpenAI Production")
3. **Secure API keys**: Use environment variables for production, not direct entry
4. **Custom ports**: If you change ports, update the Base URL field
5. **Model availability**: Verify the model is available before using it in a flow
6. **Timeout settings**: Increase timeout for large models or slow connections

## Examples

### Local Development (Ollama)
```
Name: Local Ollama
Type: Ollama (local)
Base URL: http://localhost:11434
Default model: qwen2.5-coder:14b
API Key: (none)
```

### Production OpenAI
```
Name: OpenAI Production
Type: OpenAI-compatible
Base URL: https://api.openai.com/v1
Default model: gpt-4o
API Key: (from environment: OPENAI_API_KEY)
```

### Remote Ollama
```
Name: Remote Ollama
Type: Ollama (local)
Base URL: http://192.168.1.100:11434
Default model: qwen2.5-coder:14b
API Key: (none)
```

### Custom Port LM Studio
```
Name: LM Studio Custom Port
Type: LM Studio (local)
Base URL: http://localhost:9999/v1
Default model: neural-chat-7b
API Key: (none)
```
