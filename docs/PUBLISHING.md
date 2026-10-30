# Create and push the private GitHub repository

Recommended repository name: `btc-signal-lab`

Description:

> Evidence-first BTC research workspace for market-movement timing, directional hypothesis testing, risk controls, and forward validation. No validated trading strategy claimed.

Visibility: **Private**. Do not add a new README, `.gitignore`, or license on GitHub because this folder already contains them and the first push should not create an unrelated root commit.

## Option A — GitHub CLI (fewest steps)

1. Extract this package to a local folder named `btc-signal-lab`.
2. Open Terminal and `cd` into that folder.
3. Verify the source files before committing:

   ```bash
   python3 scripts/verify_sources.py
   git status --short
   ```

4. If `gh` is installed, authenticate once:

   ```bash
   gh auth login
   ```

5. Initialize, commit, create the **private** remote repository, and push:

   ```bash
   git init -b main
   git add .
   git status --short
   git commit -m "chore: establish auditable BTC research workspace"
   gh repo create aminshahsaheb/btc-signal-lab --private --source=. --remote=origin --push
   ```

   If the Git repository is already initialized or the commit already exists, do not repeat that step; inspect `git status` and `git log -1` first.

## Option B — GitHub website + Git

1. Sign in to GitHub as `aminshahsaheb`.
2. Open the **New repository** page.
3. Repository name: `btc-signal-lab`.
4. Description: use the description above.
5. Choose **Private**.
6. Leave **Add a README**, `.gitignore`, and license unchecked. Click **Create repository**.
7. On the Mac, open Terminal in this folder and run:

   ```bash
   python3 scripts/verify_sources.py
   git init -b main
   git add .
   git status --short
   git commit -m "chore: establish auditable BTC research workspace"
   git remote add origin https://github.com/aminshahsaheb/btc-signal-lab.git
   git push -u origin main
   ```

## Final verification

After the push, open the repository page and confirm:

- Visibility is Private.
- `README.md`, `docs/STATUS.md`, `specs/`, `tools/`, and `artifacts/` are present.
- The `verify-source-artifacts` GitHub Actions workflow passes.
- No secret, raw live capture, or unrelated personal file was included.

Official instructions: [Create a new repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) and [add local code to GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
