# First Agentic Workflow

Built on the **WAT Framework** (Workflows, Agents, Tools) — an architecture that separates AI reasoning from deterministic execution for reliable, self-improving automation.

## Structure

```
workflows/      # Markdown SOPs — the instructions
tools/          # Python scripts — the execution
.tmp/           # Temporary/intermediate files (disposable)
.env            # API keys & credentials (gitignored)
CLAUDE.md       # Agent operating instructions
```

## How It Works

1. **Workflows** define *what* to do (plain-language SOPs)
2. **Agent** reads workflows and makes decisions (AI layer)
3. **Tools** execute deterministic tasks (Python scripts)

## Setup

```bash
pip install -r requirements.txt
```

Add your API keys to `.env` before running any tools.
