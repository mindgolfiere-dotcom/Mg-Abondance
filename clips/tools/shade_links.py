#!/usr/bin/env python3
"""List the files of a public Shade share and print signed SOURCE download links (valid 24 h).

Usage:
  python3 -I clips/tools/shade_links.py <publish_url_or_share_id> [--filter TEXT ...] [--all] [--out links.md]

No credentials are needed: the share is public, Shade's API only wants the share id and browser-like headers.
Links are presigned for 24 h; re-run the script to get fresh ones. Big files: use curl -C - / aria2c -c to resume.
"""
import argparse, json, re, sys, urllib.request

API = "https://api.shade.inc"


def req(method, path, body=None, share=""):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method, headers={
        "Origin": "https://app.shade.inc",
        "Referer": f"https://app.shade.inc/publish/{share}/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.load(resp)


def human(n):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("share")
    ap.add_argument("--filter", nargs="*", default=[], help="only files whose name contains one of these (case-insensitive)")
    ap.add_argument("--all", action="store_true", help="every file of the share")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", a.share)
    if not m:
        sys.exit("share id not found in argument")
    share = m.group(1)
    info = req("GET", f"/workspaces/shares/{share}", share=share)
    drive = info.get("drive_id") or info.get("share", {}).get("drive_id")
    if not drive:
        # fall back: search the info blob for a drive id
        mm = re.search(r'"drive_id":\s*"([0-9a-f-]{36})"', json.dumps(info))
        drive = mm.group(1) if mm else None
    if not drive:
        sys.exit("drive_id not found in share info")
    files = req("POST", f"/search/files?share_id={share}", {"path": "/", "drive_id": drive, "query": "", "limit": -1, "recursive": True, "share_id": share}, share=share)
    items = files if isinstance(files, list) else files.get("results") or files.get("files") or files.get("items") or []
    rows = []
    for it in items:
        name = it.get("name") or it.get("path", "").split("/")[-1]
        if it.get("type") in ("FOLDER", "folder") or it.get("is_folder") or not it.get("id"):
            continue
        if not a.all and a.filter and not any(f.lower() in name.lower() for f in a.filter):
            continue
        if not a.all and not a.filter and not re.search(r"\.(mp4|mov|mkv|mxf|m4v|wav|aif|aiff|mp3)$", name, re.I):
            continue
        rows.append((name, it["id"], int(it.get("size_bytes") or it.get("size") or 0)))
    rows.sort(key=lambda r: r[0].lower())
    out = [f"# Liens de téléchargement — share Shade {share}", "", "Liens signés valables 24 h (régénérer avec clips/tools/shade_links.py).", "", "| Fichier | Taille | Lien |", "|---|---|---|"]
    cmds = []
    for name, aid, size in rows:
        try:
            url = req("GET", f"/assets/{aid}/download?drive_id={drive}&share_id={share}&origin_type=SOURCE", share=share)
        except Exception as e:  # noqa: BLE001
            url = f"ERREUR {e}"
        if isinstance(url, str) and url.startswith("http"):
            out.append(f"| {name} | {human(size)} | [télécharger]({url}) |")
            cmds.append(f"curl -L -C - -o \"{name}\" \"{url}\"")
        else:
            out.append(f"| {name} | {human(size)} | {url} |")
    out += ["", "## Téléchargement en ligne de commande (reprise possible avec -C -)", "", "```bash"] + cmds + ["```", ""]
    text = "\n".join(out)
    if a.out:
        open(a.out, "w").write(text)
        print(f"{len(rows)} fichiers -> {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
