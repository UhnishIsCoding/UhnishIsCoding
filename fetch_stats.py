#!/usr/bin/env python3
"""
fetch_stats.py — Fetches GitHub stats and prints them as JSON.
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from urllib import request as urlreq
from urllib import error as urlerr

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
TIMEOUT = 10
MAX_RETRIES = 3


def log(msg):
    print(f"[fetch_stats] {msg}", file=sys.stderr)


def request(url, token=None, json_body=None):
    """GET (or POST if json_body given) with retry + rate-limit handling."""
    headers = {
        "User-Agent": "gh-stats-fetcher",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(json_body).encode() if json_body is not None else None
    req = urlreq.Request(url, data=data, headers=headers, method="POST" if data else "GET")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlreq.urlopen(req, timeout=TIMEOUT) as resp:
                remaining = resp.headers.get("X-RateLimit-Remaining")
                reset = resp.headers.get("X-RateLimit-Reset")
                if remaining is not None and int(remaining) < 2:
                    wait = max(0, int(reset) - int(time.time())) if reset else 5
                    log(f"rate limit nearly exhausted, sleeping {wait}s")
                    time.sleep(min(wait, 30))
                return json.loads(resp.read().decode())
        except urlerr.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in (403, 429):
                reset = e.headers.get("X-RateLimit-Reset") if e.headers else None
                wait = max(0, int(reset) - int(time.time())) if reset else 2 ** attempt
                log(f"rate limited (HTTP {e.code}), sleeping {min(wait, 30)}s "
                    f"(attempt {attempt}/{MAX_RETRIES})")
                time.sleep(min(wait, 30))
            else:
                log(f"HTTP {e.code} on {url} (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(2 ** attempt)
        except urlerr.URLError as e:
            log(f"network error on {url}: {e} (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(2 ** attempt)
    log(f"giving up on {url}")
    return None


def fetch_user(username, token):
    return request(f"{API}/users/{username}", token=token)


def fetch_all_repos(username, token):
    repos, page = [], 1
    while page <= 5:
        chunk = request(f"{API}/users/{username}/repos?per_page=100&page={page}", token=token)
        if not chunk:
            break
        repos.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return repos


def fetch_contributions(username, token):
    """Requires a token; returns None (not 0) if unavailable so callers can distinguish."""
    if not token:
        return None
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection { contributionCalendar { totalContributions } }
      }
    }"""
    result = request(GRAPHQL, token=token, json_body={"query": query, "variables": {"login": username}})
    if not result or not result.get("data") or not result["data"].get("user"):
        return None
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]


def top_languages(repos, limit=5):
    counts = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    total = sum(counts.values()) or 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [[lang, round(100 * n / total, 1)] for lang, n in ranked]


def gather(username, token):
    user = fetch_user(username, token)
    repos = fetch_all_repos(username, token)
    contributions = fetch_contributions(username, token)

    return {
        "username": username,
        "name": (user or {}).get("name"),
        "stars": sum(r.get("stargazers_count", 0) for r in repos) if repos else None,
        "followers": (user or {}).get("followers"),
        "repos": (user or {}).get("public_repos", len(repos) if repos else None),
        "contributions": contributions,
        "top_languages": top_languages(repos) if repos else [],
        "fetched_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub stats as JSON")
    parser.add_argument("--username", default=os.environ.get("GH_USERNAME"))
    parser.add_argument("--output", default=None, help="write JSON to file instead of stdout")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        log("warning: no GH_TOKEN/GITHUB_TOKEN set — lower rate limit, contributions unavailable")

    if not args.username:
        log("error: --username or GH_USERNAME is required")
        sys.exit(1)

    data = gather(args.username, token)
    output = json.dumps(data, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        log(f"wrote {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()