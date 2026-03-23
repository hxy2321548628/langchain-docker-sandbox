# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Deep Agents application that provides AI agents with sandboxed code execution capabilities. The project uses the Deep Agents framework with Daytona sandbox integration and DeepSeek as the LLM provider.

## Architecture

**Core Components:**
- `main.py` - Entry point that creates a Deep Agent with Daytona sandbox backend
- `settings.py` - Pydantic Settings configuration for environment variables
- `filesystem/` - Directory mounted by Docker Compose sandbox container

**Agent Pattern:**
```python
sandbox = Daytona().create()
backend = DaytonaSandbox(sandbox=sandbox)

agent = create_deep_agent(
    model="deepseek:deepseek-chat",
    backend=backend,
    system_prompt="...",
)
```

The agent receives messages in the format `{"messages": [{"role": "user", "content": "..."}]}` and returns results in `result["messages"][-1].content`.

**Configuration Management:**
- Environment variables are stored in `.env`
- Settings are loaded via Pydantic Settings with `SecretStr` for sensitive values
- Required environment variables: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `TAVILY_API_KEY`, `DAYTONA_API_KEY`

## Common Commands

```bash
# Run the agent
uv run python main.py

# Docker Compose sandbox
docker compose up -d               # Start sandbox container
docker compose exec uv-sandbox bash # Enter sandbox container
docker compose down                # Stop sandbox container

# Install/update dependencies
uv sync

# Code linting and formatting
ruff check .                # Check for issues
ruff check --fix .          # Auto-fix issues
ruff format .               # Format code
```

## Dependencies

- `deepagents>=0.4.11` - Deep Agents framework
- `langchain-daytona>=0.0.4` - Daytona sandbox integration
- `langchain-deepseek>=1.0.1` - DeepSeek LLM provider
- `tavily-python>=0.7.23` - Search capabilities
- `ruff>=0.15.6` - Linting and formatting (line length: 150)
- `pydantic>=2.12.5`, `pydantic-settings>=2.13.1` - Configuration

## Code Style

- Uses Ruff with line length of 150 characters
- Double quotes for strings
- Google-style docstrings
- Import order: standard-library → third-party → first-party → local-folder
- Two blank lines after imports
- Python 3.13+ required

## Reference Documentation

Local reference documentation is available at `./.langchain-langgraph-deepagent-docs`:

**Deep Agents:**
- `/src/oss/deepagents/overview.mdx` - Deep Agents overview
- `/src/oss/deepagents/quickstart.mdx` - Quick start guide
- `/src/oss/deepagents/sandboxes.mdx` - Sandbox configuration
- `/src/oss/deepagents/backends.mdx` - Backend options
- `/src/oss/deepagents/subagents.mdx` - Sub-agent orchestration
- `/src/oss/deepagents/human-in-the-loop.mdx` - Human approval workflows
- `/src/oss/deepagents/streaming.mdx` - Streaming responses
- `/src/oss/deepagents/skills.mdx` - SKILL.md format for tools
- `/src/oss/deepagents/customization.mdx` - Agent customization

**LangGraph:**
- `/src/oss/langgraph/overview.mdx` - LangGraph framework overview
- `/src/oss/langgraph/quickstart.mdx` - Quick start guide
- `/src/oss/langgraph/graph-api.mdx` - StateGraph API reference
- `/src/oss/langgraph/functional-api.mdx` - Functional API guide
- `/src/oss/langgraph/persistence.mdx` - State persistence and checkpoints
- `/src/oss/langgraph/interrupts.mdx` - Interrupts and human-in-the-loop
- `/src/oss/langgraph/streaming.mdx` - Streaming updates
- `/src/oss/langgraph/memory.mdx` - Memory integration
- `/src/oss/langgraph/workflows-agents.mdx` - Agent workflow patterns

**LangChain:**
- `/src/oss/langchain/overview.mdx` - LangChain framework overview
- `/src/oss/langchain/agents.mdx` - Agent patterns
- `/src/oss/langchain/tools.mdx` - Tool system
- `/src/oss/langchain/models.mdx` - Model integrations
- `/src/oss/langchain/streaming.mdx` - Streaming in LangChain
- `/src/oss/langchain/human-in-the-loop.mdx` - Human approval patterns

**Documentation Contributing:**
- `/README.md` - LangChain docs repository guide
- `/CLAUDE.md` - Documentation authoring guidelines
- `/Makefile` - Build commands (see `make help` for full list)

**API Reference:**
- `/src/oss/reference/overview.mdx` - API reference overview
- `/src/oss/reference/deepagents-python.mdx` - Deep Agents Python API
- `/src/oss/reference/langchain-python.mdx` - LangChain Python API
- `/src/oss/reference/langgraph-python.mdx` - LangGraph Python API
- `/src/oss/reference/integrations-python.mdx` - Python integrations API
- `/src/oss/reference/deepagents-javascript.mdx` - Deep Agents JavaScript API
- `/src/oss/reference/langchain-javascript.mdx` - LangChain JavaScript API
- `/src/oss/reference/langgraph-javascript.mdx` - LangGraph JavaScript API
- `/src/oss/reference/integrations-javascript.mdx` - JavaScript integrations API

**Online API Reference:**
- `https://reference.langchain.com/python/deepagents` - Deep Agents Python API
- `https://reference.langchain.com/python/langchain` - LangChain Python API
- `https://reference.langchain.com/python/langgraph` - LangGraph Python API
- `https://reference.langchain.com/python/integrations/overview` - Python integrations
- `https://reference.langchain.com/python/langchain_mcp_adapters/` - MCP adapters Python
- `https://reference.langchain.com/javascript/deepagents` - Deep Agents JS API
- `https://reference.langchain.com/javascript/langchain` - LangChain JS API
- `https://reference.langchain.com/javascript/langchain-langgraph` - LangGraph JS API
- `https://reference.langchain.com/javascript/langchain-community` - JS integrations
- `https://reference.langchain.com/javascript/langchain-mcp-adapters` - MCP adapters JS

## Important Notes

- The Daytona sandbox is explicitly stopped on exception for cleanup
- Algorithm directory (if exists) is excluded from linting
- Never commit `.env` file with real API keys
- The `filesystem/` directory is mounted to the Docker Compose sandbox at `/workspace` for isolated code execution
