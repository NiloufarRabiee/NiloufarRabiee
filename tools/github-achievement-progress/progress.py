#!/usr/bin/env python3
"""GitHub public achievement progress, prepared for Niloufar Rabiee.

Reads public GitHub API data only. Does not edit repositories, create
engagement, or claim that GitHub has granted an achievement.
"""

import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
STAR_MILESTONES = (16, 128, 512, 4096)
PULL_MILESTONES = (2, 16, 128, 1024)


def api_get(path, query=None, token=None):
    url = API_ROOT + path
    if query:
        url += "?" + urlencode(query)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-achievement-progress",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, headers=headers)
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def next_milestone(current, milestones):
    for target in milestones:
        if current < target:
            return {"target": target, "remaining": target - current}
    return None


def public_repositories(username, token=None):
    repos = []
    for page in range(1, 101):
        batch = api_get(
            "/users/" + quote(username, safe="") + "/repos",
            {"type": "owner", "per_page": 100, "page": page},
            token,
        )
        repos.extend(repo for repo in batch if repo.get("owner", {}).get("login", "").lower() == username.lower()
                     and not repo.get("fork", False))
        if len(batch) < 100:
            break
    return repos


def public_merged_pull_requests(username, token=None):
    data = api_get(
        "/search/issues",
        {"q": f"is:pr is:merged author:{username}", "per_page": 1},
        token,
    )
    return int(data.get("total_count", 0))


def report(username, token=None):
    repos = public_repositories(username, token)
    repos_by_stars = sorted(
        ({"name": repo["full_name"], "stars": int(repo.get("stargazers_count", 0))}
         for repo in repos),
        key=lambda repo: (-repo["stars"], repo["name"]),
    )
    best = repos_by_stars[0] if repos_by_stars else None
    merged = public_merged_pull_requests(username, token)
    return {
        "user": username,
        "scope": "Public data only; private repository PRs are excluded",
        "top_repository": best,
        "starstruck_next_milestone": next_milestone(best["stars"] if best else 0, STAR_MILESTONES),
        "public_merged_pull_requests": merged,
        "pull_shark_public_only_next_milestone": next_milestone(merged, PULL_MILESTONES),
        "public_repositories_ranked_by_stars": repos_by_stars,
        "note": "These are unofficial milestone estimates, not confirmation of awarded badges.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username", help="GitHub username to inspect")
    args = parser.parse_args()
    try:
        data = report(args.username, os.environ.get("GITHUB_TOKEN"))
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
        parser.exit(1, f"GitHub API request failed: {exc}\n")
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
