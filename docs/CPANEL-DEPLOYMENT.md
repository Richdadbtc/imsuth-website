# Automatic GitHub-to-cPanel deployment

The repository contains two supported deployment paths.

## Recommended: automatic deployment from GitHub

The workflow at `.github/workflows/deploy-cpanel.yml` validates the site, creates an allowlisted public release and sends it to cPanel over SSH whenever `main` is updated.

In the GitHub repository, open **Settings → Environments**, create an environment named `production`, and add these environment secrets:

- `CPANEL_SSH_HOST` — the cPanel server hostname
- `CPANEL_SSH_PORT` — optional; defaults to `22`. Set it only when the host supplies a different numeric SSH port
- `CPANEL_SSH_USER` — the cPanel account username
- `CPANEL_SSH_PRIVATE_KEY` — a private deployment key whose public key is authorised in cPanel
- `CPANEL_SSH_KNOWN_HOSTS` — the verified SSH host-key line supplied by the host
- `CPANEL_REMOTE_PATH` — the domain document root, for example `/home/account/public_html`

Do not store passwords, private keys or webhook tokens in the repository. Protect the `production` environment and restrict who can approve deployments.

After the secrets are configured, merge or push an approved commit to `main`. The **Deploy IMSUTH website to cPanel** workflow will run automatically. It does not delete unrelated remote files.

## Native cPanel Git deployment

The root `.cpanel.yml` supports cPanel's Git Version Control deployment feature and publishes the allowlisted site files to the main account's `public_html` directory. If this domain uses a different document root, update `DEPLOYPATH` before deployment.

When cPanel clones a GitHub repository, use **Git Version Control → Manage → Pull or Deploy → Update from Remote**, followed by **Deploy HEAD Commit**. Native automatic deployment occurs only when changes are pushed directly to the cPanel-managed repository; cloning from GitHub does not by itself make GitHub pushes deploy automatically.

## Production form activation

The website forms remain in development mode until IMSUTH configures an approved HTTPS receiver. Configure the protected server variables documented in `docs/DEPLOYMENT.md`, test on staging, and only then change `forms.mode` in `data/settings.json` to `production`.

## First deployment check

Confirm the homepage, custom 404 page, images, JSON content and PHP endpoints load from the production domain. Check HTTPS, security headers, file permissions and form delivery without using real patient data.
