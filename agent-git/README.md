# Agent-Git MCP Server

A MCP (Machine Collaboration Protocol) server that provides Git functionality for AI agents. This server enables AI agents to perform Git operations through a standardized API. The difference between this an the https://github.com/modelcontextprotocol/servers/tree/main/src/git/src/mcp_server_git is that it signs using a particular format that specifies it's from an agent:

**Example:**
```
Commit: 42118bba8538b6c046dea9c08821e570bc8d73e4
Author: Claude Agent on behalf of Andor <andor@andor.us>
Committer: Claude Agent on behalf of Andor <andor@andor.us>
Date: Wed Apr 16 23:21:23 2025 -0700
Message: [agent] Add custom committer name format functionality
```
This allows you to verify which commits were done by an agent and which were done by you. 

## Features

- Git repository operations (status, diff, log)
- File staging and commit management
- Branch creation and switching
- Support for AI agent-attributed commits

## Installation

```bash
# Install with pip
pip install agent-git

# Development installation
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

## Usage

The agent-git server can be used as part of an MCP environment:

```python
from mcp.client import Client

# Connect to the agent-git MCP server
client = Client("agent-git")

# Example: Check repository status
status = client.git_status(repo_path="/path/to/repo")
print(status)

# Example: Stage files
client.git_add(repo_path="/path/to/repo", files=["README.md"])

# Example: Create a commit
client.git_commit(
    repo_path="/path/to/repo",
    message="[agent] Update README.md",
    agent_name="Claude"
)
```

## API Reference

The server provides the following Git operations:

- `git_status(repo_path)`: Show working tree status
- `git_diff_unstaged(repo_path)`: Show unstaged changes
- `git_diff_staged(repo_path)`: Show staged changes
- `git_diff(repo_path, target)`: Show differences to target
- `git_add(repo_path, files)`: Stage files
- `git_reset(repo_path)`: Unstage all changes
- `git_log(repo_path, max_count)`: Show commit history
- `git_create_branch(repo_path, branch_name, base_branch)`: Create a new branch
- `git_checkout(repo_path, branch_name)`: Switch branches
- `git_commit(repo_path, message, agent_name, user_name, user_email)`: Create a commit
- `git_show(repo_path, revision)`: Show commit details
- `git_init(repo_path)`: Initialize a repository

## Requirements

- Python ≥ 3.11
- Dependencies: mcp[cli], click, gitpython, pydantic

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines, including code style, testing protocols, and Git conventions.

## License

This project is licensed under the terms specified in the repository.
