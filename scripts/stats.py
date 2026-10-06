"""Generate a self-hosted neon stats card (dist/stats.svg) from public GitHub data."""
import html
import json
import os
import urllib.request

USER = "Zlarien"
QUERY = """query($login:String!){user(login:$login){
  followers{totalCount}
  contributionsCollection{contributionCalendar{totalContributions}}
  repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100){
    totalCount nodes{stargazerCount languages(first:6,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req))["data"]["user"]


def build(u):
    repos = u["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])
    sizes = {}
    for n in repos["nodes"]:
        for e in n["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    total = sum(sizes.values()) or 1
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:5]
    nums = [
        ("Contributions (1 year)", u["contributionsCollection"]["contributionCalendar"]["totalContributions"]),
        ("Public repositories", repos["totalCount"]),
        ("Stars", stars),
        ("Followers", u["followers"]["totalCount"]),
    ]
    colors = ["#E8FF3A", "#5FBF8F", "#2E8B6E", "#9fb3c8", "#ffffff"]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260" role="img" aria-label="GitHub stats">',
        '<style>.n{fill:#E8FF3A}.k{fill:#9fb3c8}'
        ".b{transform-box:fill-box;transform-origin:left;animation:g 1.6s ease-out both}@keyframes g{from{transform:scaleX(0)}}"
        ".f{animation:u .8s ease-out both}@keyframes u{from{opacity:0;transform:translateY(10px)}}</style>",
        '<rect width="1200" height="260" rx="18" fill="#14213D" stroke="#1F6F5C" stroke-width="2"/>',
    ]
    for i, (k, v) in enumerate(nums):
        x = 60 + i * 270
        out.append(
            f'<g class="f" style="animation-delay:{i * 0.15}s"><text class="n" x="{x}" y="90" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="44" font-weight="800">{v}</text>'
            f'<text class="k" x="{x}" y="120" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="17">{html.escape(k)}</text></g>'
        )
    x = 60
    for i, (name, size) in enumerate(top):
        w = max(4, int(1080 * size / total))
        out.append(f'<rect class="b" style="animation-delay:{0.3 + i * 0.12}s" x="{x}" y="160" width="{w}" height="18" fill="{colors[i]}"/>')
        out.append(f'<text class="k" x="{60 + i * 216}" y="215" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="17"><tspan fill="{colors[i]}">●</tspan> {html.escape(name)} {100 * size / total:.0f}%</text>')
        x += w
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    os.makedirs("dist", exist_ok=True)
    with open("dist/stats.svg", "w", encoding="utf-8") as f:
        f.write(build(fetch()))
