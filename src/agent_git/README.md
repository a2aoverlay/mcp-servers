# agent-git: A git MCP server

## Overview

A Model Context Protocol server for Git repository interaction and automation. This server provides tools to read, search, and manipulate Git repositories via Large Language Models.

Please note that mcp-server-git is currently in early development. The functionality and available tools are subject to change and expansion as we continue to develop and improve the server.

## Quick Start

```bash
# Install with uv
uvx agent-git --repository /path/to/repo

# Use with Claude Desktop
# Add server configuration to claude_desktop_config.json (see Configuration section)
```

## Requirements

- Python 3.8+
- Git command-line tools installed
- Valid Git repository with proper permissions

## Available Tools

1. `git_status`
   - Shows the working tree status
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Current status of working directory as text output

2. `git_diff_unstaged`
   - Shows changes in working directory not yet staged
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Diff output of unstaged changes

3. `git_diff_staged`
   - Shows changes that are staged for commit
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Diff output of staged changes

4. `git_diff`
   - Shows differences between branches or commits
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `target` (string): Target branch or commit to compare with
   - Returns: Diff output comparing current state with target

5. `git_commit`
   - Records changes to the repository
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `message` (string): Commit message
   - Returns: Confirmation with new commit hash

6. `git_add`
   - Adds file contents to the staging area
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `files` (string[]): Array of file paths to stage
   - Returns: Confirmation of staged files

7. `git_reset`
   - Unstages all staged changes
   - Input:
     - `repo_path` (string): Path to Git repository
   - Returns: Confirmation of reset operation

8. `git_log`
   - Shows the commit logs
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `max_count` (number, optional): Maximum number of commits to show (default: 10)
   - Returns: Array of commit entries with hash, author, date, and message

9. `git_create_branch`
   - Creates a new branch
   - Inputs:
     - `repo_path` (string): Path to Git repository
     - `branch_name` (string): Name of the new branch
     - `start_point` (string, optional): Starting point for the new branch
   - Returns: Confirmation of branch creation

10. `git_checkout`
    - Switches branches
    - Inputs:
      - `repo_path` (string): Path to Git repository
      - `branch_name` (string): Name of branch to checkout
    - Returns: Confirmation of branch switch

11. `git_show`
    - Shows the contents of a commit
    - Inputs:
      - `repo_path` (string): Path to Git repository
      - `revision` (string): The revision (commit hash, branch name, tag) to show
    - Returns: Contents of the specified commit

12. `git_init`
    - Initializes a Git repository
    - Inputs:
      - `repo_path` (string): Path to directory to initialize git repo
    - Returns: Confirmation of repository initialization

## Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *agent-git*.

### Using PIP

Alternatively you can install `agent-git` via pip:

```
pip install agent-git
```

After installation, you can run it as a script using:

```
python -m agent_git
```

## Command-line Arguments

```
--repository PATH  Path to Git repository (required)
--verbose          Enable verbose logging
--debug            Enable debug mode
--help             Show help message
```

## Configuration

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "git": {
    "command": "uvx",
    "args": ["agent-git", "--repository", "path/to/git/repo"]
  }
}
```
</details>

<details>
<summary>Using docker</summary>

* Note: replace '/Users/username' with the a path that you want to be accessible by this tool

```json
"mcpServers": {
  "git": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "--mount", "type=bind,src=/Users/username,dst=/Users/username", "mcp/git"]
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"mcpServers": {
  "git": {
    "command": "python",
    "args": ["-m", "agent_git", "--repository", "path/to/git/repo"]
  }
}
```
</details>

### Usage with [Zed](https://github.com/zed-industries/zed)

Add to your Zed settings.json:

<details>
<summary>Using uvx</summary>

```json
"context_servers": [
  "agent-git": {
    "command": {
      "path": "uvx",
      "args": ["agent-git"]
    }
  }
],
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"context_servers": {
  "agent-git": {
    "command": {
      "path": "python",
      "args": ["-m", "agent_git"]
    }
  }
},
```
</details>

## Security Considerations

- The server executes Git commands using the permissions of the user running the server
- All commit messages must begin with "[agent]" prefix for proper tracking
- GPG signing is required for all commits (-S flag)
- The server automatically generates and manages a dedicated GPG key for agent-signed commits
- All commits made through this server are cryptographically signed with the agent's GPG key
- The agent's GPG key uses the email "agent@model.context.protocol" for clear identification
- Commits can be verified using standard Git GPG verification tools to ensure they were made by the agent
- Avoid exposing sensitive repository information through the MCP server

## Debugging

You can use the MCP inspector to debug the server. For uvx installations:

```
npx @modelcontextprotocol/inspector uvx agent-git
```

Or if you've installed the package in a specific directory or are developing on it:

```
cd path/to/servers/src/git
npx @modelcontextprotocol/inspector uv run agent-git
```

Running `tail -n 20 -f ~/Library/Logs/Claude/mcp*.log` will show the logs from the server and may
help you debug any issues.

## Development

If you are doing local development, there are two ways to test your changes:

1. Run the MCP inspector to test your changes. See [Debugging](#debugging) for run instructions.

2. Test using the Claude desktop app. Add the following to your `claude_desktop_config.json`:

### Development Environment Setup

```bash
# Install development dependencies
cd src/agent_git
pip install -e ".[dev]"  # or use uv

# Run tests
python -m pytest

# Run specific test
python -m pytest tests/test_server.py::test_git_commit_valid_message -v

# Lint code
ruff check .

# Type check
pyright
```

### Docker

```json
{
  "mcpServers": {
    "git": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--mount", "type=bind,src=/Users/username/Desktop,dst=/projects/Desktop",
        "--mount", "type=bind,src=/path/to/other/allowed/dir,dst=/projects/other/allowed/dir,ro",
        "--mount", "type=bind,src=/path/to/file.txt,dst=/projects/path/to/file.txt",
        "mcp/git"
      ]
    }
  }
}
```

### UVX
```json
{
"mcpServers": {
  "git": {
    "command": "uv",
    "args": [ 
      "--directory",
      "/<path to mcp-servers>/mcp-servers/src/agent_git",
      "run",
      "agent-git"
    ]
  }
}
```

## Contribution Guidelines

1. Follow PEP 8 conventions for Python code formatting
2. Use explicit type hints for all functions and class attributes
3. Use Pydantic models for data validation and schema definition
4. Exception handling: Use specific exceptions with descriptive error messages
5. All commit messages must begin with "[agent]" prefix
6. GPG signing is required for all commits (-S flag)

## Build

Docker build:

```bash
cd src/git
docker build -t mcp/git .
```

## Troubleshooting

- Check file permissions if you encounter access denied errors
- Ensure the Git repository path exists and is valid
- Verify that the Git command-line tools are installed and accessible
- For commit issues, confirm your commit messages start with "[agent]"
- For signing issues:
  - The server creates and manages its own GPG key automatically
  - To view the agent's GPG key: `git log --show-signature` to see commits signed by the agent
  - If GPG errors occur, check that `gnupg` is installed on your system
  - The agent key is stored in a secure keyring that persists between sessions

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.