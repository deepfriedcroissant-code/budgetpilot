# SECURITY — Compromised API credentials

## Important: delete / rotate keys first

If GitGuardian reports a PayPal OAuth2 client secret or Google Cloud / Gemini API key in this repository, **assume the credential is compromised even if it is absent from the latest branch**. A `.gitignore` update does not erase Git commits, forks, clones, caches, or logs.

1. **PayPal Developer Dashboard:** identify the affected REST app in the correct Sandbox or Live environment. Revoke/rotate the exposed **client secret**; if the incident concerns an entire app's OAuth2 credentials, replace that app's client ID and secret. Update local `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` only after creating replacement credentials. Never post either to an issue, PR, or chat.
2. **Google Cloud / Google AI Studio:** locate the exact API key using GitGuardian's alert fingerprint and the owning project. Revoke or delete it, create a new key only if needed, and set API restrictions, permitted API scope, quotas and budgets. The Gemini parser uses `GEMINI_API_KEY` in the local `.env`. A different 'Google Cloud Express' key may belong to a different project; confirm the owning project rather than automatically equating them.
3. **Check for misuse:** review PayPal Sandbox/Live activity and Google Cloud usage/quotas/billing for unexpected requests. Contact the provider if activity is suspicious.
4. **Update local machines and deployments:** replace credentials in a local `.env` or approved secrets manager. Keep `.env` untracked. Check with `git ls-files .env` (should have no output) and `git status --ignored` when needed. Do not paste raw credentials into tickets or recordings.

## Git history and GitGuardian alerts

The current project's `.gitignore` excludes `.env`, secret-bearing configs and key files, but **ignore rules only prevent new tracking**. GitGuardian detections can refer to older commits, PR branches, deleted files, or other public refs.

Use each GitGuardian alert's *file path and commit SHA* to identify the exact exposure. Do not post the credential value. Once keys have been invalidated, coordinate history cleanup with the team:

- GitHub's file-edit API cannot purge commits. Use `git-filter-repo` or BFG on a carefully backed-up mirror clone to remove the **specific secret values/affected files** from all impacted refs, followed by coordinated force-push of rewritten branches/tags.
- GitHub's documented sensitive-data removal process may require GitHub Support to remove cached views and affected pull-request refs. Existing forks/clones must be treated separately.
- History rewriting changes commit IDs, breaks old checkouts/PR references, and requires teammates to reclone or reset their copies. Do not force-push shared branches without coordinating.
- Once cleanup is confirmed, resolve GitGuardian incidents as **revoked / remediated** rather than assuming removing a current file invalidated old credentials.

## Runtime configuration

Use local `.env` (never committed) or a secure deployment secrets manager. `.env.example` intentionally contains **placeholders only**.

```dotenv
GEMINI_API_KEY=replace-with-your-new-key
PAYPAL_CLIENT_ID=replace-with-new-sandbox-client-id
PAYPAL_CLIENT_SECRET=replace-with-new-sandbox-client-secret
PAYPAL_BASE_URL=https://api-m.sandbox.paypal.com
APP_URL=http://localhost:8501
BUDGETPILOT_ENABLE_PAYPAL_SANDBOX=0
```

No production payment support is implemented. Turning Sandbox checkout on should remain an explicit local opt-in.

## Before new commits

Review staged changes with `git diff --cached` and check for credential files with `git ls-files`. Keep GitGuardian/secret scanning enabled for pull requests and branches. Do not use real credentials in test fixtures, screenshots, log output or demo videos.
