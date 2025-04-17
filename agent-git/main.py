#!/usr/bin/env python3
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import git
from mcp.server.fastmcp import FastMCP

# Create the MCP server (namespace "agent‑git")
mcp = FastMCP("agent‑git")


@mcp.tool()
def git_status(repo_path: str) -> str:
    """Show the working tree status."""
    repo = git.Repo(repo_path)
    return repo.git.status()


@mcp.tool()
def git_diff_unstaged(repo_path: str) -> str:
    """Show changes in the working directory that are not yet staged."""
    repo = git.Repo(repo_path)
    return repo.git.diff()


@mcp.tool()
def git_diff_staged(repo_path: str) -> str:
    """Show changes that are staged for commit."""
    repo = git.Repo(repo_path)
    return repo.git.diff("--cached")


@mcp.tool()
def git_diff(repo_path: str, target: str) -> str:
    """Show differences between HEAD and <target>."""
    repo = git.Repo(repo_path)
    return repo.git.diff(target)


@mcp.tool()
def git_add(repo_path: str, files: list[str]) -> str:
    """Stage the given files."""
    repo = git.Repo(repo_path)
    repo.index.add(files)
    return "Files staged successfully"


@mcp.tool()
def git_reset(repo_path: str) -> str:
    """Unstage all staged changes."""
    repo = git.Repo(repo_path)
    repo.index.reset()
    return "All staged changes reset"


@mcp.tool()
def git_log(repo_path: str, max_count: int = 10) -> list[str]:
    """Show the last <max_count> commits."""
    repo = git.Repo(repo_path)
    commits = list(repo.iter_commits(max_count=max_count))
    return [
        (
            f"Commit: {c.hexsha}\n"
            f"Author: {c.author}\n"
            f"Date:   {c.authored_datetime}\n"
            f"Message: {c.message}"
        )
        for c in commits
    ]


@mcp.tool()
def git_create_branch(
    repo_path: str, branch_name: str, base_branch: str | None = None
) -> str:
    """Create a new branch (optionally from <base_branch>)."""
    repo = git.Repo(repo_path)
    base = repo.refs[base_branch] if base_branch else repo.active_branch
    repo.create_head(branch_name, base)
    return f"Created branch '{branch_name}' from '{base.name}'"


@mcp.tool()
def git_checkout(repo_path: str, branch_name: str) -> str:
    """Switch to <branch_name>."""
    repo = git.Repo(repo_path)
    repo.git.checkout(branch_name)
    return f"Switched to branch '{branch_name}'"


@mcp.tool()
def git_commit_direct(repo_path: str, message: str, agent_name: str = "Claude", user_name: str = "Andor", user_email: str = "andor@andor.us") -> str:
    """Record changes with a commit. 
    
    Args:
        repo_path: Path to the git repository
        message: Commit message (must start with "[agent]")
        agent_name: Name of the agent making the commit (default: "Claude")
        user_name: Name of the user on whose behalf the commit is made (default: "Andor")
        user_email: Email to use for the commit (default: "andor@andor.us")
    """
    if not message.startswith("[agent]"):
        raise ValueError("Commit message must start with '[agent]'.")
    
    # Set author and committer information
    agent_email = user_email
    agent_full_name = f"{agent_name} Agent on behalf of {user_name}"
    
    # Create environment variables for git
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = agent_full_name
    env["GIT_AUTHOR_EMAIL"] = agent_email
    env["GIT_COMMITTER_NAME"] = agent_full_name
    env["GIT_COMMITTER_EMAIL"] = agent_email
    
    # Run git commit directly as a subprocess
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "commit", "-m", message],
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get the commit hash using git rev-parse
        hash_result = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        commit_hash = hash_result.stdout.strip()
        
        return f"Changes committed successfully with hash {commit_hash} (as '{agent_full_name}')"
    except subprocess.CalledProcessError as e:
        return f"Commit failed: {e.stderr}"


@mcp.tool()
def git_commit(repo_path: str, message: str, agent_name: str = "Claude", user_name: str = "Andor", user_email: str = "andor@andor.us") -> str:
    """Record changes with a commit (redirect to git_commit_direct).
    
    Args:
        repo_path: Path to the git repository
        message: Commit message (must start with "[agent]")
        agent_name: Name of the agent making the commit (default: "Claude")
        user_name: Name of the user on whose behalf the commit is made (default: "Andor")
        user_email: Email to use for the commit (default: "andor@andor.us")
    """
    return git_commit_direct(repo_path, message, agent_name, user_name, user_email)


@mcp.tool()
def git_show(repo_path: str, revision: str) -> str:
    """Show the contents (metadata and diff) of <revision>."""
    repo = git.Repo(repo_path)
    commit = repo.commit(revision)
    out = [
        f"Commit: {commit.hexsha}\n"
        f"Author: {commit.author}\n"
        f"Date:   {commit.authored_datetime}\n"
        f"Message: {commit.message}\n\n"
    ]
    parent = commit.parents[0] if commit.parents else None
    diff = (
        parent.diff(commit, create_patch=True)
        if parent
        else commit.diff(git.NULL_TREE, create_patch=True)
    )
    for d in diff:
        out.append(f"--- {d.a_path}\n+++ {d.b_path}\n{d.diff.decode()}\n")
    return "".join(out)


@mcp.tool()
def git_init(repo_path: str) -> str:
    """Initialize a new Git repository at <repo_path>."""
    try:
        r = git.Repo.init(path=repo_path, mkdir=True)
        return f"Initialized empty Git repository in {r.git_dir}"
    except Exception as e:
        return f"Error initializing repository: {e}"
