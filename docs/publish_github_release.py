"""Publish the verified release using existing Git credentials, never printing them."""
import argparse
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPO = "mostrotarlo/woacc-evo-tracker"
VERSION = (ROOT / "VERSION").read_text().strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", text=True, capture_output=True, check=True)
    credential = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    token = credential.get("password")
    if not token:
        raise RuntimeError("No existing GitHub credential is available")

    def api(path, method="GET", data=None, content_type="application/json"):
        url = path if path.startswith("https://") else f"https://api.github.com/repos/{REPO}" + (f"/{path}" if path else "")
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        request = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "WOACC-Release-Publisher",
            "Content-Type": content_type})
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"GitHub returned HTTP {error.code} for {method} {urllib.parse.urlsplit(url).path}") from None

    if not args.publish:
        repository = api("")
        releases = api("releases?per_page=5")
        print(json.dumps({"repository": repository["full_name"], "can_push": repository.get("permissions", {}).get("push"), "releases": [{"tag": item["tag_name"], "draft": item["draft"], "url": item["html_url"]} for item in releases]}, indent=2))
        return

    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise RuntimeError("Commit the selected release files before publishing")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    remote_sha = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=ROOT, text=True).split()[0]
    if sha != remote_sha:
        raise RuntimeError("Release commit does not match origin/main")
    existing = api("releases?per_page=100")
    if any(item["tag_name"] == f"v{VERSION}" for item in existing):
        raise RuntimeError("Release already exists; inspect it instead of duplicating it")
    release = api("releases", "POST", {"tag_name": f"v{VERSION}", "target_commitish": sha,
        "name": f"WOACC EVO & ACC Tracker {VERSION}", "body": (ROOT / "docs" / f"RELEASE_NOTES_{VERSION}.md").read_text(encoding="utf-8"), "draft": True, "prerelease": False})
    files = [ROOT / "release" / f"WOACC_Tracker_v{VERSION}_Windows_x64.zip",
             ROOT / "release" / f"WOACC_Tracker_v{VERSION}_Windows_x64.zip.sha256",
             ROOT / "output/pdf" / f"WOACC_Tracker_{VERSION}_Manual_IT_EN_FR_ES.pdf",
             ROOT / "docs/assets/woacc-evo-acc-tracker-15.1.0.png"]
    upload = release["upload_url"].split("{", 1)[0]
    for file in files:
        item = api(upload + "?name=" + urllib.parse.quote(file.name), "POST", file.read_bytes(), "application/octet-stream")
        if item["size"] != file.stat().st_size or item["state"] != "uploaded":
            raise RuntimeError(f"Asset verification failed: {file.name}")
        print(f"Uploaded: {item['name']} ({item['size']} bytes)")
    published = api(f"releases/{release['id']}", "PATCH", {"draft": False, "make_latest": "true"})
    verified = api(f"releases/{release['id']}")
    assert not verified["draft"] and len(verified["assets"]) == len(files)
    api("", "PATCH", {"description": "WOACC EVO & ACC Tracker: unified dedicated-server results, leaderboards, Discord notifications, Bridge API and Windows service.", "homepage": "https://woacc.zapto.org/tracker/"})
    print(published["html_url"])


if __name__ == "__main__":
    main()
