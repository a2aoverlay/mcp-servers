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

@pytest.fixture
def test_repository(tmp_path: Path):
    """
    Creates a temporary Git repository for testing.
    """
    repo_path = tmp_path / "temp_test_repo"
    test_repo = git.Repo.init(repo_path)

    # Create an initial file and commit it.
    file_path = repo_path / "test.txt"
    file_path.write_text("initial content")
    test_repo.index.add(["test.txt"])
    test_repo.index.commit("initial commit")

    yield test_repo
    shutil.rmtree(repo_path)


@pytest.fixture
def mock_git_commit(monkeypatch):
    """
    Patch `git.cmd.Git._call_process` so we can intercept calls to `git commit`.
    This avoids real GPG usage, and it allows us to see the arguments.
    """
    import git.cmd

    real_call_process = git.cmd.Git._call_process

    def fake_call_process(self, command, *args, **kwargs):
        """
        If the command is 'commit', store arguments and return a fake response.
        Otherwise, delegate to the original _call_process for normal operations.
        """
        if command == "commit":
            fake_call_process.commit_args = (command, args, kwargs)
            # Simulate success output (GitPython typically expects bytes).
            return b"Fake commit success\n"
        else:
            return real_call_process(self, command, *args, **kwargs)

    monkeypatch.setattr(git.cmd.Git, "_call_process", fake_call_process)
    return fake_call_process


def test_git_checkout_existing_branch(test_repository):
    test_repository.git.branch("test-branch")
    result = git_checkout(test_repository, "test-branch")
    assert "Switched to branch 'test-branch'" in result
    assert test_repository.active_branch.name == "test-branch"


def test_git_checkout_nonexistent_branch(test_repository):
    with pytest.raises(git.GitCommandError):
        git_checkout(test_repository, "nonexistent-branch")


def test_git_commit_valid_message(test_repository, mock_git_commit):
    """
    Verifies git_commit succeeds with a message that starts with '[agent]'.
    Also checks that '-S' and '-m' are passed to the commit command.
    """
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("updated content")
    test_repository.git.add("test.txt")

    result = git_commit(test_repository, "[agent] updated test.txt")

    # Confirm the function returns the success text
    assert "Changes committed successfully" in result

    # Check that we DID attempt a commit with the right flags
    command, args, kwargs = mock_git_commit.commit_args
    assert command == "commit"
    assert "-S" in args, f"Expected '-S' in commit args, got: {args}"
    assert "-m" in args, f"Expected '-m' in commit args, got: {args}"
    assert "[agent] updated test.txt" in args


def test_git_commit_invalid_message(test_repository, mock_git_commit):
    """
    Verifies git_commit raises an error if the message doesn't start with '[agent]'.
    """
    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("another update")
    test_repository.git.add("test.txt")

    with pytest.raises(ValueError, match="Commit message must start with '\\[agent\\]'"):
        git_commit(test_repository, "updated test.txt")

    # Because it failed before calling `repo.git.commit`,
    # we expect NO commit_args set
    assert not hasattr(mock_git_commit, "commit_args")


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


def test_git_commit_with_signing(test_repository, mock_git_commit):
    """
    Demonstrates if your code conditionally checks for a .agent_signing_key,
    it would sign with -S. If you always sign, we just confirm '-S' is present.
    """
    # If your code checks for a signing key, place one here:
    # (test_repository.working_tree_dir / ".agent_signing_key").write_text("FAKEKEY123")

    file_path = Path(test_repository.working_tree_dir) / "test.txt"
    file_path.write_text("signed update")
    test_repository.git.add("test.txt")

    result = git_commit(test_repository, "[agent] signed update")
    assert "Changes committed successfully" in result

    # Check commit args
    command, args, kwargs = mock_git_commit.commit_args
    assert command == "commit"
    assert "-S" in args, f"Expected '-S' in commit args, got: {args}"
    assert "[agent] signed update" in args