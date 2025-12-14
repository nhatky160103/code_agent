"""Lightweight helper for creating GitHub pull requests via REST API."""
from __future__ import annotations

import os
from typing import Optional

import requests
import time


class GitHubAPIError(RuntimeError):
    """Raised when the GitHub REST API returns a non-success response."""


def create_pr_via_api(
    title: str,
    body: str,
    head: str,
    base: str = "main",
    token: Optional[str] = None,
    repo: Optional[str] = None,
) -> str:
    """Create a pull request using the GitHub REST API, retry nếu network lỗi/5xx."""
    token = token or os.getenv("GITHUB_TOKEN")
    repo = repo or os.getenv("GITHUB_REPO")
    if not token:
        raise GitHubAPIError("GITHUB_TOKEN is not set.")
    if not repo:
        raise GitHubAPIError("GITHUB_REPO is not set (expected owner/repo).")
    retries = 0
    last_exc = None
    while retries < 3:
        try:
            response = requests.post(
                f"https://api.github.com/repos/{repo}/pulls",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                },
                timeout=30,
            )
            if response.status_code == 201:
                data = response.json()
                return data.get("html_url", "")
            # Retry với các lỗi 5xx hoặc lỗi network
            if response.status_code >= 500 or response.status_code in (429,):
                raise RuntimeError(f"Server/network error {response.status_code}: {response.text}")
            # Lỗi khác (4xx cứng): break luôn
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(2)
            retries += 1
    # Nếu vẫn fail
    if last_exc:
        raise GitHubAPIError(f"Failed to create PR after retries: {last_exc}")
    raise GitHubAPIError(f"Failed to create PR ({response.status_code}): {response.text}")


def create_repo_for_current_user(
    name: str,
    private: bool = True,
    description: str = "",
    token: Optional[str] = None,
) -> str:
    """Create a GitHub repository, retry nếu lỗi network/5xx."""
    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubAPIError("GITHUB_TOKEN is not set; cannot create GitHub repo.")
    retries = 0
    last_exc = None
    while retries < 3:
        try:
            response = requests.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "name": name,
                    "private": private,
                    "description": description,
                },
                timeout=30,
            )
            if response.status_code in (201, 202):
                data = response.json()
                full_name = data.get("full_name")
                if not full_name:
                    raise GitHubAPIError("GitHub API did not return full_name for created repo.")
                return full_name
            # Nếu repo đã tồn tại (422) --> vẫn như cũ
            if response.status_code == 422:
                error_data = response.json()
                if "name already exists" in str(error_data).lower():
                    user_response = requests.get(
                        "https://api.github.com/user",
                        headers={
                            "Authorization": f"token {token}",
                            "Accept": "application/vnd.github.v3+json",
                        },
                        timeout=10,
                    )
                    if user_response.status_code == 200:
                        username = user_response.json().get("login")
                        if username:
                            full_name = f"{username}/{name}"
                            print(f"Repository '{name}' already exists. Using existing repo: {full_name}")
                            return full_name
            # Retry network lỗi/5xx
            if response.status_code >= 500 or response.status_code in (429,):
                raise RuntimeError(f"Server/network error {response.status_code}: {response.text}")
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(2)
            retries += 1
    if last_exc:
        raise GitHubAPIError(f"Failed to create repo after retries: {last_exc}")
    raise GitHubAPIError(f"Failed to create repo ({response.status_code}): {response.text}")



