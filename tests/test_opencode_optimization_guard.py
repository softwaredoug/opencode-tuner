import os
import shutil
import subprocess
import tempfile

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def require_opencode():
    if shutil.which("opencode") is None:
        pytest.skip("opencode not found on PATH")


def clone_repo():
    temp_dir = tempfile.TemporaryDirectory()
    repo_dir = os.path.join(temp_dir.name, "rel-optimization")
    subprocess.run(
        ["git", "clone", REPO_ROOT, repo_dir],
        check=True,
        capture_output=True,
        text=True,
    )
    return temp_dir, repo_dir


def run_opencode(repo_dir, optimization_value, prompt):
    env = os.environ.copy()
    env["OPENCODE_OPTIMIZATION"] = optimization_value
    return subprocess.run(
        ["opencode", "run", prompt],
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
    )


def git_diff_names(repo_dir):
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def test_opencode_blocks_main_py_when_optimization_on():
    require_opencode()
    temp_dir, repo_dir = clone_repo()
    try:
        result = run_opencode(
            repo_dir,
            "On",
            'Add print("Forbidden Edit Test") near the end of main.py.',
        )
        combined_output = f"{result.stdout}\n{result.stderr}"
        assert "Disallowed new changes detected" in combined_output
        assert "main.py" not in git_diff_names(repo_dir)
    finally:
        temp_dir.cleanup()


def test_opencode_allows_main_py_when_optimization_off():
    require_opencode()
    temp_dir, repo_dir = clone_repo()
    try:
        result = run_opencode(
            repo_dir,
            "Off",
            'Add print("Allowed Edit Test") near the end of main.py.',
        )
        combined_output = f"{result.stdout}\n{result.stderr}"
        assert result.returncode == 0, combined_output
        assert "main.py" in git_diff_names(repo_dir)
    finally:
        temp_dir.cleanup()
