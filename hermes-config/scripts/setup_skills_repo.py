#!/usr/bin/env python3
"""
Setup and Push Hermes Skills to Private GitHub Repository
Author: Hermes Agent for Andryan Zulfi
"""

import os
import re
import sys
import json
import sqlite3
import subprocess
import urllib.request
import urllib.error

DB_PATH = "/opt/data/state.db"
SKILLS_DIR = "/opt/data/skills"
ENV_FILE = "/opt/data/.env"
REPO_NAME = "hermes-skills"
GITHUB_USER = "AndryanZulfi"

def get_token():
    if os.path.exists("/opt/data/.github_token_secure"):
        with open("/opt/data/.github_token_secure", "r") as f:
            t = f.read().strip()
            if t.startswith("ghp_"):
                return t
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN=") or line.startswith("GITHUB_PAT="):
                    t = line.split("=", 1)[1].strip()
                    if t.startswith("ghp_"):
                        return t
    print("Error: GitHub token not found")
    sys.exit(1)

def save_token_to_env(token):
    # Append or update GITHUB_TOKEN in /opt/data/.env
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN=") or line.startswith("GITHUB_PAT="):
                    lines.append(f"GITHUB_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"GITHUB_TOKEN={token}\n")
        
    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)
    os.chmod(ENV_FILE, 0o600)
    print(f"✓ GitHub token securely saved to {ENV_FILE} (mode 600)")

def create_github_repo(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Hermes-Agent-Setup"
    }
    
    # 1. Check if repo already exists
    check_url = f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}"
    req = urllib.request.Request(check_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"✓ Repository already exists: {data.get('html_url')} (private: {data.get('private')})")
            return data.get('clone_url')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass # Does not exist yet, proceed to create
        else:
            print(f"Error checking repo: HTTP {e.code} - {e.read().decode('utf-8')}")
            sys.exit(1)
            
    # 2. Create private repo
    create_url = "https://api.github.com/user/repos"
    payload = json.dumps({
        "name": REPO_NAME,
        "description": "Hermes Agent Skills Ecosystem (Decoupled Modular Skills Collection)",
        "private": True,
        "has_issues": True,
        "has_projects": False,
        "has_wiki": False
    }).encode('utf-8')
    
    create_req = urllib.request.Request(create_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(create_req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"✓ Successfully created private repository: {data.get('html_url')}")
            return data.get('clone_url')
    except urllib.error.HTTPError as e:
        print(f"Error creating repo: HTTP {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)

def setup_git_and_push(token):
    if not os.path.isdir(SKILLS_DIR):
        print(f"Error: Skills directory {SKILLS_DIR} not found")
        sys.exit(1)
        
    os.chdir(SKILLS_DIR)
    
    # 1. Create clean .gitignore
    gitignore_path = os.path.join(SKILLS_DIR, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("# Temporary and runtime state\n")
        f.write(".usage.json\n")
        f.write(".locks/\n")
        f.write(".curator*\n")
        f.write("__pycache__/\n")
        f.write("*.pyc\n")
        f.write(".DS_Store\n")
        f.write("*.tmp\n")
    print("✓ Created clean .gitignore in skills directory")
    
    # 2. Git init & configuration
    subprocess.run(["git", "init", "-b", "main"], check=True)
    subprocess.run(["git", "config", "user.name", "Andryan Zulfi"], check=True)
    subprocess.run(["git", "config", "user.email", "andryanzulfi2007@gmail.com"], check=True)
    
    # Configure git credential store
    cred_file = os.path.expanduser("~/.git-credentials")
    with open(cred_file, "w") as f:
        f.write(f"https://{token}:x-oauth-basic@github.com\n")
    os.chmod(cred_file, 0o600)
    subprocess.run(["git", "config", "credential.helper", "store"], check=True)
    print("✓ Configured Git credentials helper securely")
    
    # 3. Add and commit
    subprocess.run(["git", "add", "."], check=True)
    
    # Check if there are changes to commit
    status_proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if status_proc.stdout.strip():
        commit_msg = "feat: initial commit of hermes agent skills collection\n\n- 65 active modular skills\n- 12 categories (autonomous-ai-agents, creative, devops, productivity, etc.)\n- full protocols, knowledge references, and scripts"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("✓ Committed all active skills to Git main branch")
    else:
        print("✓ All skills are already committed in local Git")
        
    # 4. Set remote & push
    remote_url = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
    # Check existing remote
    remotes_proc = subprocess.run(["git", "remote"], capture_output=True, text=True)
    if "origin" in remotes_proc.stdout.split():
        subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)
    else:
        subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
        
    # Push to origin main
    print(f"→ Pushing to {remote_url}...")
    subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True)
    print("✓ Successfully pushed all skills to GitHub main branch!")

def main():
    print("=== Hermes Skills Repository Backup ===")
    token = get_token()
    save_token_to_env(token)
    create_github_repo(token)
    setup_git_and_push(token)
    print("\n🎉 ALL TASKS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
