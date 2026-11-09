import json, os, re, sys, urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lines as LN

ROOT = Path(__file__).resolve().parents[1]
CARDS = [ROOT / "assets" / "card-dark.svg", ROOT / "assets" / "card-light.svg"]
LOGIN = os.environ.get("GH_LOGIN", "CoOwner")
TOKEN = os.environ.get("GH_TOKEN", "")

REPOS = """query($login: String!, $after: String) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, first: 100, after: $after) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount isPrivate }
    }
  }
}"""
COMMITS = """query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) { contributionsCollection(from: $from, to: $to) { totalCommitContributions } }
}"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def fetch():
    stars = public = 0
    after = None
    while True:
        u = gql(REPOS, {"login": LOGIN, "after": after})["user"]
        repos = u["repositories"]
        for n in repos["nodes"]:
            stars += n["stargazerCount"]
            public += 0 if n["isPrivate"] else 1
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    now = datetime.now(timezone.utc)
    t = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    commits = 0
    while t < now:
        t1 = min(now, t.replace(year=t.year + 1))
        cc = gql(COMMITS, {"login": LOGIN, "from": t.isoformat(), "to": t1.isoformat()})["user"]["contributionsCollection"]
        commits += cc["totalCommitContributions"]
        t = t1
    return {"repos": repos["totalCount"], "public": public, "stars": stars, "commits": commits, "followers": u["followers"]["totalCount"]}


def put(svg, tid, inner):
    pat = re.compile(r'(<text\b[^>]*\bid="' + tid + r'"[^>]*>)(.*?)(</text>)', re.S)
    if not pat.search(svg):
        raise SystemExit(f"{tid} not found")
    return pat.sub(lambda m: m.group(1) + inner + m.group(3), svg, count=1)


def main():
    today = datetime.now(ZoneInfo("America/New_York")).date()
    stats = None
    if TOKEN:
        try:
            stats = fetch()
            print("stats", stats)
        except Exception as e:
            print("api failed:", e)
    for card in CARDS:
        svg = card.read_text()
        svg = put(svg, "uptime", LN.uptime_spans(LN.uptime(today)))
        if stats:
            sub = "all public" if stats["public"] == stats["repos"] else f"{LN.num(stats['public'])} public"
            svg = put(svg, "stat-repos", escape(LN.num(stats["repos"])))
            svg = put(svg, "stat-public", escape(sub))
            svg = put(svg, "stat-stars", escape(LN.num(stats["stars"])))
            svg = put(svg, "stat-commits", escape(LN.num(stats["commits"])))
            svg = put(svg, "stat-followers", escape(LN.num(stats["followers"])))
        card.write_text(svg)
    print("updated", today)


if __name__ == "__main__":
    main()
