---
name: commit-and-pr
description: Commits staged/unstaged changes and creates a GitHub Pull Request. Use when the user asks to "commit and create a PR", "commit my work and open a PR", "push and make a pull request", or similar requests to save current changes and propose them for review. Handles staging, commit message generation, branch creation, pushing, and PR creation in one workflow.
---

# Commit and PR

Automate the full git commit → push → PR workflow in a single step.

## Workflow

### 1. Assess current state

Run these in parallel:

```bash
git status          # see untracked and modified files
git diff HEAD       # see all changes
git log --oneline -5  # understand recent commit style
git branch -r       # check if a remote tracking branch exists
```

### 2. Determine branch strategy

- If already on a feature branch (not `main`/`master`): use it as-is.
- If on `main`/`master`: create a new branch. Derive the name from the change content (e.g. `feat/add-login`, `fix/null-pointer`).

```bash
git checkout -b <branch-name>
```

### 3. Stage changes

Prefer staging specific files over `git add -A`. Never include:
- `.env`, secrets, credentials
- Large binaries not already tracked
- Build artifacts already in `.gitignore`

```bash
git add <file1> <file2> ...
```

If all modified files are safe, `git add -A` is acceptable.

### 4. Write and create the commit

Analyze all changes and write a concise commit message (1–2 sentences, imperative mood, focus on **why** not **what**). Pass via heredoc:

```bash
git commit -m "$(cat <<'EOF'
<summary line>

<optional body with more context>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

If the pre-commit hook fails: fix the issue, re-stage, and create a **new** commit (never `--amend`).

### 5. Push and create PR

```bash
git push -u origin <branch-name>
```

Then create the PR:

```bash
gh pr create --title "<concise title (≤70 chars)>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <manual step or automated test to verify>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL to the user.

## Safety rules

- Never force-push to `main`/`master`.
- Never use `--no-verify` unless the user explicitly asks.
- Never amend a commit that may already be pushed.
- Confirm before pushing if the current branch is a shared/protected branch.
- Do not commit if there are no changes (`git status` shows clean tree).
