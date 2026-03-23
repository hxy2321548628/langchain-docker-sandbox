# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Deep Agents application that provides AI agents with sandboxed code execution capabilities using a custom Docker sandbox backend. The project implements `DockerSandbox` class that integrates with Deep Agents framework, allowing agents to execute commands and manipulate files in a Docker container.

## Architecture

**Core Components:**
- `langchain_docer_sandbox.py` - Custom `DockerSandbox` backend implementing `BaseSandbox` interface
- `example/` - Example code demonstrating Deep Agent usage with DockerSandbox
- `test/` - Pytest test suite for DockerSandbox
- `filesystem/` - Directory mounted to Docker Compose sandbox container at `/workspace`
- `docker-compose.yml` - Docker Compose configuration for the uv-sandbox container

**DockerSandbox Backend:**
```python
backend = DockerSandbox(container_name="uv-sandbox", work_dir="/workspace")

agent = create_deep_agent(
    model="deepseek:deepseek-chat",
    backend=backend,
    system_prompt="...",
)
```

The agent receives messages in the format `{"messages": [{"role": "user", "content": "..."}]}` and returns results in `result["messages"][-1].content`.

**Docker Container Setup:**
- Container name: `uv-sandbox`
- Image: `astral/uv:python3.13-bookworm-slim`
- Working directory: `/workspace`
- Local `filesystem/` directory mounted at `/workspace`
- Uses Docker SDK for container operations

**DockerSandbox Capabilities:**
- `execute()` - Run shell commands in the container
- `write()` - Create new files via tar archive
- `read()` - Read files with line numbers (supports offset/limit)
- `edit()` - Replace string occurrences in files (single or all)
- `upload_files()` - Batch file upload
- `download_files()` - Batch file download
- `ls_info()` - Directory listing
- `glob_info()` - Pattern-based file search
- `grep_raw()` - Text search with structured output

**Configuration Management:**
- Environment variables stored in `example/.env`
- Settings loaded via Pydantic Settings in `example/settings.py`
- Required environment variables: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`

## Common Commands

```bash
# Start sandbox container
docker compose up -d

# Enter sandbox container
docker compose exec uv-sandbox bash

# Stop sandbox container
docker compose down

# Run example agent
cd example && python main.py

# Install/update dependencies
uv sync

# Run tests
uv run pytest

# Run specific test
uv run pytest test/test_docker_sandbox.py::TestDockerSandboxExecute::test_execute_simple_command

# Code linting and formatting
ruff check .
ruff check --fix .
ruff format .
```

## Dependencies

**Core Dependencies:**
- `deepagents>=0.4.11` - Deep Agents framework
- `docker>=7.1.0` - Docker SDK for Python

**Development Dependencies:**
- `pytest>=9.0.2` - Testing framework
- `dotenv>=0.9.9` - Environment variable loading
- `langchain-daytona>=0.0.4` - Daytona sandbox integration (optional, for reference)
- `langchain-deepseek>=1.0.1` - DeepSeek LLM provider
- `pydantic>=2.12.5`, `pydantic-settings>=2.13.1` - Configuration
- `ruff>=0.15.6` - Linting and formatting
- `tavily-python>=0.7.23` - Search capabilities

## Code Style

- Uses Ruff with line length of 150 characters
- Double quotes for strings
- Google-style docstrings
- Import order: standard-library → third-party → first-party → local-folder
- Two blank lines after imports
- Python 3.13+ required

## Testing

Tests are located in `test/test_docker_sandbox.py`. Run tests with `uv run pytest`.

**Test Fixtures:**
- `backend()` - Creates `DockerSandbox` instance for testing (requires uv-sandbox container running)

**Important:** The uv-sandbox container must be running before executing tests.

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

**Online API Reference:**
- `https://reference.langchain.com/python/deepagents` - Deep Agents Python API
- `https://reference.langchain.com/python/langchain` - LangChain Python API
- `https://reference.langchain.com/python/langgraph` - LangGraph Python API
- `https://reference.langchain.com/python/integrations/overview` - Python integrations

## Important Notes

- The `filesystem/` directory is mounted to the Docker Compose sandbox at `/workspace` for isolated code execution
- Tests require the uv-sandbox container to be running (`docker compose up -d`)
- Never commit `.env` file with real API keys
- All file operations are relative to `/workspace` inside the container
- File uploads use tar archives for efficiency and proper permission handling
