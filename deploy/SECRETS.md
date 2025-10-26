Repository secrets & GHCR PAT

This file documents the repository secrets required for the CI deploy workflow and how to create a GHCR PAT for authenticated docker pulls on the VPS.

Required repository secrets

- SSH_PRIVATE_KEY
  - Contents: the private SSH key used by the workflow to SSH into your VPS (PEM/OPENSSH format). Do NOT put a passphrase unless you handle it.
  - On the VPS, the corresponding public key must be present in `~/.ssh/authorized_keys` of the deploy user.

- SSH_HOST
  - Hostname or IP address of your VPS (e.g. `s2591.rootserver.io`).

- SSH_USER
  - SSH username the action should use (e.g. `deploy` or `root`).

- REMOTE_PATH
  - Path on the server where the repo is deployed, e.g. `/var/www/parkingsrv`.

Optional but recommended

- SSH_PORT (optional)
  - SSH port (defaults to 22 if not set).

- GHCR_PAT (optional, recommended if images are private)
  - GitHub Personal Access Token used to authenticate `docker pull` from ghcr.io on the VPS. Minimal scope: `read:packages` (classic PAT) or `packages:read` for fine-grained tokens.

How to create a GHCR PAT (classic PAT)

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token.
2. Give a descriptive name (e.g. `parking-app-deploy-ghcr`).
3. Select `read:packages` (minimum required for pulling packages).
4. Generate and COPY the token — it is shown only once.

How to add repository secrets in GitHub

1. Open your repository on GitHub: https://github.com/<owner>/<repo>
2. Go to Settings → Secrets and variables → Actions → New repository secret
3. Enter name and value (`SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `REMOTE_PATH`, `GHCR_PAT`)

Quick local GHCR test

```bash
# login locally with GHCR PAT
echo "${GHCR_PAT}" | docker login ghcr.io -u <your-github-username> --password-stdin
# try pulling an image
docker pull ghcr.io/<your-github-username>/parking-frontend:<IMAGE_TAG>
```

Common failure modes explained

- SSH permission denied (publickey): wrong SSH key or public key not on the server.
- docker pull 401 Unauthorized: GHCR_PAT missing or incorrect on the VPS.
- docker-compose: command not found: install docker-compose or use the Docker plugin.
- Healthcheck fails: `deploy/update.sh` exit code 2 indicates healthcheck failed — inspect the healthcheck script or container logs.

Re-running workflows / fetching logs

- List recent runs for the workflow:
  gh run list --repo <owner>/<repo> --workflow=docker-deploy.yml --limit 10
- Fetch full logs for a run:
  gh run view <RUN_ID> --repo <owner>/<repo> --log
- Re-run a run:
  gh run rerun <RUN_ID> --repo <owner>/<repo>

If you'd like, I can add the same content into `README.md` or create a short `docs/DEPLOY.md` and open a PR — tell me which you prefer.