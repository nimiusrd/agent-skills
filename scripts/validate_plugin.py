#!/usr/bin/env python3
"""Validate plugin.json against the Agent Plugins 1.0.0 schema."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SKILLS_DIRNAME = "skills"
SKILL_FILENAME = "SKILL.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def fetch_schema(url: str) -> object:
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def discover_skills(root: Path) -> list[str]:
    skills_dir = root / SKILLS_DIRNAME
    if not skills_dir.is_dir():
        return []

    names: list[str] = []
    for child in sorted(skills_dir.iterdir()):
        if child.is_dir() and (child / SKILL_FILENAME).is_file():
            names.append(child.name)
    return names


def validate_manifest(manifest: object, schema: object) -> list[str]:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    return [
        f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in validator.iter_errors(manifest)
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to plugin.json (default: <repo>/plugin.json)",
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=None,
        help="Local schema file instead of fetching the official schema",
    )
    parser.add_argument(
        "--schema-url",
        default=SCHEMA_URL,
        help=f"Official schema URL (default: {SCHEMA_URL})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    manifest_path = args.manifest or (root / "plugin.json")

    if not manifest_path.is_file():
        print(f"plugin.json が見つかりません: {manifest_path}", file=sys.stderr)
        return 1

    try:
        manifest = load_json(manifest_path)
        schema = (
            load_json(args.schema_file)
            if args.schema_file
            else fetch_schema(args.schema_url)
        )
    except (OSError, json.JSONDecodeError) as error:
        print(f"マニフェストまたはスキーマの読み込みに失敗しました: {error}", file=sys.stderr)
        return 1

    errors = validate_manifest(manifest, schema)
    if errors:
        print("plugin.json が Agent Plugins 1.0.0 スキーマに適合しません:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    skills = discover_skills(root)
    print(f"plugin.json は Agent Plugins 1.0.0 スキーマに適合しています: {manifest_path}")
    if isinstance(manifest, dict) and "name" in manifest:
        print(f"plugin name: {manifest['name']}")
    print(f"discovered skills ({len(skills)}): {', '.join(skills) or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
