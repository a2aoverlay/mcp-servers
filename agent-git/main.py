#!/usr/bin/env python3
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Union

import git
from mcp.server.fastmcp import FastMCP

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent-git")

# Create the MCP server (namespace "agent-git")
mcp = FastMCP("agent-git")


def validate_repo(repo_path: str) -> git.Repo:
    """Validate and return a git.Repo object.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        git.Repo object
        
    Raises:
        ValueError: If repo_path is invalid or doesn't exist
        git.InvalidGitRepositoryError: If the path is not a valid git repository
    """
    if not repo_path:
        raise ValueError("Repository path cannot be empty")
        
    path = Path(repo_path)
    if not path.exists():
        raise ValueError(f"Repository path does not exist: {repo_path}")
        
    try:
        return git.Repo(repo_path)
    except git.InvalidGitRepositoryError:
        logger.error(f"Invalid git repository: {repo_path}")
        raise


@mcp.tool()
def git_status(repo_path: str) -> str:
    """Show the working tree status."""
    try:
        repo = validate_repo(repo_path)
        return repo.git.status()
    except Exception as e:
        logger.error(f"Error in git_status: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def git_diff_unstaged(repo_path: str) -> str:
    """Show changes in the working directory that are not yet staged."""
    try:
        repo = validate_repo(repo_path)
        return repo.git.diff()
    except Exception as e:
        logger.error(f"Error in git_diff_unstaged: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def git_diff_staged(repo_path: str) -> str:
    """Show changes that are staged for commit."""
    try:
        repo = validate_repo(repo_path)
        return repo.git.diff("--cached")
    except Exception as e:
        logger.error(f"Error in git_diff_staged: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def git_diff(repo_path: str, target: str) -> str:
    """Show differences between HEAD and <target>."""
    try:
        repo = validate_repo(repo_path)
        return repo.git.diff(target)
    except Exception as e:
        logger.error(f"Error in git_diff: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def git_add(repo_path: str, files: List[str]) -> str:
    """Stage the given files."""
    try:
        repo = validate_repo(repo_path)
        repo.index.add(files)
        return "Files staged successfully"
    except Exception as e:
        logger.error(f"Error in git_add: {e}")
        return f"Error staging files: {str(e)}"


@mcp.tool()
def git_reset(repo_path: str) -> str:
    """Unstage all staged changes."""
    try:
        repo = validate_repo(repo_path)
        repo.index.reset()
        return "All staged changes reset"
    except Exception as e:
        logger.error(f"Error in git_reset: {e}")
        return f"Error resetting staged changes: {str(e)}"


@mcp.tool()
def git_log(repo_path: str, max_count: int = 10) -> List[str]:
    """Show the last <max_count> commits."""
    try:
        repo = validate_repo(repo_path)
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
    except Exception as e:
        logger.error(f"Error in git_log: {e}")
        return [f"Error retrieving commit log: {str(e)}"]


@mcp.tool()
def git_create_branch(
    repo_path: str, branch_name: str, base_branch: Optional[str] = None
) -> str:
    """Create a new branch (optionally from <base_branch>)."""
    try:
        repo = validate_repo(repo_path)
        # Check if branch already exists
        if branch_name in repo.heads:
            return f"Branch '{branch_name}' already exists"
            
        base = repo.refs[base_branch] if base_branch else repo.active_branch
        repo.create_head(branch_name, base)
        return f"Created branch '{branch_name}' from '{base.name}'"
    except Exception as e:
        logger.error(f"Error in git_create_branch: {e}")
        return f"Error creating branch: {str(e)}"


@mcp.tool()
def git_checkout(repo_path: str, branch_name: str) -> str:
    """Switch to <branch_name>."""
    try:
        repo = validate_repo(repo_path)
        # Check if branch exists
        if branch_name not in repo.heads and branch_name != "HEAD":
            return f"Error: Branch '{branch_name}' does not exist"
            
        repo.git.checkout(branch_name)
        return f"Switched to branch '{branch_name}'"
    except Exception as e:
        logger.error(f"Error in git_checkout: {e}")
        return f"Error checking out branch: {str(e)}"


@mcp.tool()
def git_commit_direct(
    repo_path: str, 
    message: str, 
    agent_name: str = "Claude", 
    user_name: str = "Andor", 
    user_email: str = "andor@andor.us"
) -> str:
    """Record changes with a commit. 
    
    Args:
        repo_path: Path to the git repository
        message: Commit message (must start with "[agent]")
        agent_name: Name of the agent making the commit (default: "Claude")
        user_name: Name of the user on whose behalf the commit is made (default: "Andor")
        user_email: Email to use for the commit (default: "andor@andor.us")
    """
    try:
        validate_repo(repo_path)
        
        if not message.startswith("[agent]"):
            raise ValueError("Commit message must start with '[agent]'.")
        
        # Set author and committer information
        agent_email = user_email
        agent_full_name = f"MCP Agent ({agent_name}) on Behalf Of {user_name}"
        
        # Create environment variables for git
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = agent_full_name
        env["GIT_AUTHOR_EMAIL"] = agent_email
        env["GIT_COMMITTER_NAME"] = agent_full_name
        env["GIT_COMMITTER_EMAIL"] = agent_email
        
        # Run git commit directly as a subprocess
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
        logger.error(f"Commit failed: {e.stderr}")
        return f"Commit failed: {e.stderr}"
    except Exception as e:
        logger.error(f"Error in git_commit_direct: {e}")
        return f"Error committing changes: {str(e)}"


@mcp.tool()
def git_commit(
    repo_path: str, 
    message: str, 
    agent_name: str = "Claude", 
    user_name: str = "Andor", 
    user_email: str = "andor@andor.us"
) -> str:
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
    try:
        repo = validate_repo(repo_path)
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
    except Exception as e:
        logger.error(f"Error in git_show: {e}")
        return f"Error showing revision: {str(e)}"


@mcp.tool()
def git_init(repo_path: str) -> str:
    """Initialize a new Git repository at <repo_path>."""
    try:
        path = Path(repo_path)
        if path.exists() and any(path.iterdir()):
            # Check if .git directory already exists
            if (path / ".git").exists():
                return f"Repository already initialized at {repo_path}"
                
        r = git.Repo.init(path=repo_path, mkdir=True)
        return f"Initialized empty Git repository in {r.git_dir}"
    except Exception as e:
        logger.error(f"Error in git_init: {e}")
        return f"Error initializing repository: {str(e)}"


@mcp.tool()
def git_remote_add(repo_path: str, name: str, url: str) -> str:
    """Add a remote to the repository.
    
    Args:
        repo_path: Path to the git repository
        name: Name of the remote (e.g. "origin")
        url: URL of the remote repository
    """
    try:
        repo = validate_repo(repo_path)
        
        # Check if remote already exists
        for remote in repo.remotes:
            if remote.name == name:
                return f"Remote '{name}' already exists"
                
        repo.create_remote(name, url)
        return f"Added remote '{name}' with URL '{url}'"
    except Exception as e:
        logger.error(f"Error in git_remote_add: {e}")
        return f"Error adding remote: {str(e)}"


@mcp.tool()
def git_push(repo_path: str, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> str:
    """Push changes to remote repository.
    
    Args:
        repo_path: Path to the git repository
        remote: Name of the remote to push to (default: "origin")
        branch: Branch to push (default: current branch)
        force: Force push (default: False)
    """
    try:
        repo = validate_repo(repo_path)
        
        # Check if remote exists
        if remote not in [r.name for r in repo.remotes]:
            return f"Error: Remote '{remote}' does not exist"
            
        # Get the branch to push
        if branch is None:
            branch = repo.active_branch.name
            
        # Construct the push command with appropriate options
        push_command = ["push"]
        if force:
            push_command.append("--force")
        push_command.extend([remote, branch])
        
        output = repo.git.execute(["git"] + push_command)
        return f"Push successful: {output}"
    except Exception as e:
        logger.error(f"Error in git_push: {e}")
        return f"Error pushing to remote: {str(e)}"


if __name__ == "__main__":
    logger.info("Starting agent-git MCP server")
    # This will start the FastMCP server
    mcp.run()
