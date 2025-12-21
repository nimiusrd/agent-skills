#!/usr/bin/env bash
set -euo pipefail

# Apply Dev Container template with safe/overwrite modes.
# Options:
#   --stack <auto|node|python>         (default: auto)
#   --package-manager <npm|pnpm|yarn>  (node only, default: npm)
#   --mode <safe|overwrite>            (default: safe)
#   --include-tools <true|false>       (default: false)
#   --add-ci <true|false>              (default: false)
#
# Behavior:
# - stack=auto: uses detect_stack.sh (multiple hits => fail with guidance)
# - always backs up existing .devcontainer/ to .devcontainer.bak-<timestamp>/ before changes
# - safe: merge extensions/settings/features/postCreateCommand; keep existing where possible
# - overwrite: replace devcontainer.json + Dockerfile with template
# - common postCreate.sh is always installed and invoked from postCreateCommand
# - addCI=true: generate minimal GitHub Actions workflow (devcontainers/ci)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_ROOT="$(cd "${SCRIPT_DIR}/../templates" && pwd)"
ROOT_DIR="$(pwd)"

STACK="auto"
PKG_MANAGER="npm"
MODE="safe"
INCLUDE_TOOLS="false"
ADD_CI="false"

usage() {
  cat <<'EOF'
Usage: apply_devcontainer.sh [options]
  --stack <auto|node|python|go>      Default: auto
  --package-manager <npm|pnpm|yarn>  Node only (default: npm)
  --mode <safe|overwrite>            Default: safe
  --include-tools <true|false>       Default: false
  --add-ci <true|false>              Default: false
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack) STACK="$2"; shift 2;;
    --package-manager) PKG_MANAGER="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --include-tools) INCLUDE_TOOLS="$2"; shift 2;;
    --add-ci) ADD_CI="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1;;
  esac
done

log() { echo "[$(date +%H:%M:%S)] $*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

validate_bool() {
  case "$1" in
    true|false) ;;
    *) fail "Expected true/false, got '$1'" ;;
  esac
}

validate_bool "$INCLUDE_TOOLS"
validate_bool "$ADD_CI"

case "$MODE" in
  safe|overwrite) ;;
  *) fail "mode must be safe or overwrite (got: $MODE)" ;;
esac

case "$STACK" in
  auto|node|python) ;;
  *) fail "stack must be auto|node|python (got: $STACK)" ;;
esac

case "$PKG_MANAGER" in
  npm|pnpm|yarn) ;;
  *) fail "package-manager must be npm|pnpm|yarn (got: $PKG_MANAGER)" ;;
esac

# resolve stack
if [[ "$STACK" == "auto" ]]; then
  DETECTED="$("${SCRIPT_DIR}/detect_stack.sh" "$ROOT_DIR")"
  log "auto-detected stack: ${DETECTED}"
  if [[ "$DETECTED" == "unknown" ]]; then
    fail "スタックを判定できませんでした。--stack で node|python を明示してください。"
  fi
  STACK="$DETECTED"
fi

if [[ "$STACK" != "node" && "$PKG_MANAGER" != "npm" ]]; then
  log "package-manager is only used for node; ignoring for $STACK."
fi

STACK_TEMPLATE_DIR="${TEMPLATE_ROOT}/${STACK}"
DEVCONTAINER_TEMPLATE="${STACK_TEMPLATE_DIR}/devcontainer.json"
DOCKERFILE_TEMPLATE="${STACK_TEMPLATE_DIR}/Dockerfile"
COMMON_POSTCREATE="${TEMPLATE_ROOT}/common/postCreate.sh"

[[ -f "$DEVCONTAINER_TEMPLATE" ]] || fail "Template not found: $DEVCONTAINER_TEMPLATE"
[[ -f "$DOCKERFILE_TEMPLATE" ]] || fail "Template not found: $DOCKERFILE_TEMPLATE"
[[ -f "$COMMON_POSTCREATE" ]] || fail "Common postCreate.sh not found: $COMMON_POSTCREATE"

timestamp() { date +%Y%m%d-%H%M%S; }
ensure_devcontainer_dir() { mkdir -p ".devcontainer"; }

backup_devcontainer() {
  if [[ -d ".devcontainer" ]]; then
    local bak=".devcontainer.bak-$(timestamp)"
    cp -a ".devcontainer" "$bak"
    log "バックアップ作成: $bak"
  fi
}

install_common_postcreate() {
  ensure_devcontainer_dir
  cp "$COMMON_POSTCREATE" ".devcontainer/postCreate.sh"
  chmod +x ".devcontainer/postCreate.sh"
}

write_ci_workflow() {
  local workflow_dir=".github/workflows"
  local workflow="$workflow_dir/devcontainer-bootstrap.yml"
  mkdir -p "$workflow_dir"

  if [[ -f "$workflow" ]]; then
    local bak="${workflow}.bak-$(timestamp)"
    cp -a "$workflow" "$bak"
    log "既存 workflow をバックアップ: $bak"
    if [[ "$MODE" == "safe" ]]; then
      log "safe モードのため既存 workflow を保持します（更新スキップ）。"
      return
    fi
  fi

  cat > "$workflow" <<'YAML'
name: DevContainer Bootstrap

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build-devcontainer:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build devcontainer
        uses: devcontainers/ci@v0.3.1900000417
        with:
          runCmd: |
            ls -la .devcontainer || true
            devcontainer build --workspace-folder .
YAML
  log "workflow を生成しました: $workflow"
}

prepare_extra_features() {
  local tmp="$1"
  if [[ "$INCLUDE_TOOLS" == "true" ]]; then
    cat > "$tmp" <<'EOF'
{
  "ghcr.io/devcontainers/features/git:1": {},
  "ghcr.io/devcontainers/features/github-cli:1": {
    "version": "latest"
  }
}
EOF
  else
    echo "{}" > "$tmp"
  fi
}

merge_with_jq() {
  local target="$1"
  local template="$2"
  local extra_features_file="$3"
  local tmp_out
  tmp_out="$(mktemp)"

  jq \
    --slurpfile tpl "$template" \
    --slurpfile extra "$extra_features_file" \
    --arg pm "$PKG_MANAGER" \
    '
    def to_array(x):
      if x == null then [] elif (x|type)=="array" then x else [x] end;
    def ensure_post(cmd):
      if .postCreateCommand == null then cmd
      elif (.postCreateCommand|type)=="string" then (.postCreateCommand + " && " + cmd)
      else (.postCreateCommand + [cmd])
      end;
    def uniq(a): a | unique;
    . as $orig
    | .features = (($orig.features // {}) + ($tpl[0].features // {}) + ($extra[0]))
    | .customizations.vscode.extensions = (
        (to_array($orig.customizations.vscode.extensions) + to_array($tpl[0].customizations.vscode.extensions))
        | unique
      )
    | .customizations.vscode.settings = (($orig.customizations.vscode.settings // {}) + ($tpl[0].customizations.vscode.settings // {}))
    | .postCreateCommand = ensure_post(".devcontainer/postCreate.sh")
    | (if $orig["updateContentCommand"] then . else . end)
    | (if $orig["remoteUser"] then . else . end)
    | (if $orig["build"] then . else . end)
    | (if $orig["runArgs"] then . else . end)
    | (if $orig["mounts"] then . else . end)
    | (if $orig["containerUser"] then . else . end)
    ' "$target" > "$tmp_out"

  mv "$tmp_out" "$target"
}

merge_with_python() {
  local target="$1"
  local template="$2"
  local extra_features_file="$3"
  python - "$target" "$template" "$extra_features_file" "$PKG_MANAGER" <<'PY'
import json, sys
from pathlib import Path

target, template, extra, pkg = map(Path, sys.argv[1:5])
data = json.loads(target.read_text())
tpl = json.loads(Path(template).read_text())
extra_features = json.loads(Path(extra).read_text())

def uniq(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def to_list(val):
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]

features = data.get("features", {})
features.update(tpl.get("features", {}))
features.update(extra_features)
data["features"] = features

cust = data.setdefault("customizations", {}).setdefault("vscode", {})
tpl_cust = tpl.get("customizations", {}).get("vscode", {})

extensions = uniq(to_list(cust.get("extensions")) + to_list(tpl_cust.get("extensions")))
cust["extensions"] = extensions

settings = cust.get("settings", {})
settings.update(tpl_cust.get("settings", {}))
cust["settings"] = settings

pcc = data.get("postCreateCommand")
if pcc is None:
    data["postCreateCommand"] = ".devcontainer/postCreate.sh"
elif isinstance(pcc, str):
    data["postCreateCommand"] = pcc + " && .devcontainer/postCreate.sh"
elif isinstance(pcc, list):
    data["postCreateCommand"] = pcc + [".devcontainer/postCreate.sh"]
else:
    data["postCreateCommand"] = ".devcontainer/postCreate.sh"

target.write_text(json.dumps(data, indent=2))
PY
}

apply_overwrite() {
  ensure_devcontainer_dir
  cp "$DEVCONTAINER_TEMPLATE" ".devcontainer/devcontainer.json"
  cp "$DOCKERFILE_TEMPLATE" ".devcontainer/Dockerfile"
  log "overwrite: テンプレートを配置しました (.devcontainer/devcontainer.json, Dockerfile)"
}

apply_safe() {
  ensure_devcontainer_dir
  if [[ -f ".devcontainer/devcontainer.json" ]]; then
    log "safe: 既存 devcontainer.json をマージします"
    tmp_features="$(mktemp)"
    prepare_extra_features "$tmp_features"
    if command -v jq >/dev/null 2>&1; then
      merge_with_jq ".devcontainer/devcontainer.json" "$DEVCONTAINER_TEMPLATE" "$tmp_features"
    else
      log "jq が見つかりませんでした。Python で最小限マージします。"
      merge_with_python ".devcontainer/devcontainer.json" "$DEVCONTAINER_TEMPLATE" "$tmp_features"
    fi
    rm -f "$tmp_features"
  else
    log "safe: devcontainer.json が無いのでテンプレートから新規作成します"
    cp "$DEVCONTAINER_TEMPLATE" ".devcontainer/devcontainer.json"
  fi

  if [[ -f ".devcontainer/Dockerfile" ]]; then
    log "safe: 既存 Dockerfile を保持します（テンプレート未反映）。必要なら手動で調整してください。"
  else
    cp "$DOCKERFILE_TEMPLATE" ".devcontainer/Dockerfile"
    log "safe: Dockerfile をテンプレートから追加しました"
  fi
}

set_package_manager() {
  [[ "$STACK" == "node" ]] || return 0
  if command -v jq >/dev/null 2>&1; then
    tmp="$(mktemp)"
    jq --arg pm "$PKG_MANAGER" '
      .remoteEnv = (.remoteEnv // {}) |
      .remoteEnv.PACKAGE_MANAGER = $pm
    ' ".devcontainer/devcontainer.json" > "$tmp"
    mv "$tmp" ".devcontainer/devcontainer.json"
  else
    python - "$PKG_MANAGER" <<'PY'
import json, sys
from pathlib import Path
pm = sys.argv[1]
path = Path(".devcontainer/devcontainer.json")
data = json.loads(path.read_text())
data.setdefault("remoteEnv", {})["PACKAGE_MANAGER"] = pm
path.write_text(json.dumps(data, indent=2))
PY
  fi
  log "PACKAGE_MANAGER を設定しました: $PKG_MANAGER"
}

main() {
  log "開始: stack=$STACK mode=$MODE includeTools=$INCLUDE_TOOLS addCI=$ADD_CI pkgManager=$PKG_MANAGER"
  backup_devcontainer
  install_common_postcreate

  if [[ "$MODE" == "overwrite" ]]; then
    apply_overwrite
  else
    apply_safe
  fi

  set_package_manager

  if [[ "$ADD_CI" == "true" ]]; then
    write_ci_workflow
  fi

  log "完了: .devcontainer を更新しました"
  log "作成/更新ファイル例: .devcontainer/devcontainer.json, .devcontainer/Dockerfile, .devcontainer/postCreate.sh"
  if [[ "$ADD_CI" == "true" ]]; then
    log "CI workflow: .github/workflows/devcontainer-bootstrap.yml"
  fi
}

main "$@"
