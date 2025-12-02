"""Lightweight helper for creating GitHub pull requests via REST API."""
from __future__ import annotations

import os
from typing import Optional

import requests


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
    """
    Create a pull request using the GitHub REST API.

    Args:
        title: PR title shown on GitHub.
        body: Markdown body/description of the PR.
        head: Source branch name (must already exist on the remote).
        base: Target branch name, usually "main" or "master".
        token: Personal access token (defaults to GITHUB_TOKEN env var).
        repo: Repository in "owner/name" format (defaults to GITHUB_REPO env).

    Returns:
        The HTML URL of the created pull request.
    """
    token = token or os.getenv("GITHUB_TOKEN")
    repo = repo or os.getenv("GITHUB_REPO")

    if not token:
        raise GitHubAPIError("GITHUB_TOKEN is not set.")
    if not repo:
        raise GitHubAPIError("GITHUB_REPO is not set (expected owner/repo).")

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

    if response.status_code != 201:
        raise GitHubAPIError(
            f"Failed to create PR ({response.status_code}): {response.text}"
        )

    data = response.json()
    return data.get("html_url", "")


