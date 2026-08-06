#!/usr/bin/env python3
"""Validate the top-level *.json files in this repo, optionally repairing them in place.

Modes:
  (no flags)          check only, exit 1 if any file is invalid JSON
  --fix               also try to repair invalid files with json_repair; if the
                       repaired result looks sane, write it back
  --restore-fallback  when a file can't be repaired (or the repair looks unsafe,
                       e.g. it dropped most of the entries), fall back to the last
                       version of that file in git history that was valid JSON
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from json_repair import repair_json

ROOT = Path(__file__).resolve().parent.parent
JSON_FILES = sorted(ROOT.glob("*.json"))


def git_show(ref: str, rel_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def last_good_version(rel_path: str):
    """Walk commit history for this file and return (text, obj) of the newest valid revision."""
    log = subprocess.run(
        ["git", "log", "--format=%H", "--", rel_path],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.split()
    for commit in log:
        content = git_show(commit, rel_path)
        if content is None:
            continue
        try:
            return content, json.loads(content)
        except json.JSONDecodeError:
            continue
    return None


def looks_sane(repaired: object, reference: object) -> bool:
    """Guard against a 'repair' that silently throws away most of the data."""
    if type(repaired) is not type(reference):
        return False
    if isinstance(reference, (list, dict)):
        return len(repaired) >= max(1, int(len(reference) * 0.8))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--restore-fallback", action="store_true")
    args = parser.parse_args()

    changed = []
    failed = []

    for path in JSON_FILES:
        rel_path = str(path.relative_to(ROOT))
        original = path.read_text(encoding="utf-8")
        try:
            json.loads(original)
            continue  # already valid, nothing to do
        except json.JSONDecodeError as exc:
            print(f"::error file={rel_path}::invalid JSON: {exc}")

        if not args.fix:
            failed.append(rel_path)
            continue

        reference = last_good_version(rel_path)
        fixed = False
        try:
            repaired_text = repair_json(original, ensure_ascii=False)
            repaired_obj = json.loads(repaired_text)
            if reference is None or looks_sane(repaired_obj, reference[1]):
                path.write_text(
                    json.dumps(repaired_obj, indent=4, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"Repaired {rel_path}")
                changed.append(rel_path)
                fixed = True
        except Exception as exc:
            print(f"repair attempt for {rel_path} failed: {exc}")

        if not fixed:
            if args.restore_fallback and reference is not None:
                path.write_text(reference[0], encoding="utf-8")
                print(f"Restored {rel_path} to its last known-good version from git history")
                changed.append(rel_path)
            else:
                failed.append(rel_path)

    if changed:
        print("CHANGED:" + ",".join(changed))
    if failed:
        print("FAILED:" + ",".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
