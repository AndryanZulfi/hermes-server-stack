#!/usr/bin/env python3
"""
Hermes Comprehensive Git Synchronization Automation (Watchdog Pattern)
Synchronizes two-way with GitHub repositories for:
1. Skills repository: ~/.hermes/skills -> https://github.com/AndryanZulfi/hermes-skills.git
2. Profile Skills (e.g. ~/.hermes/profiles/web-dev/skills) -> https://github.com/AndryanZulfi/hermes-skills.git
3. Stack & Agent Config: ~/Documents/hermes-server-stack -> https://github.com/AndryanZulfi/hermes-server-stack.git
   - Two-way sync: user.md, SOUL.md, vocab_history.json, memories/, plugins/, scripts/, refleksi/
   - Submodule updates (skills & honcho)
4. Agent Core: ~/.hermes/hermes-agent -> https://github.com/NousResearch/hermes-agent.git (Upstream pull)

Execution triggers:
- macOS LaunchAgent: com.andryanzulfi.hermes-git-sync (StartInterval 3600, RunAtLoad true)
- Auto-catch up on Wake from Sleep / Boot
- Hermes internal cron job (no_agent: true)
- On-demand / manual execution: python3 sync_hermes_git.py [--verbose]
"""

import os
import sys
import fcntl
import hashlib
import shutil
import subprocess
import argparse
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))

HERMES_DIR = os.path.expanduser("~/.hermes")
SKILLS_DIR = os.path.join(HERMES_DIR, "skills")
PROFILES_DIR = os.path.join(HERMES_DIR, "profiles")
AGENT_DIR = os.path.join(HERMES_DIR, "hermes-agent")
STACK_DIR = os.path.expanduser("~/Documents/hermes-server-stack")
STACK_CONFIG_DIR = os.path.join(STACK_DIR, "hermes-config")
LOCK_FILE = os.path.join(HERMES_DIR, "cache", "hermes_git_sync.lock")

# Items to synchronize two-way between ~/.hermes and hermes-server-stack/hermes-config
SYNC_FILES = ["user.md", "SOUL.md", "vocab_history.json"]
SYNC_DIRS = ["memories", "plugins", "scripts", "refleksi"]

EXCLUDE_PATTERNS = {
    ".DS_Store",
    "__pycache__",
    "node_modules",
    ".git",
    ".locks",
    "*.pyc",
    "*.tmp",
    "*.lock",
    "whatsapp-bridge/node_modules"
}

def get_wib_timestamp():
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")

def file_hash(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def should_exclude(rel_path):
    parts = rel_path.split(os.sep)
    for part in parts:
        if part in EXCLUDE_PATTERNS or (part.startswith(".") and part != ".env.example"):
            if part not in (".hermes", "."):
                return True
        if part == "node_modules" or part == "__pycache__":
            return True
        if part.endswith(".pyc") or part.endswith(".lock") or part.endswith(".tmp"):
            return True
    return False

def sync_file_two_way(path_a, path_b):
    """
    Two-way file synchronization based on mtime and hash.
    Returns True if a copy occurred.
    """
    exists_a = os.path.isfile(path_a)
    exists_b = os.path.isfile(path_b)

    if not exists_a and not exists_b:
        return False
    if exists_a and not exists_b:
        os.makedirs(os.path.dirname(path_b), exist_ok=True)
        shutil.copy2(path_a, path_b)
        return True
    if not exists_a and exists_b:
        os.makedirs(os.path.dirname(path_a), exist_ok=True)
        shutil.copy2(path_b, path_a)
        return True

    # Both exist: check content hash
    if file_hash(path_a) == file_hash(path_b):
        return False

    # Compare modification times
    mtime_a = os.path.getmtime(path_a)
    mtime_b = os.path.getmtime(path_b)

    if mtime_a > mtime_b:
        shutil.copy2(path_a, path_b)
        return True
    elif mtime_b > mtime_a:
        shutil.copy2(path_b, path_a)
        return True

    return False

def sync_dir_two_way(dir_a, dir_b):
    """
    Recursively synchronize two directories two-way.
    """
    if not os.path.exists(dir_a) and not os.path.exists(dir_b):
        return 0

    copies = 0
    all_rel_paths = set()

    if os.path.isdir(dir_a):
        for root, _, files in os.walk(dir_a):
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), dir_a)
                if not should_exclude(rel):
                    all_rel_paths.add(rel)

    if os.path.isdir(dir_b):
        for root, _, files in os.walk(dir_b):
            for file in files:
                rel = os.path.relpath(os.path.join(root, file), dir_b)
                if not should_exclude(rel):
                    all_rel_paths.add(rel)

    for rel in all_rel_paths:
        file_a = os.path.join(dir_a, rel)
        file_b = os.path.join(dir_b, rel)
        if sync_file_two_way(file_a, file_b):
            copies += 1

    return copies

def sync_hermes_config_two_way():
    """
    Synchronizes config files between ~/.hermes and ~/Documents/hermes-server-stack/hermes-config
    """
    if not os.path.isdir(STACK_CONFIG_DIR):
        return 0

    total_synced = 0

    # Sync single files
    for item in SYNC_FILES:
        file_hermes = os.path.join(HERMES_DIR, item)
        file_stack = os.path.join(STACK_CONFIG_DIR, item)
        if sync_file_two_way(file_hermes, file_stack):
            total_synced += 1

    # Sync directories
    for item in SYNC_DIRS:
        dir_hermes = os.path.join(HERMES_DIR, item)
        dir_stack = os.path.join(STACK_CONFIG_DIR, item)
        total_synced += sync_dir_two_way(dir_hermes, dir_stack)

    return total_synced

def run_git_cmd(repo_dir, args, timeout=90):
    cmd = ["git", "-C", repo_dir] + args
    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + env.get("PATH", "")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)

def sync_repository(repo_dir, repo_label, is_stack=False, pull_only=False):
    """
    Implements the watchdog synchronization pattern on a repository:
    1. clean tracked runtime noise (.usage.json)
    2. pull --rebase --autostash origin main
    3. abort rebase safely on conflict
    4. sync hermes-config & submodules if stack repo
    5. if pull_only: return early
    6. git status --porcelain
    7. git add -A, commit, git push origin main
    """
    result = {
        "label": repo_label,
        "dir": repo_dir,
        "pull_status": "unchanged",
        "pulled_commits": 0,
        "push_status": "unchanged",
        "changed_files_count": 0,
        "error": None
    }

    if not os.path.isdir(repo_dir) or not os.path.isdir(os.path.join(repo_dir, ".git")):
        result["error"] = f"Directory {repo_dir} is not a valid git repository"
        return result

    # 1. Clean tracked runtime noise if any to prevent merge blocks
    run_git_cmd(repo_dir, ["checkout", "--", ".usage.json"])

    # 2. Get HEAD commit before pull
    head_before = None
    proc_head = run_git_cmd(repo_dir, ["rev-parse", "HEAD"])
    if proc_head.returncode == 0:
        head_before = proc_head.stdout.strip()

    # Determine branch (default to main, fallback to master)
    branch = "main"
    proc_branch = run_git_cmd(repo_dir, ["rev-parse", "--abbrev-ref", "HEAD"])
    if proc_branch.returncode == 0 and proc_branch.stdout.strip():
        branch = proc_branch.stdout.strip()

    # 3. Git pull --rebase --autostash origin <branch>
    try:
        proc_pull = run_git_cmd(repo_dir, ["pull", "--rebase", "--autostash", "origin", branch], timeout=90)
        if proc_pull.returncode != 0:
            # Rebase failed or conflict -> abort rebase immediately
            run_git_cmd(repo_dir, ["rebase", "--abort"])
            err_msg = proc_pull.stderr.strip() or proc_pull.stdout.strip()
            result["error"] = f"Pull/rebase failed, aborted safely: {err_msg}"
            return result

        # Check if HEAD changed after pull
        proc_head_after = run_git_cmd(repo_dir, ["rev-parse", "HEAD"])
        if proc_head_after.returncode == 0:
            head_after = proc_head_after.stdout.strip()
            if head_before and head_after != head_before:
                proc_log = run_git_cmd(repo_dir, ["rev-list", "--count", f"{head_before}..{head_after}"])
                pulled_count = int(proc_log.stdout.strip()) if proc_log.returncode == 0 else 1
                result["pull_status"] = "updated"
                result["pulled_commits"] = pulled_count
    except subprocess.TimeoutExpired:
        run_git_cmd(repo_dir, ["rebase", "--abort"])
        result["error"] = "Pull/rebase timed out after 90 seconds"
        return result
    except Exception as e:
        run_git_cmd(repo_dir, ["rebase", "--abort"])
        result["error"] = f"Pull exception: {e}"
        return result

    # If pull only, stop here
    if pull_only:
        return result

    # 4. If stack repo, propagate config changes between ~/.hermes and hermes-config
    if is_stack:
        try:
            sync_hermes_config_two_way()
        except Exception as e:
            result["error"] = f"Config two-way sync warning: {e}"

        # Update submodules if present
        try:
            run_git_cmd(repo_dir, ["submodule", "update", "--remote", "--merge", "skills"])
        except Exception:
            pass

    # 5. Check status porcelain
    proc_status = run_git_cmd(repo_dir, ["status", "--porcelain"])
    if proc_status.returncode != 0:
        result["error"] = f"Git status failed: {proc_status.stderr.strip()}"
        return result

    status_out = proc_status.stdout.strip()
    if not status_out:
        # Working tree clean
        return result

    # Files have changes
    changed_lines = [l for l in status_out.splitlines() if l.strip()]
    result["changed_files_count"] = len(changed_lines)

    # 6. Commit and Push
    try:
        proc_add = run_git_cmd(repo_dir, ["add", "-A"])
        if proc_add.returncode != 0:
            result["error"] = f"Git add failed: {proc_add.stderr.strip()}"
            return result

        timestamp = get_wib_timestamp()
        commit_msg = f"chore(auto-sync): update {repo_label} ({timestamp})"
        proc_commit = run_git_cmd(repo_dir, ["commit", "-m", commit_msg])
        if proc_commit.returncode != 0:
            result["error"] = f"Git commit failed: {proc_commit.stderr.strip()}"
            return result

        proc_push = run_git_cmd(repo_dir, ["push", "origin", branch], timeout=90)
        if proc_push.returncode != 0:
            result["error"] = f"Git push failed: {proc_push.stderr.strip()}"
            return result

        result["push_status"] = "pushed"
    except subprocess.TimeoutExpired:
        result["error"] = "Git push timed out after 90 seconds"
    except Exception as e:
        result["error"] = f"Push exception: {e}"

    return result

def main():
    parser = argparse.ArgumentParser(description="Hermes Local Git Synchronization Automation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose output even if clean")
    args = parser.parse_args()

    # Ensure cache directory exists for lock
    os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
    lock_fd = open(LOCK_FILE, "w")
    try:
        # Non-blocking lock to guarantee single instance execution
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (IOError, BlockingIOError):
        # Another sync instance is already running; exit silently
        sys.exit(0)

    results = []

    # 1. Sync Primary Skills repository
    if os.path.isdir(SKILLS_DIR):
        res_skills = sync_repository(SKILLS_DIR, "Skills (~/.hermes/skills)", is_stack=False)
        results.append(res_skills)

    # 2. Sync Profile Skills repositories (e.g. web-dev profile)
    if os.path.isdir(PROFILES_DIR):
        try:
            for profile_name in os.listdir(PROFILES_DIR):
                pskills = os.path.join(PROFILES_DIR, profile_name, "skills")
                if os.path.isdir(os.path.join(pskills, ".git")):
                    res_p = sync_repository(pskills, f"Profile Skills ({profile_name})", is_stack=False)
                    results.append(res_p)
        except Exception as e:
            results.append({"label": "Profiles Scanner", "dir": PROFILES_DIR, "pull_status": "unchanged", "pulled_commits": 0, "push_status": "unchanged", "changed_files_count": 0, "error": str(e)})

    # 3. Sync Hermes Server Stack repository (Agent persona, config, submodules)
    if os.path.isdir(STACK_DIR):
        res_stack = sync_repository(STACK_DIR, "Server Stack (hermes-server-stack)", is_stack=True)
        results.append(res_stack)

    # 4. Pull updates for Hermes Agent Core upstream repository
    if os.path.isdir(AGENT_DIR):
        res_agent = sync_repository(AGENT_DIR, "Hermes Agent Core (~/.hermes/hermes-agent)", is_stack=False, pull_only=True)
        results.append(res_agent)

    # Release lock
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
    except Exception:
        pass

    # Check if there is any activity or error
    has_activity = any(r["pull_status"] == "updated" or r["push_status"] == "pushed" for r in results)
    has_error = any(bool(r["error"]) for r in results)

    # Zero-noise invariant: If no activity, no error, and not verbose, remain completely silent
    if not has_activity and not has_error and not args.verbose:
        sys.exit(0)

    # Format output log
    ts = get_wib_timestamp()
    lines = [f"[{ts}] Hermes Comprehensive Auto-Sync:"]
    for r in results:
        lines.append(f"  • {r['label']}:")
        if r["pull_status"] == "updated":
            lines.append(f"    - Pull: Pulled {r['pulled_commits']} new commit(s) from remote")
        else:
            lines.append("    - Pull: Up to date")

        if r["push_status"] == "pushed":
            lines.append(f"    - Push: Committed & pushed {r['changed_files_count']} changed file(s)")
        else:
            lines.append("    - Push: Clean (no local changes to push)")

        if r["error"]:
            lines.append(f"    - Status/Error: {r['error']}")

    print("\n".join(lines))
    if has_error:
        sys.exit(1)

if __name__ == "__main__":
    main()
