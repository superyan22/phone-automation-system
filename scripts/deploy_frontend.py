#!/usr/bin/env python3
"""Deploy frontend build to GitHub Pages via API."""
import os
import sys
import json
import base64
import subprocess
import requests
from pathlib import Path

def get_github_token():
    """Get GitHub token from various sources."""
    # Try environment variables
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    
    # Try git credential-store
    try:
        result = subprocess.run(
            ["git", "credential-store", "get"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True,
            text=True
        )
        for line in result.stdout.split("\n"):
            if line.startswith("password="):
                return line.split("=", 1)[1]
    except:
        pass
    
    return None

def main():
    token = get_github_token()
    if not token:
        print("ERROR: No GitHub token found")
        sys.exit(1)
    
    print(f"Token found, length: {len(token)}")
    
    repo = "superyan22/phone-automation-system"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Get current gh-pages ref
    r = requests.get(f"https://api.github.com/repos/{repo}/git/refs/heads/gh-pages", headers=headers)
    if r.status_code == 200:
        base_sha = r.json()["object"]["sha"]
        print(f"Current SHA: {base_sha[:12]}")
    else:
        print(f"Error getting ref: {r.status_code}")
        sys.exit(1)
    
    # 2. Create blobs for all files
    build_dir = Path("/home/yan/phone-automation-system/frontend/build")
    tree_items = []
    
    for file_path in sorted(build_dir.rglob("*")):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(build_dir))
            with open(file_path, "rb") as f:
                content = f.read()
            
            blob_data = {
                "content": base64.b64encode(content).decode("utf-8"),
                "encoding": "base64"
            }
            r = requests.post(f"https://api.github.com/repos/{repo}/git/blobs", 
                             headers=headers, json=blob_data)
            if r.status_code == 201:
                tree_items.append({
                    "path": rel_path,
                    "mode": "100644",
                    "type": "blob",
                    "sha": r.json()["sha"]
                })
    
    print(f"Created {len(tree_items)} blobs")
    
    # 3. Create tree
    r = requests.post(f"https://api.github.com/repos/{repo}/git/trees", 
                     headers=headers, json={"tree": tree_items})
    if r.status_code != 201:
        print(f"Tree error: {r.status_code}")
        sys.exit(1)
    tree_sha = r.json()["sha"]
    
    # 4. Create commit
    r = requests.post(f"https://api.github.com/repos/{repo}/git/commits", 
                     headers=headers, 
                     json={"message": "deploy: frontend with public API", "tree": tree_sha, "parents": [base_sha]})
    if r.status_code != 201:
        print(f"Commit error: {r.status_code}")
        sys.exit(1)
    new_sha = r.json()["sha"]
    
    # 5. Update ref
    r = requests.patch(f"https://api.github.com/repos/{repo}/git/refs/heads/gh-pages", 
                      headers=headers, json={"sha": new_sha, "force": True})
    if r.status_code == 200:
        print("✅ Deployed successfully!")
        print(f"URL: https://superyan22.github.io/phone-automation-system/")
    else:
        print(f"Ref error: {r.status_code}")
        sys.exit(1)

if __name__ == "__main__":
    main()
