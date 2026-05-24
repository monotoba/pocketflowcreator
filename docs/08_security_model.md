# Security Model

PocketFlow Creator may run user code, shell tools, file writers, network tools, and LLM provider calls. These are powerful and need visible safety controls.

## Safety Levels

```text
read_only       Reads files or data only.
file_write      Writes project or user files.
network         Accesses external network resources.
shell           Runs shell commands.
destructive     Deletes, overwrites, or modifies outside project boundaries.
```

## Requirements

- Shell and destructive tools must be visually marked.
- Untrusted templates must be marked before import.
- Provider credentials must not be stored in project files by default.
- File-write tools should require explicit paths or project-relative restrictions.
- Run configuration should be able to disable dangerous tools.
