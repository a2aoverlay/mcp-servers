import pytest
import shutil
from pathlib import Path
import git
from agent_git.server import (
    git_checkout,
    git_commit,
    git_add,
    git_status,
    git_diff_unstaged,
    git_diff_staged,
    git_diff,
    git_create_branch,
    git_init,
    git_show,
)
import os

@pytest.fixture
def test_repository(tmp_path: Path):
    repo_path = tmp_path / "temp_test_repo"
    # Initialize repository.
    test_repo = git.Repo.init(repo_path)
    
    # Create an initial file and commit it.
    file_path = repo_path / "test.txt"
    file_path.write_text("initial content")
    test_repo.index.add(["test.txt"])
    test_repo.index.commit("initial commit")
    
    yield test_repo
    shutil.rmtree(repo_path)

def test_git_checkout_existing_branch(test_repository):
    test_repository.git.branch("test-branch")
    result = git_checkout(test_repository, "test-branch")
    assert "Switched to branch 'test-branch'" in result
    assert test_repository.active_branch.name == "test-branch"

def test_git_checkout_nonexistent_branch(test_repository):
    with pytest.raises(git.GitCommandError):
        git_checkout(test_repository, "nonexistent-branch")

def test_git_commit_valid_message(test_repository):
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("updated content")
    test_repository.git.add("test.txt")
    result = git_commit(test_repository, "[agent] updated test.txt")
    assert "Changes committed successfully" in result
    assert "[agent] updated test.txt" in test_repository.head.commit.message

def test_git_commit_invalid_message(test_repository):
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("another update")
    test_repository.git.add("test.txt")
    with pytest.raises(ValueError, match="Commit message must start with '\\[agent\\]'"):
        git_commit(test_repository, "updated test.txt")

def test_git_diff_unstaged_and_status(test_repository):
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("unstaged change")
    status = git_status(test_repository)
    diff_unstaged = git_diff_unstaged(test_repository)
    assert "modified:" in status
    assert diff_unstaged.strip() != ""

def test_git_create_branch(test_repository):
    result = git_create_branch(test_repository, "new-branch")
    assert "Created branch 'new-branch'" in result
    new_branch = [b for b in test_repository.branches if b.name == "new-branch"]
    assert len(new_branch) == 1

def test_git_show_initial_commit(test_repository):
    commit_hash = test_repository.head.commit.hexsha
    output = git_show(test_repository, commit_hash)
    assert commit_hash in output
    assert "initial commit" in output

def test_git_commit_with_signing(monkeypatch, test_repository):
    """
    Test commit signing by simulating that a dummy signing key is registered.
    We simulate this by creating a file named .agent_signing_key in the repository's
    working tree and then patching the commit method on the Git instance.
    """
    # Write a dummy signing key.
    key_file = Path(test_repository.working_tree_dir) / ".agent_signing_key"
    dummy_key = "DUMMYKEY123"
    key_file.write_text(dummy_key)
    
    # Modify a file and stage it.
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("signed update")
    test_repository.git.add("test.txt")
    
    # Define a fake commit function to capture arguments.
    def fake_commit(*args, **kwargs):
        fake_commit.called_args = args
        # Create a fake commit object with a predetermined hash.
        class FakeCommit:
            hexsha = "signed123"
        # (Simulate updating the repository HEAD if needed.)
        test_repository.head.commit.hexsha = "signed123"
        return FakeCommit()
    
    # Patch the commit method on the specific Git instance.
    monkeypatch.setattr(test_repository.git, "commit", fake_commit)
    
    result = git_commit(test_repository, "[agent] signed update")
    
    # Assert that the commit was invoked with the signing flag.
    assert "-S" in fake_commit.called_args, f"Expected '-S' in commit args, got: {fake_commit.called_args}"
    # Verify the fake commit hash appears in the return message.
    assert "Changes committed successfully" in result
    assert "signed123" in result