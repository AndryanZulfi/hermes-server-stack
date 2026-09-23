#!/usr/bin/env python3
"""
Automated Git Backup for Server Projects & Skills
Synchronizes and pushes changes to GitHub for:
1. hermes-skills (/opt/data/skills)
2. graph-view / galaxy-view (/opt/data/galaxy-view)
3. hermes-server-stack (/home/zulfi/Projects via alpine/git)

Can be executed:
- On schedule via Hermes cron job (e.g. 02:00 WIB daily)
- Manually on-demand: python3 backup_projects_git.py
- Continuous watcher mode: python3 backup_projects_git.py --watch
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone, timedelta
import argparse

WIB = timezone(timedelta(hours=7))

SKILLS_DIR = "/opt/data/skills"
GALAXY_DIR = "/opt/data/galaxy-view"
HOST_PROJECTS_DIR = "/home/zulfi/Projects"

def get_wib_now_str():
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")

def get_git_status_porcelain(repo_dir):
    try:
        res = subprocess.run(
            ["git", "-C", repo_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def backup_local_repo(repo_dir, repo_name, branch="main"):
    if not os.path.isdir(repo_dir) or not os.path.isdir(os.path.join(repo_dir, ".git")):
        return None

    status = get_git_status_porcelain(repo_dir)
    if not status:
        return None

    changed_files = [line.strip().split()[-1] for line in status.splitlines() if line.strip()]
    count = len(changed_files)
    sample = ", ".join(changed_files[:3])
    if count > 3:
        sample += f" (+{count - 3} lainnya)"

    now_str = get_wib_now_str()
    commit_msg = f"chore({repo_name}): auto-backup ({now_str})\n\nUpdated files ({count}):\n" + "\n".join(f"- {f}" for f in changed_files[:20])
    if count > 20:
        commit_msg += f"\n- ... and {count - 20} more files"

    try:
        subprocess.run(["git", "-C", repo_dir, "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_dir, "commit", "-m", commit_msg], check=True, capture_output=True)
        subprocess.run(["git", "-C", repo_dir, "push", "origin", branch], check=True, capture_output=True)
        return {
            "name": repo_name,
            "status": "pushed",
            "count": count,
            "sample": sample
        }
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        return {
            "name": repo_name,
            "status": "error",
            "error": err_msg or str(e)
        }

def sync_hermes_config_to_host():
    """Sync live seed configuration files from /opt/data into host hermes-config directory."""
    sync_script = """
set -e
mkdir -p /host_p/hermes-config/memories
mkdir -p /host_p/hermes-config/cron
mkdir -p /host_p/hermes-config/plugins
mkdir -p /host_p/hermes-config/scripts

# Sync memory & persona files
cp -f /host_p/9router-hermes/hermes-data/memories/MEMORY.md /host_p/hermes-config/memories/ 2>/dev/null || true
cp -f /host_p/9router-hermes/hermes-data/memories/USER.md /host_p/hermes-config/memories/ 2>/dev/null || true
cp -f /host_p/9router-hermes/hermes-data/user.md /host_p/hermes-config/ 2>/dev/null || true
cp -f /host_p/9router-hermes/hermes-data/SOUL.md /host_p/hermes-config/ 2>/dev/null || true
cp -f /host_p/9router-hermes/hermes-data/cron/jobs.json /host_p/hermes-config/cron/ 2>/dev/null || true

# Sync plugins and scripts (excluding node_modules / caches)
if [ -d /host_p/9router-hermes/hermes-data/plugins ]; then
  cp -rf /host_p/9router-hermes/hermes-data/plugins/* /host_p/hermes-config/plugins/ 2>/dev/null || true
fi
if [ -d /host_p/9router-hermes/hermes-data/scripts ]; then
  cp -rf /host_p/9router-hermes/hermes-data/scripts/* /host_p/hermes-config/scripts/ 2>/dev/null || true
  rm -rf /host_p/hermes-config/scripts/whatsapp-bridge/node_modules 2>/dev/null || true
fi

# Sync daily reflections
mkdir -p /host_p/hermes-config/refleksi
if [ -d /host_p/9router-hermes/hermes-data/refleksi ]; then
  cp -rf /host_p/9router-hermes/hermes-data/refleksi/* /host_p/hermes-config/refleksi/ 2>/dev/null || true
fi
"""
    try:
        subprocess.run(
            ["docker", "run", "--rm", "-v", f"{HOST_PROJECTS_DIR}:/host_p", "alpine", "sh", "-c", sync_script],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def backup_host_server_stack():
    """Sync seed templates and commit/push hermes-server-stack repo via alpine/git."""
    sync_hermes_config_to_host()

    now_str = get_wib_now_str()
    git_run_cmd = f"""
set -e
cd /host_p
git config --global --add safe.directory /host_p
git config credential.helper "store --file=/host_p/9router-hermes/hermes-data/home/.git-credentials"

# Check status
STATUS=$(git status --porcelain)
if [ -z "$STATUS" ]; then
    echo "NO_CHANGES"
    exit 0
fi

# Stage and commit
git add -A
git commit -m "chore(stack): auto-backup server infrastructure & seed configs ({now_str})"
git push origin main
echo "PUSHED_OK"
"""

    try:
        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--entrypoint", "/bin/sh",
                "-v", f"{HOST_PROJECTS_DIR}:/host_p",
                "alpine/git",
                "-c", git_run_cmd
            ],
            capture_output=True,
            text=True,
            check=True
        )
        out = proc.stdout.strip()
        if "PUSHED_OK" in out:
            return {
                "name": "hermes-server-stack",
                "status": "pushed",
                "count": "configs/stack",
                "sample": "hermes-config & server stack"
            }
        return None
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() if e.stderr else str(e)
        return {
            "name": "hermes-server-stack",
            "status": "error",
            "error": err
        }

def run_backup_cycle(verbose=False):
    results = []

    # 1. Skills repo
    res_skills = backup_local_repo(SKILLS_DIR, "hermes-skills")
    if res_skills:
        results.append(res_skills)

    # 2. Galaxy View repo
    res_galaxy = backup_local_repo(GALAXY_DIR, "graph-view")
    if res_galaxy:
        results.append(res_galaxy)

    # 3. Host Server Stack repo
    res_stack = backup_host_server_stack()
    if res_stack:
        results.append(res_stack)

    # If changes were pushed, format notification message
    pushed = [r for r in results if r.get("status") == "pushed"]
    errors = [r for r in results if r.get("status") == "error"]

    if pushed or errors:
        lines = [f"📦 *Laporan Backup Otomatis GitHub* ({get_wib_now_str()})"]
        if pushed:
            lines.append("✅ *Perubahan berhasil di-commit & di-push ke GitHub:*")
            for item in pushed:
                lines.append(f"• *{item['name']}*: {item['count']} perubahan ({item['sample']})")
        if errors:
            lines.append("\n⚠️ *Peringatan error pada:*")
            for item in errors:
                lines.append(f"• *{item['name']}*: {item['error']}")
        
        message = "\n".join(lines)
        print(message)
        return True
    else:
        if verbose:
            print(f"[{get_wib_now_str()}] Semua repositori bersih, tidak ada perubahan yang perlu di-backup.")
        return False

def watch_mode(interval_seconds=60, debounce_seconds=30):
    print(f"🚀 Memulai Git Backup Watcher Daemon (Interval: {interval_seconds}s, Debounce: {debounce_seconds}s)...")
    
    def check_has_changes():
        skills_st = get_git_status_porcelain(SKILLS_DIR) or ""
        galaxy_st = get_git_status_porcelain(GALAXY_DIR) or ""
        return bool(skills_st or galaxy_st)

    while True:
        try:
            if check_has_changes():
                print(f"[{get_wib_now_str()}] Perubahan terdeteksi. Menunggu debounce {debounce_seconds}s agar stabil...")
                time.sleep(debounce_seconds)
                run_backup_cycle(verbose=True)
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("Watcher dihentikan.")
            break
        except Exception as e:
            print(f"Error watcher: {e}")
            time.sleep(interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="Git Auto-Backup Script for Hermes Server & Skills")
    parser.add_argument("--watch", action="store_true", help="Jalankan sebagai watcher daemon real-time")
    parser.add_argument("--verbose", "-v", action="store_true", help="Tampilkan log meskipun tidak ada perubahan")
    args = parser.parse_args()

    if args.watch:
        watch_mode()
    else:
        run_backup_cycle(verbose=args.verbose)

if __name__ == "__main__":
    main()
