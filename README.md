# agent-skills

配布元リポジトリとして、Skill を subtree で取り込む運用を想定。

## subtree で取り込む例
```bash
# 初回追加（例: devcontainer-bootstrap）
git subtree add --prefix skills/devcontainer-bootstrap https://github.com/nimiusrd/agent-skills.git main --squash

# 更新を取り込む
git subtree pull --prefix skills/devcontainer-bootstrap https://github.com/nimiusrd/agent-skills.git main --squash
```

## 利用者側の最短導入手順（devcontainer-bootstrap）
```bash
# skill を取り込んだリポジトリで
bash skills/devcontainer-bootstrap/scripts/apply_devcontainer.sh --mode safe
```

### 含まれるもの
- `skills/skill-creator/`（ベースユーティリティ）
- `skills/devcontainer-bootstrap/`（Dev Container ブートストラップ）