# devcontainer-bootstrap Skill

## 目的
どのリポジトリでも一貫した Dev Container 初期設定を導入・更新するためのスキル。スタック自動判定→テンプレ適用（safe/overwrite 切替）→変更内容の説明までをスクリプトで行う。対応スタック: node / python / rust。

## チャット呼び出し例
1) **auto + safe**  
   「このリポジトリに Dev Container を safe モードで自動設定して」
2) **node + pnpm + overwrite**  
   「stack=node, packageManager=pnpm, mode=overwrite, includeTools=true, addCI=true で貼って」
3) **rust + safe**  
   「stack=rust, mode=safe で貼って（Cargo.toml があるリポジトリ）」

## ローカルで直接叩く例
```bash
# 1) 自動判定 + safe
bash skills/devcontainer-bootstrap/scripts/apply_devcontainer.sh --mode safe

# 2) node + pnpm + overwrite + CI 生成
bash skills/devcontainer-bootstrap/scripts/apply_devcontainer.sh --stack node --package-manager pnpm --mode overwrite --include-tools true --add-ci true

# 3) 既存 devcontainer を安全更新（python を明示）
bash skills/devcontainer-bootstrap/scripts/apply_devcontainer.sh --stack python --mode safe
```

実行には Python 3.8 以上が必要です。新規作成・overwrite ではプロジェクトのバージョン制約に合うイメージタグを確認し、`--image-tag` で指定できます。既存 JSONC は自動更新せず停止します。

オプションと制約は [SKILL.md](SKILL.md)、更新・復旧の判断は [docs/decision-guide.md](docs/decision-guide.md) を参照。
