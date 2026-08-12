"""
Validates Pages.json.

Unlike the other store files, Pages.json does not point at whole repositories but
at single .scpage files inside them, each pinned to its own commit. Next to every
.scpage there has to be a manifest with the same name, so the store can show the
page without downloading it.

Run from the repository root:

    python3 scripts/validate_pages.py

Exits non-zero if anything is wrong.
"""
import json
import re
import sys
import urllib.error
import urllib.request

PAGES_FILE = "Pages.json"
PAGE_EXTENSION = ".scpage"
MANIFEST_SUFFIX = ".manifest.json"

REPO_PATTERN = re.compile(r"^https://github\.com/[^/\s]+/[^/\s]+$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")

TIMEOUT = 15
USER_AGENT = "StreamController-Store-Validator"


def build_raw_url(repo_url: str, path: str, commit: str) -> str:
    repo_url = repo_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
    return f"{repo_url}/{commit}/{path}"


def fetch(url: str) -> bytes | None:
    """Returns the content of the url, None if it does not exist."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach {url}: {e.reason}") from e


def manifest_path_for(page_path: str) -> str:
    return page_path[:-len(PAGE_EXTENSION)] + MANIFEST_SUFFIX


def validate_page(repo_url: str, page: dict, errors: list, seen_ids: dict, seen_paths: dict) -> None:
    path = page.get("path")
    commit = page.get("commit")
    where = f"{repo_url} -> {path}"

    if not isinstance(path, str) or not path.endswith(PAGE_EXTENSION):
        errors.append(f"{repo_url}: 'path' has to be a {PAGE_EXTENSION} file, got {path!r}")
        return
    if path.startswith("/") or ".." in path.split("/"):
        errors.append(f"{where}: 'path' has to be relative to the repository root")
        return
    if not isinstance(commit, str) or not COMMIT_PATTERN.match(commit):
        errors.append(f"{where}: 'commit' has to be a full 40 character commit hash, got {commit!r}")
        return

    if (repo_url, path) in seen_paths:
        errors.append(f"{where}: listed more than once")
        return
    seen_paths[(repo_url, path)] = True

    if fetch(build_raw_url(repo_url, path, commit)) is None:
        errors.append(f"{where}: does not exist at commit {commit}")

    manifest_url = build_raw_url(repo_url, manifest_path_for(path), commit)
    manifest_content = fetch(manifest_url)
    if manifest_content is None:
        errors.append(f"{where}: is missing its {manifest_path_for(path)} at commit {commit}")
        return

    try:
        manifest = json.loads(manifest_content)
    except json.JSONDecodeError as e:
        errors.append(f"{where}: manifest is not valid JSON ({e})")
        return

    if not isinstance(manifest, dict):
        errors.append(f"{where}: manifest has to be an object")
        return

    for key in ("id", "name"):
        if not manifest.get(key):
            errors.append(f"{where}: manifest is missing '{key}'")

    page_id = manifest.get("id")
    if isinstance(page_id, str) and page_id:
        if page_id in seen_ids:
            errors.append(f"{where}: id '{page_id}' is already used by {seen_ids[page_id]}")
        else:
            seen_ids[page_id] = where


def validate(json_path: str = PAGES_FILE) -> list:
    with open(json_path) as f:
        data = json.load(f)

    errors = []
    if not isinstance(data, list):
        return [f"{json_path} has to contain a list"]

    seen_ids: dict = {}
    seen_paths: dict = {}

    for entry in data:
        if not isinstance(entry, dict):
            errors.append(f"{entry!r} is not an object")
            continue

        repo_url = entry.get("url")
        if not isinstance(repo_url, str) or not REPO_PATTERN.match(repo_url):
            errors.append(f"{repo_url!r} is not a https://github.com/<owner>/<repo> url")
            continue

        pages = entry.get("pages")
        if not isinstance(pages, list) or not pages:
            errors.append(f"{repo_url}: 'pages' has to be a non empty list")
            continue

        for page in pages:
            if not isinstance(page, dict):
                errors.append(f"{repo_url}: {page!r} is not an object")
                continue
            validate_page(repo_url, page, errors, seen_ids, seen_paths)

    return errors


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else PAGES_FILE

    try:
        found = validate(path)
    except RuntimeError as e:
        print(e)
        sys.exit(2)

    if found:
        print(f"{path} is not valid:")
        for error in found:
            print(f"  - {error}")
        sys.exit(1)

    print(f"{path} is valid")
