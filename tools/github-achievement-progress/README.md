# GitHub Achievement Progress (public data)

A tiny, read-only Python 3 utility that uses the **GitHub REST API** to inspect public repository stars and merged pull requests. Built for **Niloufar Rabiee**; usable with any public GitHub username.

This is a real API integration in development, **not** a badge generator. It cannot grant achievements, auto-star repositories, sponsor accounts, or verify which badges GitHub has actually awarded. Its tier thresholds follow community-documented milestones and may change.

## Run

```bash
python3 tools/github-achievement-progress/progress.py NiloufarRabiee
```

No dependencies beyond the Python standard library. A token is optional for public data, but GitHub API rate limits apply. For higher limits, set `GITHUB_TOKEN` in the environment; **never commit a token**.

## What it reports

- Highest-starred public repository and the next Starstruck milestone (16 / 128 / 512 / 4,096 stars)
- Count of **publicly visible** merged PRs opened by the user and the next Pull Shark milestone (2 / 16 / 128 / 1,024 PRs)
- Public non-fork repositories sorted by stars

Private PRs can contribute to GitHub's achievement system but **are not counted here**. Likewise, accepted Discussions answers and coauthored PR attribution cannot be reliably read by this minimal utility. Treat the output as planning data, not as authoritative GitHub achievement status.

## Privacy and scope

This utility only makes GET requests to public GitHub REST API endpoints (`/users/{username}/repos` and `/search/issues`). It stores no credentials or fetched data, and makes no changes to any GitHub account or repository.
