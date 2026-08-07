# GitHub Upload Guide — use-case-3--multimodal-ai-chatbot-aws-bedrock

Complete step-by-step guide to push this project to GitHub from scratch.

---

## Prerequisites

- Git installed: `git --version`
- GitHub account: [github.com/aamir490](https://github.com/aamir490)
- GitHub repo created (empty, no README): `use-case-3--multimodal-ai-chatbot-aws-bedrock`

---

## Step 1 — Open PowerShell and navigate to the project folder

```powershell
# [PowerShell]
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"
```

Verify you are in the right folder:

```powershell
# [PowerShell]
Get-Location
dir
```

Expected output should show files like `mod_chatbot_frontend.py`, `README.md`, `services\`, etc.

---

## Step 2 — Verify Git is installed

```powershell
# [PowerShell]
git --version
```

Expected output: `git version 2.x.x.windows.x`

If Git is not installed, download it from: https://git-scm.com/download/win

---

## Step 3 — Initialize Git repository

```powershell
# [PowerShell]
git init
```

Expected output: `Initialized empty Git repository in E:/.../.git/`

---

## Step 4 — Verify .gitignore exists and is correct

This is critical — must be done **before** `git add` to prevent committing secrets or large files.

```powershell
# [PowerShell]
# Check the file exists
Test-Path .gitignore
```

Expected: `True`

```powershell
# [PowerShell]
# View the contents
Get-Content .gitignore
```

Verify these lines are present:

```
.env
.env.*
.venv/
__pycache__/
*.pdf
secrets.json
aws_credentials
.streamlit/secrets.toml
```

If `.gitignore` is missing for any reason, create it:

```powershell
# [PowerShell] — only if Test-Path returned False
Copy-Item .env.example .env.example.bak   # safety backup
New-Item -ItemType File -Name .gitignore -Force | Out-Null
notepad .gitignore
```

Paste the content from the existing `.gitignore` file in this project.

---

## Step 5 — Check Git status (before staging)

```powershell
# [PowerShell]
git status
```

**What you should see — files listed as Untracked:**
```
mod_chatbot_frontend.py
README.md
architecture.md
deployment.md
cleanup.md
model_selection.md
troubleshooting.md
requirements_new.txt
.env.example
.gitignore
github_upload.md
services/
utils/
scripts/
docs/
```

**What you should NOT see:**
- `.venv/` — virtual environment (ignored)
- `.env` — secrets file (ignored)
- `__pycache__/` — Python cache (ignored)
- Any `.pdf` files (ignored)

If you see `.venv/` or `.env` in the list, stop and check your `.gitignore`.

---

## Step 6 — Connect the remote GitHub repository

```powershell
# [PowerShell]
git remote add origin https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git
```

Verify the remote was added:

```powershell
# [PowerShell]
git remote -v
```

Expected output:
```
origin  https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git (fetch)
origin  https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git (push)
```

---

## Step 7 — Rename branch to main

```powershell
# [PowerShell]
git branch -M main
```

---

## Step 8 — Stage all project files

```powershell
# [PowerShell]
git add .
```

---

## Step 9 — Verify what is staged (IMPORTANT)

```powershell
# [PowerShell]
git status
```

**Green (staged — these will be committed):**
```
new file: mod_chatbot_frontend.py
new file: README.md
new file: architecture.md
new file: deployment.md
new file: cleanup.md
new file: model_selection.md
new file: troubleshooting.md
new file: github_upload.md
new file: requirements_new.txt
new file: .env.example
new file: .gitignore
new file: services/__init__.py
new file: services/bedrock_service.py
new file: services/document_service.py
new file: services/image_service.py
new file: utils/__init__.py
new file: utils/validators.py
new file: scripts/bedrock_model_access_check.py
```

**If you see `.env` or `.venv/` in the staged list — STOP.**
Run these commands to fix it before committing:

```powershell
# [PowerShell] — unstage everything and fix .gitignore first
git rm -r --cached .
# fix .gitignore, then:
git add .
git status   # verify again
```

---

## Step 10 — Create the first commit

```powershell
# [PowerShell]
git commit -m "Initial commit: NovaMind AI multimodal chatbot — Bedrock, Streamlit, Python"
```

Expected output:
```
[main (root-commit) xxxxxxx] Initial commit: NovaMind AI multimodal chatbot...
 18 files changed, ...
```

---

## Step 11 — Push to GitHub

```powershell
# [PowerShell]
git push -u origin main
```

You will be prompted for GitHub credentials:
- **Username:** your GitHub username (`aamir490`)
- **Password:** use a **Personal Access Token (PAT)**, NOT your GitHub password

### Creating a Personal Access Token (if you don't have one)

```
# [GitHub — browser]
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Note: novabot-push
4. Expiration: 90 days
5. Scopes: check "repo" (full control of private repositories)
6. Click "Generate token"
7. COPY the token immediately — it will not be shown again
```

Use the token as your password when `git push` prompts for it.

---

## Step 12 — Verify the upload on GitHub

```
# [Browser]
Open: https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock
```

Confirm:
- [ ] All files are visible
- [ ] `README.md` renders correctly as the repo homepage
- [ ] `services/`, `utils/`, `scripts/` folders are present
- [ ] `.env` file is NOT visible (correctly ignored)
- [ ] `.venv/` folder is NOT visible (correctly ignored)
- [ ] `__pycache__/` is NOT visible (correctly ignored)
- [ ] The `main` branch is shown

---

## Future Updates — Push Changes After Editing

Whenever you make changes to the project:

```powershell
# [PowerShell]
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"

# Check what changed
git status
git diff

# Stage specific files (preferred over git add .)
git add mod_chatbot_frontend.py
git add services/bedrock_service.py
# OR stage all changes:
git add .

# Commit with a meaningful message
git commit -m "feat: add streaming response support"

# Push
git push
```

---

## Quick Reference

```powershell
# [PowerShell] — complete flow from scratch
cd "E:\GenAi-Project-Udemy\Code_15042025\Chatbot_text_image"
git init
Test-Path .gitignore                         # must return True
git status                                   # verify .venv not listed
git remote add origin https://github.com/aamir490/use-case-3--multimodal-ai-chatbot-aws-bedrock.git
git remote -v                                # verify remote
git branch -M main
git add .
git status                                   # verify staged files
git commit -m "Initial commit: NovaMind AI multimodal chatbot"
git push -u origin main
```

---

## Troubleshooting

### `git push` rejected — remote already has commits

```powershell
# [PowerShell]
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Authentication failed

- Make sure you are using a Personal Access Token, not your GitHub password
- Generate a new token at: https://github.com/settings/tokens

### `.venv` was accidentally committed

```powershell
# [PowerShell]
git rm -r --cached .venv
git commit -m "fix: remove .venv from tracking"
git push
```

### Large file error

The `.gitignore` already blocks `*.pdf` and `.venv/`.
If you get a large file error for something else, remove it from tracking:

```powershell
# [PowerShell]
git rm --cached <filename>
# add it to .gitignore
git commit -m "fix: remove large file"
git push
```
