#!/usr/bin/env python3
"""テンプレートを一時領域で検証・構成し、バックアップ後に反映する。"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import uuid

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
SCRIPT_NAME = "bootstrap-postCreate.sh"
COMMAND = "bash .devcontainer/" + SCRIPT_NAME
KEY = "devcontainer-bootstrap"


def read_json(path):
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: strict JSON が必要です。JSONC（コメント・末尾カンマ）は未対応。変更は行いません。") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object が必要です")
    return value


def merge_missing(defaults, existing):
    """既存の値（false、空値も含む）を優先し、不足項目のみ補完する。"""
    result = copy.deepcopy(defaults)
    for key, value in existing.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_missing(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_command(command):
    if isinstance(command, str):
        return
    if isinstance(command, list) and command and all(isinstance(x, str) for x in command):
        return
    raise ValueError("postCreateCommand は string、空でない string 配列、またはそれらを値に持つ object が必要です")


def append_command(command):
    if command is None:
        return COMMAND
    if isinstance(command, dict):
        for value in command.values():
            validate_command(value)
        result = copy.deepcopy(command)
        if KEY in result and result[KEY] != COMMAND:
            raise ValueError(f"postCreateCommand.{KEY} は既に別の処理に使われています")
        result[KEY] = COMMAND
        return result
    validate_command(command)
    if command == COMMAND or (isinstance(command, str) and command.endswith("\n} && " + COMMAND)):
        return command
    # 配列は argv。各引数を quote してシェルの別コマンドとして合成する。
    original = command if isinstance(command, str) else " ".join(shlex.quote(x) for x in command)
    if not original.strip():
        return COMMAND
    return "{\n" + original + "\n} && " + COMMAND


def prepare(args, root, stage):
    source = root / ".devcontainer"
    if source.exists():
        if source.is_symlink() or not source.is_dir():
            raise ValueError(".devcontainer は実ディレクトリである必要があります")
        shutil.copytree(source, stage, symlinks=True)
    else:
        stage.mkdir()
    # 更新対象の symlink を辿って一時領域外を書き換えない。
    for name in ("devcontainer.json", "Dockerfile", SCRIPT_NAME):
        if (stage / name).is_symlink():
            raise ValueError(f"更新対象 {name} の symlink は未対応です")
    tpl = read_json(TEMPLATES / args.stack / "devcontainer.json")
    config = stage / "devcontainer.json"
    existing = args.mode == "safe" and config.exists()
    data = read_json(config) if existing else copy.deepcopy(tpl)
    if existing:
        # image/build 等の構成は既存設定をそのまま使う。
        for key in ("features", "customizations"):
            if not isinstance(data.get(key, {}), dict):
                raise ValueError(f"{key} は object が必要です")
            data[key] = merge_missing(tpl.get(key, {}), data.get(key, {}))
        vscode = data["customizations"]["vscode"]
        if not isinstance(vscode, dict) or not isinstance(vscode.get("settings", {}), dict):
            raise ValueError("customizations.vscode と settings は object が必要です")
        extensions = vscode.get("extensions", [])
        if not isinstance(extensions, list) or not all(isinstance(x, str) for x in extensions):
            raise ValueError("extensions は string 配列が必要です")
        vscode["extensions"] = list(dict.fromkeys(extensions + tpl["customizations"]["vscode"]["extensions"]))
    if args.include_tools == "true":
        for feature in ("git", "github-cli"):
            data.setdefault("features", {}).setdefault(f"ghcr.io/devcontainers/features/{feature}:1", {})
    if args.stack == "node":
        env = data.setdefault("remoteEnv", {})
        if not isinstance(env, dict):
            raise ValueError("remoteEnv は object が必要です")
        if args.package_manager is not None:
            env["PACKAGE_MANAGER"] = args.package_manager
        else:
            env.setdefault("PACKAGE_MANAGER", "npm")
    data["postCreateCommand"] = append_command(data.get("postCreateCommand") if existing else None)
    script = stage / SCRIPT_NAME
    content = (TEMPLATES / "common/postCreate.sh").read_bytes()
    if args.mode == "safe" and script.exists() and script.read_bytes() != content:
        raise ValueError(f"{SCRIPT_NAME} に変更があります。上書きせず停止します")
    script.write_bytes(content)
    script.chmod(0o755)
    dockerfile = stage / "Dockerfile"
    create_dockerfile = args.mode == "overwrite" or not dockerfile.exists()
    if args.image_tag:
        if existing:
            raise ValueError("既存設定の safe 更新では --image-tag を使えません。既存 image/build を確認し個別に変更してください")
        data["image"] = tpl["image"].rsplit(":", 1)[0] + ":" + args.image_tag
    if create_dockerfile:
        docker = (TEMPLATES / args.stack / "Dockerfile").read_text()
        if args.image_tag:
            docker = docker.replace(tpl["image"], data["image"])
        dockerfile.write_text(docker)
    config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    read_json(config)


def apply(args, root):
    source = root / ".devcontainer"
    workflow = root / ".github/workflows/devcontainer-bootstrap.yml"
    # CI も変更前に内容・対象を検証する。
    ci_content = (TEMPLATES / "common/devcontainer-bootstrap.yml").read_bytes() if args.add_ci == "true" else None
    write_ci = ci_content is not None and (args.mode == "overwrite" or not workflow.exists())
    if ci_content is not None and any(p.is_symlink() for p in (workflow, workflow.parent, workflow.parent.parent)):
        raise ValueError("CI 更新対象の symlink は未対応です")
    old_ci = workflow.read_bytes() if write_ci and workflow.exists() else None
    suffix = uuid.uuid4().hex[:12]
    with tempfile.TemporaryDirectory(prefix=".devcontainer-stage-", dir=root) as temporary:
        stage = Path(temporary) / "content"
        prepare(args, root, stage)
        backup = root / (".devcontainer.bak-" + suffix)
        if source.exists():
            shutil.copytree(source, backup, symlinks=True)
            print(f"バックアップ: {backup}")
        if write_ci and old_ci is not None:
            ci_backup = workflow.with_name(workflow.name + ".bak-" + suffix)
            shutil.copy2(workflow, ci_backup)
            print(f"バックアップ: {ci_backup}")
        previous = Path(temporary) / "previous"
        installed = False
        try:
            if source.exists():
                os.replace(source, previous)
            os.replace(stage, source)
            installed = True
            if write_ci:
                workflow.parent.mkdir(parents=True, exist_ok=True)
                # 同一 FS の一時ファイルから置換。部分書き込みを公開しない。
                ci_stage = Path(temporary) / "workflow.yml"
                ci_stage.write_bytes(ci_content)
                os.replace(ci_stage, workflow)
        except Exception:
            if installed:
                shutil.rmtree(source)
            if previous.exists():
                os.replace(previous, source)
            # CI の atomic replace が成功した後に失敗する処理は置かない。
            raise
    print("完了: .devcontainer を更新しました")
    if ci_content is not None and not write_ci:
        print("safe: 既存 workflow を保持しました")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", choices=("auto", "node", "python", "rust"), default="auto")
    parser.add_argument("--package-manager", choices=("npm", "pnpm", "yarn"))
    parser.add_argument("--mode", choices=("safe", "overwrite"), default="safe")
    parser.add_argument("--include-tools", choices=("true", "false"), default="false")
    parser.add_argument("--add-ci", choices=("true", "false"), default="false")
    parser.add_argument("--image-tag", help="新規作成/overwrite 用の確認済み固定イメージタグ")
    args = parser.parse_args()
    if args.image_tag and (args.image_tag == "latest" or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", args.image_tag)):
        parser.error("--image-tag には latest 以外の Docker タグを指定してください")
    root = Path.cwd()
    if args.stack == "auto":
        args.stack = subprocess.check_output(["bash", str(Path(__file__).with_name("detect_stack.sh")), str(root)], text=True).strip()
        if args.stack not in ("node", "python", "rust"):
            parser.error("スタックを判定できません。--stack node|python|rust を指定してください")
    try:
        apply(args, root)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
