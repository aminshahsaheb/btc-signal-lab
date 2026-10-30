# Security and sensitive data

Do not commit exchange API keys, API secrets, access tokens, webhook URLs, account screenshots, account identifiers, or personal data. Do not use live trading credentials in this repository. Keep live capture and raw market streams out of Git unless a documented data-handling decision explicitly authorizes their storage.

If a secret is accidentally committed, revoking it is necessary; deleting it from the latest file alone is not enough because Git history may retain it.
